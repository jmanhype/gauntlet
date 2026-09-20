"""Leakage-resistant walk-forward evaluation and replay artifacts."""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from gauntlet.config.resolver import ResolvedConfig
from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.contracts.manifests import create_exclusive
from gauntlet.data.dependency import DependencyEvaluation, evaluate_dependencies
from gauntlet.ledger import Actor, EventRecord, append_event, regenerate_heads
from gauntlet.ledger._common import LedgerError, data_root_path

from .splits import SplitError, SplitManifest, build_split_manifest
from .synthetic import BarRow, FrozenPopulation


JUDGE_POLICY_HASH = sha256_digest(canonical_json({"entry": "next_bar", "selection": "validation_then_lock", "synthetic_promotion": "prohibited"}))


class WalkForwardError(RuntimeError):
    """A machine-readable walk-forward request or integrity rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message); self.code = code; self.message = message; self.path = path


@dataclass(frozen=True, slots=True)
class CandidateVariant:
    """A factory candidate sealed by its feature and parameter provenance."""

    fingerprint: str; feature_provenance: Mapping[str, object]; parameters: Mapping[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.feature_provenance, Mapping) or not isinstance(self.parameters, Mapping): raise WalkForwardError("CANDIDATE_INVALID", "feature_provenance and parameters must be objects", "$.candidates")
        unknown = sorted(set(self.parameters) - {"lookback", "momentum_weight", "volume_weight", "threshold"})
        if unknown: raise WalkForwardError("PARAMETER_UNKNOWN", f"unregistered candidate parameter(s): {unknown}", "$.candidates.parameters")
        sealed = self.fingerprint or sha256_digest(canonical_json({"feature_provenance": dict(self.feature_provenance), "parameters": dict(self.parameters)}))
        object.__setattr__(self, "fingerprint", _digest(sealed, "$.candidates.fingerprint"))
        object.__setattr__(self, "feature_provenance", MappingProxyType(dict(self.feature_provenance)))
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))


@dataclass(frozen=True, slots=True)
class FactoryRankingEntry:
    """Exploratory race output; score is deliberately not judge evidence."""

    fingerprint: str; score: float


@dataclass(frozen=True, slots=True)
class WalkForwardRequest:
    """Every immutable input required for a local synthetic evaluation."""

    population: FrozenPopulation; config: ResolvedConfig; candidates: tuple[CandidateVariant, ...]; actor: Actor
    feature_provenance: Mapping[str, object]; factory_ranking: tuple[FactoryRankingEntry, ...] = ()
    split_manifest: SplitManifest | None = None; as_of: datetime | None = None


@dataclass(frozen=True, slots=True)
class Prediction:
    """One row-level test signal with its explicit modeled bases."""

    row_id: str; fold_id: str; timestamp_utc: str; entry_timestamp_utc: str; venue: str; token: str; intended_action: str
    prediction: float; label: float; label_completed_at_utc: str; prediction_basis: str; label_basis: str; selected_fingerprint: str

    def mapping(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Trade:
    """One next-bar entry and target-horizon exit replay row."""

    trade_id: str; fold_id: str; row_id: str; venue: str; token: str; intended_action: str; label: float
    label_completed_at_utc: str; entry_timestamp_utc: str; entry_bar_id: str; exit_timestamp_utc: str; entry_price: int; exit_price: int
    return_fraction: float; execution_basis: str; outcome_basis: str; selection_lock_hash: str

    def mapping(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    """A split fold with its post-selection lock and untouched test proof."""

    fold_id: str; order: int; train_membership: tuple[str, ...]; validation_membership: tuple[str, ...]
    test_membership: tuple[str, ...]; boundaries: Mapping[str, str]; selection_lock: Mapping[str, object]

    def mapping(self) -> dict[str, object]:
        return {"fold_id": self.fold_id, "order": self.order, "boundaries": dict(self.boundaries), "train_membership": list(self.train_membership), "validation_membership": list(self.validation_membership), "test_membership": list(self.test_membership), "selection_lock": dict(self.selection_lock)}


@dataclass(frozen=True, slots=True)
class WalkForwardRun:
    """The complete typed result and immutable physical evidence."""

    status: str; run_hash: str; canonical_bytes: bytes; run_report: Mapping[str, object]
    folds: tuple[WalkForwardFold, ...]; predictions: tuple[Prediction, ...]; trades: tuple[Trade, ...]
    artifact_paths: Mapping[str, Path]; event_head_hash: str; event_record: Mapping[str, object]; replayed: bool

    def mapping(self) -> dict[str, object]:
        value = json.loads(self.canonical_bytes)
        return {**value, "event_head_hash": self.event_head_hash, "event_record": dict(self.event_record), "replayed": self.replayed}


def _utc_z(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None: raise WalkForwardError("TIMESTAMP_INVALID", "as_of must be timezone-aware", "$.as_of")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00") if value.endswith("Z") else None
    except ValueError as error:
        raise WalkForwardError("TIMESTAMP_INVALID", "timestamp must be UTC ISO-8601 ending in Z") from error
    if parsed is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0: raise WalkForwardError("TIMESTAMP_INVALID", "timestamp must be UTC ISO-8601 ending in Z")
    return parsed


def _digest(value: object, path: str) -> str:
    hexadecimal = value[7:] if isinstance(value, str) else ""
    if not isinstance(value, str) or not value.startswith("sha256:") or len(hexadecimal) != 64 or any(char not in "0123456789abcdef" for char in hexadecimal): raise WalkForwardError("DIGEST_INVALID", "must be sha256:<64 lowercase hexadecimal>", path)
    return value


def _validate_request(request: WalkForwardRequest) -> tuple[CandidateVariant, ...]:
    if request.population.digest() != request.population.population_hash: raise WalkForwardError("POPULATION_MUTATED", "population contents no longer match their frozen hash", "$.population")
    if not isinstance(request.config, ResolvedConfig): raise WalkForwardError("CONFIG_UNREGISTERED", "config must be a ResolvedConfig", "$.config")
    if not isinstance(request.feature_provenance, Mapping): raise WalkForwardError("PROVENANCE_INVALID", "feature_provenance must be an object", "$.feature_provenance")
    if not request.candidates: raise WalkForwardError("CANDIDATE_MISSING", "at least one candidate variant is required", "$.candidates")
    candidates = request.candidates
    fingerprints = [candidate.fingerprint for candidate in candidates]
    if len(set(fingerprints)) != len(fingerprints): raise WalkForwardError("CANDIDATE_DUPLICATED", "candidate fingerprints must be unique", "$.candidates")
    known = set(fingerprints)
    for entry in request.factory_ranking:
        _digest(entry.fingerprint, "$.factory_ranking.fingerprint")
        if isinstance(entry.score, bool) or not isinstance(entry.score, (int, float)) or not math.isfinite(entry.score): raise WalkForwardError("FACTORY_SCORE_INVALID", "factory score must be finite but is not judge evidence", "$.factory_ranking.score")
        if entry.fingerprint not in known: raise WalkForwardError("FACTORY_CANDIDATE_UNKNOWN", "factory ranking names an unregistered candidate", "$.factory_ranking")
    if request.as_of is not None: _utc_z(request.as_of)
    for kind, rows, raw_path, content_hash, descriptor in (("bars", request.population.bars, request.population.bars_content_path, request.population.bars_content_hash, request.population.bars_descriptor), ("events", request.population.events, request.population.events_content_path, request.population.events_content_hash, request.population.events_descriptor)):
        path = Path(raw_path)
        if not path.is_file() or path.is_symlink() or sha256_digest(path.read_bytes()) != content_hash or descriptor.get("content_hash") != content_hash: raise WalkForwardError("POPULATION_CONTENT_MISMATCH", f"{kind} rows no longer match registered immutable content", f"$.population.{kind}")
        envelope: object = json.loads(path.read_bytes())
        if not isinstance(envelope, dict) or envelope.get("rows") != [row.mapping() for row in rows]: raise WalkForwardError("POPULATION_CONTENT_MISMATCH", f"{kind} in-memory rows differ from registered content", f"$.population.{kind}")
    return candidates


def _dependency(request: WalkForwardRequest, as_of: datetime) -> DependencyEvaluation:
    return evaluate_dependencies([str(request.population.bars_descriptor["descriptor_hash"]), str(request.population.events_descriptor["descriptor_hash"])], as_of, JUDGE_POLICY_HASH, set())


def _provenance(candidate: CandidateVariant, signal: datetime) -> None:
    def visit(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                child = f"{path}.{key}"
                if key in ("uses_future", "future_data") and item is True: raise WalkForwardError("FUTURE_NORMALIZATION_REJECTED", "normalization may not declare future data", child)
                if key in ("normalization_end_utc", "available_at_utc") and isinstance(item, str) and _parse(item) > signal: raise WalkForwardError("FUTURE_NORMALIZATION_REJECTED", "normalization availability is after prediction time", child)
                visit(item, child)
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")

    visit(candidate.feature_provenance, "$.candidates.feature_provenance")


def _features(row: BarRow, rows: list[BarRow], candidate: CandidateVariant, policy_window: int) -> float:
    index = next(item for item, candidate_row in enumerate(rows) if candidate_row.row_id == row.row_id)
    if index < 2: raise WalkForwardError("FEATURE_WINDOW_INVALID", f"insufficient prior bars for {row.row_id}", f"$.bars.{row.row_id}")
    _provenance(candidate, _parse(row.timestamp_utc))
    lookback = int(candidate.parameters.get("lookback", min(2, index)))
    if lookback < 1 or lookback > index: raise WalkForwardError("FEATURE_WINDOW_INVALID", "candidate lookback exceeds available past", "$.candidates.parameters.lookback")
    window = rows[max(0, index - policy_window):index]; previous = rows[index - 1].close
    momentum = previous / rows[index - lookback].close - 1; mean_volume = sum(item.volume for item in window) / len(window)
    volume_z = (previous and rows[index - 1].volume - mean_volume) / (mean_volume or 1)
    return float(candidate.parameters.get("momentum_weight", 1.0)) * momentum + float(candidate.parameters.get("volume_weight", 0.0)) * volume_z


def _action(score: float, candidate: CandidateVariant) -> str:
    return "BUY" if score > float(candidate.parameters.get("threshold", 0.0)) else "FLAT"


def _select(rows: list[BarRow], membership: tuple[str, ...], candidates: tuple[CandidateVariant, ...], window: int) -> CandidateVariant:
    by_id = {row.row_id: row for row in rows}
    member_rows = [by_id[row_id] for row_id in membership]
    ranked: list[tuple[float, int, CandidateVariant]] = []
    for candidate in candidates:
        utility = 0.0
        for row in member_rows:
            score = _features(row, rows, candidate, window)
            future = next(item for item in rows if item.timestamp_utc == row.target_completed_at_utc)
            utility += future.close / row.close - 1 if _action(score, candidate) == "BUY" else 0.0
        ranked.append((utility, -int(candidate.fingerprint[7:], 16), candidate))
    return max(ranked, key=lambda item: (item[0], item[1]))[2]


def _evaluate_fold(fold: WalkForwardFold, rows: list[BarRow], selected: CandidateVariant, policy_window: int, target_horizon: int, interval: int) -> tuple[tuple[Prediction, ...], tuple[Trade, ...], str | None]:
    by_id = {row.row_id: row for row in rows}
    indices = {row.row_id: index for index, row in enumerate(rows)}
    predictions: list[Prediction] = []
    trades: list[Trade] = []
    for row_id in fold.test_membership:
        row = by_id[row_id]; index = indices[row_id]; score = _features(row, rows, selected, policy_window)
        intended = _action(score, selected); entry_index = index + 1
        if entry_index >= len(rows) or _parse(rows[entry_index].timestamp_utc) - _parse(row.timestamp_utc) != timedelta(seconds=interval): return (), (), f"NEXT_BAR_MISSING:{row_id}"
        expected_target = _parse(row.timestamp_utc) + timedelta(seconds=target_horizon * interval)
        outcome = next((item for item in rows if item.timestamp_utc == row.target_completed_at_utc), None)
        if outcome is None or _parse(row.target_completed_at_utc) != expected_target: return (), (), f"TARGET_BAR_MISSING:{row_id}"
        entry = rows[entry_index]; label = outcome.close / row.close - 1
        prediction = Prediction(row_id, fold.fold_id, row.timestamp_utc, entry.timestamp_utc, row.venue, row.token, intended, round(score, 12), round(label, 12), row.target_completed_at_utc, "MODELED", "MODELED", selected.fingerprint)
        predictions.append(prediction)
        if intended != "FLAT":
            trades.append(Trade(f"trade-{fold.fold_id}-{row_id}", fold.fold_id, row_id, row.venue, row.token, intended, round(label, 12), row.target_completed_at_utc, entry.timestamp_utc, entry.row_id, outcome.timestamp_utc, entry.close, outcome.close, round(outcome.close / entry.close - 1, 12), "MODELED", "MODELED", str(fold.selection_lock["selection_lock_hash"])))
    return tuple(predictions), tuple(trades), None


def _dependency_mapping(evaluation: DependencyEvaluation) -> dict[str, object]:
    return {"status": evaluation.status, "graph_hash": evaluation.graph_hash, "selected_descriptor_hashes": list(evaluation.selected_descriptor_hashes), "affected_metrics": list(evaluation.affected_metrics), "coverage": evaluation.coverage, "findings": [{"check": finding.check, "code": finding.code, "message": finding.message, "descriptor_hash": finding.descriptor_hash} for finding in evaluation.findings]}


def _split(request: WalkForwardRequest) -> SplitManifest:
    manifest = request.split_manifest or build_split_manifest(request.population.policy, request.population)
    expected = build_split_manifest(request.population.policy, request.population)
    if manifest.mapping() != expected.mapping(): raise WalkForwardError("SPLIT_MUTATED", "split manifest no longer matches its canonical membership", "$.split_manifest")
    return manifest


def _write_bundle(root: Path, run_hash: str, files: Mapping[str, bytes]) -> dict[str, Path]:
    destination = root / "runs" / run_hash
    expected = {root / "runs" / run_hash / name: data for name, data in files.items()}
    if destination.exists():
        if not destination.is_dir() or any(not path.is_file() or path.read_bytes() != data for path, data in expected.items()): raise WalkForwardError("ARTIFACT_MISMATCH", "existing immutable run artifacts do not match this evaluation", str(destination))
        return {name: destination / name for name in files}
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = root / "runs" / f".{run_hash}.{os.getpid()}.tmp"
    staging.mkdir()
    try:
        paths = {name: create_exclusive(staging / name, data) for name, data in files.items()}
        os.rename(staging, destination)
    except BaseException:
        if staging.exists():
            for path in sorted(staging.iterdir(), reverse=True):
                path.unlink()
            staging.rmdir()
        raise
    return {name: destination / path.name for name, path in paths.items()}


def _event(root: Path, request: WalkForwardRequest, run_hash: str, output_hash: str, timestamp: str) -> tuple[str, Mapping[str, object], bool]:
    event_id = f"walk-forward-{run_hash}"
    ledger = root / "ledger" / "events.jsonl"
    if ledger.is_file():
        for line in ledger.read_bytes().splitlines():
            record: object = json.loads(line)
            if isinstance(record, dict) and record.get("event_id") == event_id: return str(record["event_hash"]), record, True
    args_hash = sha256_digest(canonical_json({"config_hash": request.config.config_hash, "population_hash": request.population.population_hash, "policy_hash": JUDGE_POLICY_HASH}))
    event = EventRecord(event_id, timestamp, request.actor, "gate.evaluate", run_hash, args_hash, output_hash, "OK", None, {"run_id": run_hash, "phase": "walk-forward"})
    try:
        appended = append_event(event, regenerate_heads(root).events.head_hash, data_root=root)
    except LedgerError as error:
        raise WalkForwardError("EVENT_APPEND_FAILED", error.message, error.path or "$.event") from error
    return appended.head_hash, appended.record, False


def _publish(request: WalkForwardRequest, dependency: DependencyEvaluation, split: SplitManifest | None, folds: tuple[WalkForwardFold, ...], predictions: tuple[Prediction, ...], trades: tuple[Trade, ...], blocked: str | None, as_of: datetime) -> WalkForwardRun:
    selected_fingerprints = [str(fold.selection_lock["candidate_fingerprint"]) for fold in folds]
    report: dict[str, object] = {"schema_version": "gauntlet.walk-forward-run.v1", "status": "BLOCKED" if blocked else "OK", "blocked_reason": blocked, "venue": "solana_dex", "population_hash": request.population.population_hash, "population_evidence_class": "SYNTHETIC_FIXTURE", "promotable_venue_evidence": False, "config_hash": request.config.config_hash, "feature_provenance": dict(request.feature_provenance), "source_descriptor_hashes": sorted((str(request.population.bars_descriptor["descriptor_hash"]), str(request.population.events_descriptor["descriptor_hash"]))), "selected_fingerprints": selected_fingerprints, "factory_ranking": {"admissible": False, "ranking_score_is_judge_evidence": False, "entry_condition": "selected_fingerprint_locked"}, "dependency_evaluation": _dependency_mapping(dependency), "fold_count": len(folds), "test_membership_digests_after_evaluation": [sha256_digest(canonical_json(list(fold.test_membership))) for fold in folds], "prediction_count": len(predictions), "trade_count": len(trades), "execution": {"entry": "NEXT_BAR", "gap_policy": "BLOCKED", "imputed_fill": False}}
    fold_manifest = split.mapping() if split is not None else {"schema_version": "gauntlet.walk-forward-split.v1", "population_hash": request.population.population_hash, "status": "BLOCKED", "error_code": blocked}
    evaluation_hash = sha256_digest(canonical_json({"folds": [fold.mapping() for fold in folds], "predictions": [prediction.mapping() for prediction in predictions], "report": report, "trades": [trade.mapping() for trade in trades]})); report["evaluation_hash"] = evaluation_hash
    bundle = {"fold_manifest": fold_manifest, "predictions": [prediction.mapping() for prediction in predictions], "run_report": report, "trades": [trade.mapping() for trade in trades]}; canonical = canonical_json(bundle); run_hash = sha256_digest(canonical)
    files = {"fold_manifest.json": canonical_json(fold_manifest), "predictions.json": canonical_json(bundle["predictions"]), "trades.json": canonical_json(bundle["trades"]), "run_report.json": canonical_json(report)}; root = data_root_path(None); paths = _write_bundle(root, run_hash, files)
    event_head, event_record, replayed = _event(root, request, run_hash, sha256_digest(canonical), _utc_z(as_of))
    return WalkForwardRun("BLOCKED" if blocked else "OK", run_hash, canonical, MappingProxyType(report), folds, predictions, trades, MappingProxyType(paths), event_head, MappingProxyType(dict(event_record)), replayed)


def evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun:
    """Evaluate validation-selected variants on untouched following test windows."""

    candidates = _validate_request(request); rows = list(request.population.bars); as_of = request.as_of or _parse(str(request.population.bars_descriptor["coverage"]["end_exclusive_utc"])); dependency = _dependency(request, as_of)
    folds: list[WalkForwardFold] = []; predictions: list[Prediction] = []; trades: list[Trade] = []
    blocked: str | None = dependency.status if dependency.status not in ("OK", "DEGRADED") else None
    try: split = _split(request)
    except SplitError as error:
        if error.code in {"TARGET_BAR_MISSING", "TARGET_HORIZON_INVALID"}: return _publish(request, dependency, None, (), (), (), error.code, as_of)
        raise
    if blocked is None:
        for fold in split.folds:
            test_digest = sha256_digest(canonical_json(list(fold.test_membership)))
            selected = _select(rows, fold.validation_membership, candidates, request.population.policy.normalization_window_bars)
            lock = {"fold_id": fold.fold_id, "state": "LOCKED", "candidate_fingerprint": selected.fingerprint, "config_hash": request.config.config_hash, "feature_provenance": dict(selected.feature_provenance), "locked_at_boundary": fold.validation_end_utc, "selection_input": "validation_only", "test_membership_digest_before_selection": test_digest}
            lock_hash = sha256_digest(canonical_json(lock))
            evaluated = WalkForwardFold(fold.fold_id, fold.order, fold.train_membership, fold.validation_membership, fold.test_membership, MappingProxyType({"train_start_utc": fold.train_start_utc, "train_end_utc": fold.train_end_utc, "validation_start_utc": fold.validation_start_utc, "validation_end_utc": fold.validation_end_utc, "test_start_utc": fold.test_start_utc, "test_end_utc": fold.test_end_utc}), MappingProxyType(lock | {"selection_lock_hash": lock_hash}))
            folds.append(evaluated)
            fold_predictions, fold_trades, gap = _evaluate_fold(evaluated, rows, selected, request.population.policy.normalization_window_bars, request.population.policy.target_horizon_bars, request.population.policy.bar_interval_seconds)
            if gap is not None:
                blocked = gap; break
            predictions.extend(fold_predictions)
            trades.extend(fold_trades)
    return _publish(request, dependency, split, tuple(folds), tuple(predictions), tuple(trades), blocked, as_of)


__all__ = ["CandidateVariant", "FactoryRankingEntry", "JUDGE_POLICY_HASH", "Prediction", "Trade", "WalkForwardError", "WalkForwardFold", "WalkForwardRequest", "WalkForwardRun", "evaluate_walk_forward"]
