"""Immutable, frozen-split Kronos adaptation trials."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.contracts.manifests import create_exclusive
from gauntlet.data.descriptors import DescriptorError, load_descriptor_registry
from gauntlet.ledger import Actor, EventRecord, TrialPayload, append_event, append_trial, regenerate_heads, verify_chains
from gauntlet.ledger._common import LedgerError, actor_mapping, data_root_path, validate_digest, validate_timestamp
from gauntlet.model.registry import ModelError, ModelRegistration

ADAPTATION_SCHEMA = "gauntlet.model-adaptation.v1"


@dataclass(frozen=True, slots=True)
class AdaptationWindow:
    """One inclusive UTC window used by a temporal split."""

    start_utc: str; end_utc: str
    def mapping(self) -> dict[str, str]: return {"start_utc": self.start_utc, "end_utc": self.end_utc}


@dataclass(frozen=True, slots=True)
class AdaptationSample:
    """One feature observation and, when complete, its future target."""

    sample_id: str; timestamp_utc: str; available_at_utc: str; features: Mapping[str, object]
    target_value: float | None = None; target_completed_at_utc: str | None = None
    def __post_init__(self) -> None: object.__setattr__(self, "features", MappingProxyType(dict(self.features)))
    def mapping(self) -> dict[str, object]: return {"sample_id": self.sample_id, "timestamp_utc": self.timestamp_utc, "available_at_utc": self.available_at_utc, "features": dict(self.features), "target_value": self.target_value, "target_completed_at_utc": self.target_completed_at_utc}


@dataclass(frozen=True, slots=True)
class AdaptationPolicy:
    """Temporal bars and the only permitted checkpoint-selection scope."""

    bar_interval_seconds: int; lookback_bars: int; normalization_window_bars: int; target_horizon_bars: int
    embargo_bars: int; purge_bars: int; expanding_window: bool; selection_input: str; policy_hash: str = ""
    def mapping(self) -> dict[str, object]: return {"bar_interval_seconds": self.bar_interval_seconds, "lookback_bars": self.lookback_bars, "normalization_window_bars": self.normalization_window_bars, "target_horizon_bars": self.target_horizon_bars, "embargo_bars": self.embargo_bars, "purge_bars": self.purge_bars, "expanding_window": self.expanding_window, "selection_input": self.selection_input}
    def __post_init__(self) -> None: object.__setattr__(self, "policy_hash", sha256_digest(canonical_json(self.mapping())))


@dataclass(frozen=True, slots=True)
class AdaptationFold:
    """Frozen train/validation/test/prospective membership for one ordered fold."""

    fold_id: str; order: int; train_window: AdaptationWindow; validation_window: AdaptationWindow
    test_window: AdaptationWindow; prospective_window: AdaptationWindow | None
    train_membership: tuple[str, ...]; validation_membership: tuple[str, ...]
    test_membership: tuple[str, ...]; prospective_membership: tuple[str, ...] = ()
    def mapping(self) -> dict[str, object]:
        selection = {"fold_id": self.fold_id, "state": "PENDING", "candidate_fingerprint": None, "locked_at_boundary": self.validation_window.end_utc, "selection_input": "validation_only"}
        return {"fold_id": self.fold_id, "order": self.order, "train_window": self.train_window.mapping(), "validation_window": self.validation_window.mapping(), "test_window": self.test_window.mapping(), "prospective_window": self.prospective_window.mapping() if self.prospective_window else None, "train_membership": list(self.train_membership), "validation_membership": list(self.validation_membership), "test_membership": list(self.test_membership), "prospective_membership": list(self.prospective_membership), "selection_lock": selection}


@dataclass(frozen=True, slots=True)
class AdaptationReplay:
    """Every non-input identity needed to reconstruct the selected checkpoint."""

    code_version: str; dependency_lock_hash: str; environment_hash: str; normalization_version: str
    seeds: Mapping[str, object]; sampler: Mapping[str, object]
    def mapping(self) -> dict[str, object]: return {"code_version": self.code_version, "dependency_lock_hash": self.dependency_lock_hash, "environment_hash": self.environment_hash, "normalization_version": self.normalization_version, "seeds": dict(self.seeds), "sampler": dict(self.sampler)}
    def __post_init__(self) -> None: object.__setattr__(self, "seeds", MappingProxyType(dict(self.seeds))); object.__setattr__(self, "sampler", MappingProxyType(dict(self.sampler)))


@dataclass(frozen=True, slots=True)
class AdaptationManifest:
    """A sealed adaptation request and its exact registered source population."""

    adaptation_id: str; venue_track: str; requested_at_utc: str; samples: tuple[AdaptationSample, ...]
    folds: tuple[AdaptationFold, ...]; policy: AdaptationPolicy; replay: AdaptationReplay
    feature_manifest_hash: str; policy_manifest_hash: str; resolved_config_hash: str
    source_descriptor_hashes: tuple[str, ...]; source_content_hashes: tuple[str, ...]
    search_space: Mapping[str, object]; actor: Actor; prior_trial_id: str | None = None
    population_hash: str = ""; split_hash: str = ""; manifest_hash: str = ""
    def mapping(self) -> dict[str, object]: return {"schema_version": ADAPTATION_SCHEMA, "adaptation_id": self.adaptation_id, "venue_track": self.venue_track, "requested_at_utc": self.requested_at_utc, "samples": [row.mapping() for row in self.samples], "folds": [fold.mapping() for fold in self.folds], "policy": self.policy.mapping(), "policy_hash": self.policy.policy_hash, "feature_manifest_hash": self.feature_manifest_hash, "policy_manifest_hash": self.policy_manifest_hash, "resolved_config_hash": self.resolved_config_hash, "source_descriptor_hashes": list(self.source_descriptor_hashes), "source_content_hashes": list(self.source_content_hashes), "search_space": dict(self.search_space), "replay": self.replay.mapping(), "prior_trial_id": self.prior_trial_id}
    def ledger_mapping(self) -> dict[str, object]:
        value = self.mapping(); replay = dict(value["replay"]); replay["dependency_lock_digest"] = replay.pop("dependency_lock_hash"); value["replay"] = replay; return value
    def __post_init__(self) -> None:
        object.__setattr__(self, "search_space", MappingProxyType(dict(self.search_space))); population = {"samples": [row.mapping() for row in self.samples]}; split = [fold.mapping() for fold in self.folds]
        object.__setattr__(self, "population_hash", sha256_digest(canonical_json(population))); object.__setattr__(self, "split_hash", sha256_digest(canonical_json(split))); object.__setattr__(self, "manifest_hash", sha256_digest(canonical_json(self.mapping())))


@dataclass(frozen=True, slots=True)
class AdaptationRun:
    """A sealed adaptation result and its immutable physical evidence."""

    run_hash: str; artifact_hash: str; trial_id: str; trial_head_hash: str; event_head_hash: str
    status: str; gate_state: str; replayable: bool; population_hash: str; checkpoint_hash: str
    canonical_bytes: bytes; payload: Mapping[str, object]; artifact_path: Path; manifest_path: Path
    logs_path: Path; checkpoint_path: Path; event_record: Mapping[str, object]; replayed: bool


def _invalid(message: str, path: str, code: str = "ADAPTATION_INVALID") -> ModelError: return ModelError(code, message, path)
def _digest(value: object, field: str) -> str:
    try: validate_digest(value, f"$.{field}")
    except LedgerError as error: raise _invalid(f"{field} must be sha256:<64 lowercase hexadecimal>", f"$.{field}", "ADAPTATION_REPLAY_INCOMPLETE") from error
    assert isinstance(value, str); return value
def _time(value: object, field: str) -> datetime:
    try: validate_timestamp(value, f"$.{field}")
    except LedgerError as error: raise _invalid(f"{field} must be UTC ISO-8601", f"$.{field}") from error
    assert isinstance(value, str); return datetime.fromisoformat(value[:-1] + "+00:00")
def _finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)): raise _invalid(f"{field} must be finite", f"$.{field}")
    return float(value)


def _validate_policy(policy: AdaptationPolicy) -> None:
    for field in ("bar_interval_seconds", "lookback_bars", "normalization_window_bars", "target_horizon_bars", "embargo_bars", "purge_bars"):
        if isinstance(getattr(policy, field), bool) or not isinstance(getattr(policy, field), int) or getattr(policy, field) < 1: raise _invalid(f"{field} must be a positive integer", f"$.policy.{field}")
    if policy.selection_input != "validation_only": raise _invalid("checkpoint selection may use validation only", "$.policy.selection_input", "SELECTION_SCOPE_INVALID")


def _validate_replay(replay: AdaptationReplay) -> None:
    for field in ("code_version", "normalization_version"):
        if not isinstance(getattr(replay, field), str) or not getattr(replay, field).strip(): raise _invalid(f"replay.{field} is required", f"$.replay.{field}", "ADAPTATION_REPLAY_INCOMPLETE")
    for field in ("dependency_lock_hash", "environment_hash"): _digest(getattr(replay, field), f"replay.{field}")
    if not replay.seeds: raise _invalid("replay seeds are required", "$.replay.seeds", "ADAPTATION_REPLAY_INCOMPLETE")
    for name, seed in replay.seeds.items():
        if not isinstance(name, str) or not name.strip() or isinstance(seed, bool) or not isinstance(seed, int) or seed < 0: raise _invalid("replay seeds must map names to non-negative integers", f"$.replay.seeds.{name}", "ADAPTATION_REPLAY_INCOMPLETE")
    sampler = replay.sampler
    if not sampler or sampler.get("deterministic") is not True or not isinstance(sampler.get("name"), str) or not sampler["name"].strip(): raise _invalid("complete deterministic sampler settings are required", "$.replay.sampler", "ADAPTATION_REPLAY_INCOMPLETE")
    if _finite(sampler.get("temperature"), "replay.sampler.temperature") <= 0 or isinstance(sampler.get("top_k"), bool) or not isinstance(sampler.get("top_k"), int) or sampler["top_k"] < 1: raise _invalid("sampler temperature and top_k must be positive", "$.replay.sampler", "ADAPTATION_REPLAY_INCOMPLETE")


def _rates(manifest: AdaptationManifest) -> tuple[float, ...]:
    raw = manifest.search_space.get("learning_rates")
    if not isinstance(raw, list) or not raw: raise _invalid("learning_rates must be a non-empty array", "$.search_space.learning_rates")
    values = tuple(_finite(item, "search_space.learning_rates") for item in raw)
    if any(item <= 0 for item in values) or len(set(values)) != len(values): raise _invalid("learning rates must be positive and unique", "$.search_space.learning_rates")
    return values


def _rows(manifest: AdaptationManifest) -> dict[str, AdaptationSample]:
    rows: dict[str, AdaptationSample] = {}
    for index, row in enumerate(manifest.samples):
        if not isinstance(row.sample_id, str) or not row.sample_id.strip() or row.sample_id in rows: raise _invalid("sample IDs must be unique non-empty strings", f"$.samples[{index}].sample_id")
        observed, available = _time(row.timestamp_utc, f"samples[{index}].timestamp_utc"), _time(row.available_at_utc, f"samples[{index}].available_at_utc")
        if available < observed or not row.features: raise _invalid("each feature must be available at or after observation and non-empty", f"$.samples[{index}]", "FOLD_BOUNDARY_LEAK")
        for name, value in row.features.items():
            if not isinstance(name, str) or not name.strip(): raise _invalid("feature names must be non-empty", f"$.samples[{index}].features")
            _finite(value, f"samples[{index}].features.{name}")
        if row.target_value is None:
            if row.target_completed_at_utc is not None: raise _invalid("unresolved target cannot declare completion", f"$.samples[{index}].target_completed_at_utc")
        else:
            _finite(row.target_value, f"$.samples[{index}].target_value")
            if row.target_completed_at_utc is None: raise _invalid("resolved target requires completion", f"$.samples[{index}].target_completed_at_utc")
            completed = _time(row.target_completed_at_utc, f"samples[{index}].target_completed_at_utc")
            expected = observed.timestamp() + manifest.policy.target_horizon_bars * manifest.policy.bar_interval_seconds
            if completed.timestamp() != expected: raise _invalid("target completion does not match the declared horizon", f"$.samples[{index}].target_completed_at_utc", "FOLD_BOUNDARY_LEAK")
        rows[row.sample_id] = row
    return rows


def _validate_folds(manifest: AdaptationManifest, rows: dict[str, AdaptationSample]) -> None:
    interval = manifest.policy.bar_interval_seconds; seen_tests: set[str] = set(); prior_end: datetime | None = None
    for index, fold in enumerate(manifest.folds):
        path = f"$.folds[{index}]"
        if fold.order != index + 1 or not fold.fold_id.strip(): raise _invalid("fold order must be contiguous and IDs non-empty", f"{path}.order")
        train_start, train_end = _time(fold.train_window.start_utc, f"{path}.train_window.start_utc"), _time(fold.train_window.end_utc, f"{path}.train_window.end_utc")
        validation_start, validation_end = _time(fold.validation_window.start_utc, f"{path}.validation_window.start_utc"), _time(fold.validation_window.end_utc, f"{path}.validation_window.end_utc")
        test_start, test_end = _time(fold.test_window.start_utc, f"{path}.test_window.start_utc"), _time(fold.test_window.end_utc, f"{path}.test_window.end_utc")
        if not train_start < train_end < validation_start < validation_end < test_start < test_end: raise _invalid("temporal windows must be strictly ordered", path, "FOLD_BOUNDARY_LEAK")
        if (validation_start - train_end).total_seconds() < (manifest.policy.embargo_bars + manifest.policy.purge_bars) * interval: raise _invalid("validation begins before embargo/purge gaps end", path, "EMBARGO_PURGE_INVALID")
        if prior_end is not None and train_end <= prior_end: raise _invalid("later folds must move forward in time", path)
        if fold.prospective_window is not None:
            prospective = fold.prospective_window
            prospective_start = _time(prospective.start_utc, f"{path}.prospective_window.start_utc"); prospective_end = _time(prospective.end_utc, f"{path}.prospective_window.end_utc")
            if not test_end < prospective_start < prospective_end: raise _invalid("prospective window must follow test", path, "FOLD_BOUNDARY_LEAK")
        memberships = ((fold.train_membership, train_start, train_end), (fold.validation_membership, validation_start, validation_end), (fold.test_membership, test_start, test_end))
        if fold.prospective_window is not None: memberships = (*memberships, (fold.prospective_membership, _time(fold.prospective_window.start_utc, "prospective"), _time(fold.prospective_window.end_utc, "prospective")))
        for membership, start, end in memberships:
            if len(set(membership)) != len(membership) or not membership: raise _invalid("each fold segment needs unique non-empty membership", path)
            for sample_id in membership:
                if sample_id not in rows: raise _invalid(f"unknown sample {sample_id!r}", path, "POPULATION_INVALID")
                row = rows[sample_id]; observed = _time(row.timestamp_utc, "samples"); available = _time(row.available_at_utc, "samples")
                if observed < start or observed > end or available > end: raise _invalid(f"sample {sample_id!r} leaks its segment boundary", path, "FOLD_BOUNDARY_LEAK")
                if row.target_value is None and (membership is not fold.prospective_membership): raise _invalid(f"unresolved target {sample_id!r}", path, "FOLD_BOUNDARY_LEAK")
                if row.target_value is not None:
                    completed = _time(row.target_completed_at_utc or row.timestamp_utc, "samples")
                    if membership is fold.prospective_membership: raise _invalid("prospective outcomes cannot enter adaptation", path, "FOLD_BOUNDARY_LEAK")
                    if completed > end: raise _invalid(f"target completion crosses boundary for {sample_id!r}", path, "FOLD_BOUNDARY_LEAK")
        if set(fold.train_membership) & set(fold.validation_membership) or set(fold.train_membership) & set(fold.test_membership) or set(fold.validation_membership) & set(fold.test_membership): raise _invalid("train, validation, and test memberships overlap", path)
        if seen_tests & (set(fold.train_membership) | set(fold.validation_membership)): raise _invalid("prior frozen test membership cannot train or tune", path, "POPULATION_INVALID")
        if seen_tests & set(fold.test_membership): raise _invalid("frozen test membership cannot be reused", path, "POPULATION_INVALID")
        seen_tests.update(fold.test_membership); prior_end = validation_end
        if manifest.policy.lookback_bars > len(fold.train_membership) or manifest.policy.normalization_window_bars > len(fold.train_membership): raise _invalid("lookback/normalization windows exceed train bars", path)


def _registration(manifest: AdaptationManifest, model: ModelRegistration) -> tuple[dict[str, object], dict[str, object], bytes]:
    try: records = load_descriptor_registry()
    except DescriptorError as error: raise _invalid(error.message, error.path, "MODEL_UNREGISTERED") from error
    stored = records.get(model.descriptor_hash)
    if stored is None or stored.value.get("artifact_id") != model.model_fingerprint: raise _invalid("model descriptor is unregistered", "$.model", "MODEL_UNREGISTERED")
    try: entry: object = json.loads(model.entry_path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as error: raise _invalid(f"model entry cannot be read: {error}", str(model.entry_path), "MODEL_UNREGISTERED") from error
    if not isinstance(entry, dict) or entry.get("model_fingerprint") != model.model_fingerprint: raise _invalid("model entry does not match fingerprint", "$.model", "MODEL_UNREGISTERED")
    checkpoints: dict[str, object] = {}
    base = model.base_checkpoint_path.read_bytes() if model.base_checkpoint_path.is_file() and not model.base_checkpoint_path.is_symlink() else None
    if base is None or sha256_digest(base) != model.base_checkpoint_hash: raise _invalid("base checkpoint bytes are missing", str(model.base_checkpoint_path), "ADAPTATION_REPLAY_INCOMPLETE")
    checkpoints["base"] = {"hash": model.base_checkpoint_hash, "status": "READY"}
    if model.fine_tuned_checkpoint_path is not None:
        fine = model.fine_tuned_checkpoint_path.read_bytes() if model.fine_tuned_checkpoint_path.is_file() and not model.fine_tuned_checkpoint_path.is_symlink() else None
        if fine is None or model.fine_tuned_checkpoint_hash is None or sha256_digest(fine) != model.fine_tuned_checkpoint_hash: raise _invalid("fine-tuned checkpoint bytes are missing", str(model.fine_tuned_checkpoint_path), "ADAPTATION_REPLAY_INCOMPLETE")
        checkpoints["fine_tuned"] = {"hash": model.fine_tuned_checkpoint_hash, "status": "READY"}
    if len(manifest.source_descriptor_hashes) != len(manifest.source_content_hashes) or not manifest.source_descriptor_hashes: raise _invalid("exact source descriptor/content hash pairs are required", "$.source_descriptor_hashes")
    sources: dict[str, object] = {}
    for index, (descriptor_hash, content_hash) in enumerate(zip(manifest.source_descriptor_hashes, manifest.source_content_hashes, strict=True)):
        _digest(descriptor_hash, f"source_descriptor_hashes[{index}]"); _digest(content_hash, f"source_content_hashes[{index}]")
        source = records.get(descriptor_hash)
        if source is None or source.value.get("content_hash") != content_hash: raise _invalid(f"source descriptor {descriptor_hash!r} is unregistered or changed", f"$.source_descriptor_hashes[{index}]", "SOURCE_UNREGISTERED")
        sources[descriptor_hash] = dict(source.value)
    expected_population = sha256_digest(canonical_json({"population": [row.mapping() for row in manifest.samples]}))
    if expected_population not in set(manifest.source_content_hashes): raise _invalid("manifest population is not committed by an exact registered source", "$.source_content_hashes", "SOURCE_POPULATION_MISMATCH")
    return sources, checkpoints, base


def _statistics(rows: tuple[AdaptationSample, ...], window: int) -> dict[str, object]:
    selected = rows[-window:]; values = tuple(_finite(row.features.get("value"), "features.value") for row in selected)
    mean = sum(values) / len(values); variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {"method": "TRAIN_ONLY_POPULATION_ZSCORE", "uses_future": False, "window_bars": window, "input_sample_ids": [row.sample_id for row in selected], "bounds": {"start_utc": selected[0].timestamp_utc, "end_utc": selected[-1].timestamp_utc}, "statistics": {"mean": mean, "population_variance": variance}}


def _checkpoint(base: bytes, material: Mapping[str, object]) -> tuple[bytes, str]:
    content = b"GAUNTLET-KRONOS-ADAPTATION\x00" + base + canonical_json(material); return content, sha256_digest(content)


def _log(event_id: str, actor: Actor, timestamp: str, inputs: tuple[Mapping[str, object], ...], reason: str) -> dict[str, object]:
    return {"event_id": event_id, "actor": actor_mapping(actor), "timestamp_utc": timestamp, "metric_inputs": [dict(item) for item in inputs], "reason": reason}


def _train(manifest: AdaptationManifest, model: ModelRegistration, model_checkpoints: Mapping[str, object], base: bytes) -> tuple[dict[str, object], bytes, str]:
    rows = _rows(manifest); _validate_folds(manifest, rows); rates = _rates(manifest); outputs: list[dict[str, object]] = []; logs: list[dict[str, object]] = []; aggregate: dict[float, list[float]] = {rate: [] for rate in rates}
    for fold in manifest.folds:
        train = tuple(rows[sample_id] for sample_id in fold.train_membership); validation = tuple(rows[sample_id] for sample_id in fold.validation_membership); normalization = _statistics(train, manifest.policy.normalization_window_bars); statistics = normalization["statistics"]; assert isinstance(statistics, dict); deviation = math.sqrt(float(statistics["population_variance"])) or 1.0
        candidates: list[dict[str, object]] = []
        for rate in rates:
            material = {"candidate": rate, "fold": fold.fold_id, "manifest": manifest.manifest_hash, "model": model.model_fingerprint, "normalization": normalization, "samples": list(fold.train_membership), "seeds": dict(manifest.replay.seeds)}
            _, checkpoint_hash = _checkpoint(base, material)
            score = sum(float(row.target_value or 0.0) * math.tanh(rate * (float(row.features.get("value")) - float(statistics["mean"])) / deviation) for row in validation) / len(validation)
            aggregate[rate].append(score); candidates.append({"candidate_id": f"lr-{rate:g}", "learning_rate": rate, "checkpoint_hash": checkpoint_hash, "validation_metric": score, "metric_input_hash": sha256_digest(canonical_json(list(fold.validation_membership)))})
        selected = max(candidates, key=lambda item: (float(item["validation_metric"]), str(item["candidate_id"])))
        lock = {"fold_id": fold.fold_id, "state": "LOCKED", "candidate_fingerprint": selected["checkpoint_hash"], "config_hash": manifest.resolved_config_hash, "locked_at_boundary": fold.validation_window.end_utc, "selection_input": "validation_only", "test_membership_digest_before_selection": sha256_digest(canonical_json(list(fold.test_membership))), "prospective_membership_digest_before_selection": sha256_digest(canonical_json(list(fold.prospective_membership))), "test_targets_read": False, "prospective_targets_read": False}
        lock_hash = sha256_digest(canonical_json(lock)); train_hash = sha256_digest(canonical_json(list(fold.train_membership))); validation_hash = sha256_digest(canonical_json(list(fold.validation_membership)))
        logs.append(_log(f"adaptation-train-{fold.fold_id}", manifest.actor, fold.train_window.end_utc, ({"kind": "train_membership", "hash": train_hash}, {"kind": "normalization", "hash": sha256_digest(canonical_json(normalization))}), "deterministic training uses train-complete observations only"))
        logs.append(_log(f"adaptation-select-{fold.fold_id}", manifest.actor, fold.validation_window.end_utc, ({"kind": "validation_membership", "hash": validation_hash}, {"kind": "candidate_metrics", "hash": sha256_digest(canonical_json(candidates))}), "highest validation metric wins; test and prospective targets are unread"))
        outputs.append({"fold_id": fold.fold_id, "order": fold.order, "boundaries": {"train": fold.train_window.mapping(), "validation": fold.validation_window.mapping(), "test": fold.test_window.mapping(), "prospective": fold.prospective_window.mapping() if fold.prospective_window else None}, "memberships": {"train": list(fold.train_membership), "validation": list(fold.validation_membership), "test": list(fold.test_membership), "prospective": list(fold.prospective_membership)}, "policy": manifest.policy.mapping(), "normalization": normalization, "candidates": candidates, "selected_checkpoint_hash": selected["checkpoint_hash"], "selection_lock": lock | {"selection_lock_hash": lock_hash}})
    selected_rate = max(rates, key=lambda rate: (sum(aggregate[rate]) / len(aggregate[rate]), -rate)); final_ids = tuple(sorted({sample_id for fold in manifest.folds for sample_id in (*fold.train_membership, *fold.validation_membership)}, key=lambda item: rows[item].timestamp_utc)); final_rows = tuple(rows[sample_id] for sample_id in final_ids); final_normalization = _statistics(final_rows, manifest.policy.normalization_window_bars)
    material = {"candidate": selected_rate, "folds": [fold.fold_id for fold in manifest.folds], "manifest": manifest.manifest_hash, "model": model.model_fingerprint, "normalization": final_normalization, "samples": list(final_ids), "replay": manifest.replay.mapping(), "validation_metric": sum(aggregate[selected_rate]) / len(aggregate[selected_rate])}
    checkpoint, checkpoint_hash = _checkpoint(base, material); selection = {"selection_input": "validation_only", "selected_candidate_id": f"lr-{selected_rate:g}", "selected_checkpoint_hash": checkpoint_hash, "aggregate_validation_metric": sum(aggregate[selected_rate]) / len(aggregate[selected_rate]), "fold_candidates": [{"fold_id": output["fold_id"], "candidates": output["candidates"]} for output in outputs], "test_targets_read": False, "prospective_targets_read": False, "test_membership_digests": [output["selection_lock"]["test_membership_digest_before_selection"] for output in outputs], "reason": "highest aggregate validation metric; selection boundary is the final validation end"}
    metric_projection = [{"candidate_id": f"lr-{rate:g}", "scores": aggregate[rate]} for rate in rates]
    logs.append(_log("adaptation-checkpoint-final", manifest.actor, max(fold.validation_window.end_utc for fold in manifest.folds), ({"kind": "fold_validation_metrics", "hash": sha256_digest(canonical_json(metric_projection))}, {"kind": "final_tuning_population", "hash": sha256_digest(canonical_json(list(final_ids)))}), "aggregate validation-only score selects the final checkpoint"))
    fold_manifest = {"schema_version": "gauntlet.model-adaptation-splits.v1", "policy": manifest.policy.mapping(), "policy_hash": manifest.policy.policy_hash, "population_hash": manifest.population_hash, "fold_order": [fold.order for fold in manifest.folds], "folds": [fold.mapping() for fold in manifest.folds], "membership_hash": manifest.split_hash}
    execution = {"schema_version": ADAPTATION_SCHEMA, "manifest": manifest.mapping(), "fold_manifest": fold_manifest, "folds": outputs, "checkpoint_selection": selection, "logs": logs, "checkpoint_hash": checkpoint_hash, "model_fingerprint": model.model_fingerprint}
    run_hash = sha256_digest(canonical_json(execution)); return {"fold_manifest": fold_manifest, "folds": outputs, "checkpoint_selection": selection, "logs": logs, "run_hash": run_hash, "model_checkpoints": model_checkpoints}, checkpoint, checkpoint_hash


def _prior(root: Path, manifest: AdaptationManifest) -> dict[str, object] | None:
    ledger = root / "ledger" / "trials.jsonl"
    if not ledger.is_file(): return None
    found: dict[str, object] | None = None
    for line in ledger.read_bytes().splitlines():
        value: object = json.loads(line)
        if not isinstance(value, dict): continue
        parameters = value.get("payload", {}).get("parameters", {}) if isinstance(value.get("payload"), dict) else {}
        adaptation = parameters.get("adaptation") if isinstance(parameters, dict) else None
        if isinstance(adaptation, dict) and adaptation.get("adaptation_id") == manifest.adaptation_id: found = value
    return found


def _trial(manifest: AdaptationManifest, model: ModelRegistration, sources: Mapping[str, object], prior: dict[str, object] | None, root: Path) -> tuple[str, str, bool]:
    trial_id = f"adaptation-{manifest.manifest_hash}"; ledger = root / "ledger" / "trials.jsonl"
    if ledger.is_file():
        for line in ledger.read_bytes().splitlines():
            value: object = json.loads(line)
            if isinstance(value, dict) and value.get("trial_id") == trial_id: return trial_id, str(value["entry_hash"]), True
    prior_parameters = prior.get("payload", {}).get("parameters", {}) if prior else {}; prior_adaptation = prior_parameters.get("adaptation", {}) if isinstance(prior_parameters, dict) else {}
    prior_ids = (str(prior["trial_id"]),) if prior and prior.get("trial_id") != trial_id else ()
    if manifest.prior_trial_id: prior_ids = (*prior_ids, manifest.prior_trial_id)
    dependencies = ({"artifact_id": model.model_fingerprint, "relation": "requires", "descriptor_hash": model.descriptor_hash, "descriptor_id": f"model-{model.model_id}-{model.model_fingerprint[7:19]}"}, *tuple({"artifact_id": str(value["artifact_id"]), "relation": "requires", "descriptor_hash": digest, "descriptor_id": str(value["descriptor_id"])} for digest, value in sorted(sources.items())))
    payload = TrialPayload(trial_id, manifest.adaptation_id, manifest.venue_track, manifest.requested_at_utc, "Adapt Kronos without evaluation leakage", "Checkpoint is selected on validation only and replay is complete", "No checkpoint is produced when temporal or replay integrity fails", "model-adaptation", prior_ids, None, {"start": manifest.samples[0].timestamp_utc, "end": manifest.samples[-1].timestamp_utc}, manifest.split_hash, tuple(sorted((*manifest.source_descriptor_hashes, model.descriptor_hash))), True, manifest.feature_manifest_hash, sha256_digest(canonical_json(manifest.replay.normalization_version)), {"adaptation": {"adaptation_id": manifest.adaptation_id, "manifest_hash": manifest.manifest_hash, "population_hash": manifest.population_hash, "prior_population_hash": prior_adaptation.get("population_hash"), "model_fingerprint": model.model_fingerprint}, "manifest": manifest.ledger_mapping(), "model_checkpoints": dict(_model_checkpoint_projection(model))}, dict(manifest.search_space), {"mode": "local-single-owner", "walk_forward": False}, (), "kronos-adaptation", "information-source", {"adaptation_runs": 1}, {"condition": "integrity-or-validation-failure"}, {"mode": "frozen-temporal-splits"}, {"code": manifest.replay.code_version, "normalization": manifest.replay.normalization_version, "policy": manifest.policy.policy_hash}, manifest.resolved_config_hash, dependencies, "GATE_CRITICAL")
    result = append_trial(payload, manifest.actor, regenerate_heads(root).trials.head_hash, data_root=root)
    return trial_id, result.head_hash, False
def _model_checkpoint_projection(model: ModelRegistration) -> dict[str, object]: return {"base": model.base_checkpoint_hash, **({"fine_tuned": model.fine_tuned_checkpoint_hash} if model.fine_tuned_checkpoint_hash else {})}


def _report(manifest: AdaptationManifest, model: ModelRegistration, trained: dict[str, object], checkpoint_hash: str, trial_id: str) -> dict[str, object]:
    run_hash = str(trained["run_hash"]); paths = {"manifest": f"model/adaptations/{run_hash}/manifest.json", "logs": f"model/adaptations/{run_hash}/logs.json", "checkpoint": f"model/adaptations/{run_hash}/checkpoint.bin", "run": f"model/adaptations/{run_hash}/run.json"}
    replay = manifest.replay.mapping() | {"source_descriptor_hashes": list(manifest.source_descriptor_hashes), "source_content_hashes": list(manifest.source_content_hashes), "checkpoint": {"hash": checkpoint_hash, "path": paths["checkpoint"], "base_model_hash": model.base_checkpoint_hash}, "model_checkpoints": dict(trained["model_checkpoints"])}
    report = {"schema_version": ADAPTATION_SCHEMA, "status": "OK", "gate_state": "PASS", "requested_at_utc": manifest.requested_at_utc, "actor": actor_mapping(manifest.actor), "trial_id": trial_id, "run_hash": run_hash, "fingerprints": {"manifest": manifest.manifest_hash, "population": manifest.population_hash, "split": manifest.split_hash, "model": model.model_fingerprint, "feature": manifest.feature_manifest_hash, "policy": manifest.policy.policy_hash, "config": manifest.resolved_config_hash}, "source_descriptor_hashes": list(manifest.source_descriptor_hashes), "fold_manifest": trained["fold_manifest"], "folds": trained["folds"], "checkpoint_selection": trained["checkpoint_selection"], "replay": replay, "logs": trained["logs"]}
    report["artifact_files"] = [{"path": paths["manifest"], "hash": sha256_digest(canonical_json(manifest.mapping()))}, {"path": paths["logs"], "hash": sha256_digest(canonical_json(trained["logs"]))}, {"path": paths["checkpoint"], "hash": checkpoint_hash}, {"path": paths["run"], "hash": sha256_digest(canonical_json(report))}]
    return report


def _write(root: Path, report: dict[str, object], manifest: AdaptationManifest, trained: dict[str, object], checkpoint: bytes) -> tuple[Path, Path, Path, Path, bool]:
    destination = root / "model" / "adaptations" / str(report["run_hash"]); run = destination / "run.json"; contents = {destination / "manifest.json": canonical_json(manifest.mapping()), destination / "logs.json": canonical_json(trained["logs"]), destination / "checkpoint.bin": checkpoint, run: canonical_json(report)}
    if run.is_file():
        for path, content in contents.items():
            if path.is_symlink() or not path.is_file() or path.read_bytes() != content: raise _invalid("existing adaptation artifacts differ from deterministic replay", str(path), "ARTIFACT_MISMATCH")
        return run, destination / "manifest.json", destination / "logs.json", destination / "checkpoint.bin", True
    created: list[Path] = []
    try:
        for path, content in contents.items(): created.append(create_exclusive(path, content))
    except BaseException:
        for path in created:
            if path.exists(): path.unlink()
        raise
    return run, destination / "manifest.json", destination / "logs.json", destination / "checkpoint.bin", False


def _event(root: Path, manifest: AdaptationManifest, report: dict[str, object], trial_id: str, artifact_hash: str) -> tuple[str, dict[str, object], bool]:
    event_id = f"model-adaptation-{artifact_hash}"; ledger = root / "ledger" / "events.jsonl"
    if ledger.is_file():
        for line in ledger.read_bytes().splitlines():
            value: object = json.loads(line)
            if isinstance(value, dict) and value.get("event_id") == event_id: return str(value["event_hash"]), dict(value), True
    event = EventRecord(event_id, manifest.requested_at_utc, manifest.actor, "snapshot.write", f"model-adaptation:{report['run_hash']}", sha256_digest(canonical_json({"manifest_hash": manifest.manifest_hash, "model_fingerprint": report["fingerprints"]["model"]})), artifact_hash, "OK", None, {"run_id": report["run_hash"], "trial_id": trial_id, "phase": "model-adaptation"})
    appended = append_event(event, regenerate_heads(root).events.head_hash, data_root=root); return appended.head_hash, dict(appended.record), False


def run_adaptation(manifest: AdaptationManifest, model: ModelRegistration) -> AdaptationRun:
    """Register first, then train and seal one validation-selected adaptation."""
    if not isinstance(manifest, AdaptationManifest): raise _invalid("manifest must be an AdaptationManifest", "$.manifest")
    if not isinstance(model, ModelRegistration): raise _invalid("model must be a ModelRegistration", "$.model")
    if not manifest.adaptation_id.strip() or manifest.venue_track not in {"solana_dex", "hyperliquid", "external", "cross_venue_transfer"}: raise _invalid("adaptation_id and registered venue are required", "$.manifest")
    if not manifest.samples or not manifest.folds: raise _invalid("samples and folds are required", "$.manifest")
    _time(manifest.requested_at_utc, "requested_at_utc"); actor_mapping(manifest.actor); _validate_policy(manifest.policy); _validate_replay(manifest.replay)
    for field in ("feature_manifest_hash", "policy_manifest_hash", "resolved_config_hash"): _digest(getattr(manifest, field), field)
    _rates(manifest)
    root = data_root_path(None); sources, model_checkpoints, base = _registration(manifest, model); rows = _rows(manifest); _validate_folds(manifest, rows); prior = _prior(root, manifest); trial_id, trial_head, _ = _trial(manifest, model, sources, prior, root)
    trained, checkpoint, checkpoint_hash = _train(manifest, model, model_checkpoints, base); report = _report(manifest, model, trained, checkpoint_hash, trial_id); artifact_path, manifest_path, logs_path, checkpoint_path, artifact_replayed = _write(root, report, manifest, trained, checkpoint); artifact_hash = sha256_digest(canonical_json(report)); event_head, event_record, event_replayed = _event(root, manifest, report, trial_id, artifact_hash)
    if not verify_chains(root).valid: raise _invalid("ledger verification failed after adaptation", "$", "ADAPTATION_UNVERIFIED")
    return AdaptationRun(str(report["run_hash"]), artifact_hash, trial_id, trial_head, event_head, "OK", "PASS", True, manifest.population_hash, checkpoint_hash, canonical_json(report), MappingProxyType(report), artifact_path, manifest_path, logs_path, checkpoint_path, MappingProxyType(event_record), artifact_replayed or event_replayed)

__all__ = ["ADAPTATION_SCHEMA", "AdaptationFold", "AdaptationManifest", "AdaptationPolicy", "AdaptationReplay", "AdaptationRun", "AdaptationSample", "AdaptationWindow", "run_adaptation"]
