"""Strict temporal split contracts for walk-forward evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest

if TYPE_CHECKING:
    from .synthetic import FrozenPopulation


class SplitError(RuntimeError):
    """A machine-readable temporal-boundary rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message); self.code = code; self.message = message; self.path = path


@dataclass(frozen=True, slots=True)
class SplitPolicy:
    """The complete, immutable walk-forward boundary declaration."""

    start_at: datetime; bar_interval_seconds: int; train_bars: int; validation_bars: int; test_bars: int
    fold_count: int; lookback_bars: int; normalization_window_bars: int; target_horizon_bars: int
    embargo_bars: int; purge_bars: int; expanding_window: bool

    def __post_init__(self) -> None:
        positive = ("bar_interval_seconds", "train_bars", "validation_bars", "test_bars", "fold_count", "lookback_bars", "normalization_window_bars", "target_horizon_bars")
        for field in positive:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise SplitError("POLICY_INVALID", f"{field} must be a positive integer", f"$.{field}")
        for field in ("embargo_bars", "purge_bars"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SplitError("POLICY_INVALID", f"{field} must be a non-negative integer", f"$.{field}")
        if type(self.expanding_window) is not bool: raise SplitError("POLICY_INVALID", "expanding_window must be boolean", "$.expanding_window")
        if self.start_at.tzinfo is None or self.start_at.utcoffset() is None: raise SplitError("POLICY_INVALID", "start_at must be timezone-aware", "$.start_at")
        normalized = self.start_at.astimezone(timezone.utc).replace(microsecond=0)
        object.__setattr__(self, "start_at", normalized)
        if self.train_bars <= self.lookback_bars + self.target_horizon_bars: raise SplitError("POLICY_INVALID", "train_bars must exceed lookback plus target horizon", "$.train_bars")
        if self.validation_bars <= self.target_horizon_bars + 1 or self.test_bars <= self.target_horizon_bars + 1:
            raise SplitError("POLICY_INVALID", "evaluation windows must provide entries and completed targets", "$.validation_bars")

    def mapping(self) -> dict[str, object]:
        return {"start_at_utc": _z(self.start_at), "bar_interval_seconds": self.bar_interval_seconds, "train_bars": self.train_bars, "validation_bars": self.validation_bars, "test_bars": self.test_bars, "fold_count": self.fold_count, "lookback_bars": self.lookback_bars, "normalization_window_bars": self.normalization_window_bars, "horizon_bars": self.target_horizon_bars, "target_horizon_bars": self.target_horizon_bars, "embargo_bars": self.embargo_bars, "purge_bars": self.purge_bars, "expanding_window": self.expanding_window}

    @property
    def hash(self) -> str:
        return sha256_digest(canonical_json(self.mapping()))


@dataclass(frozen=True, slots=True)
class SplitFold:
    """One chronological train/validation/test boundary set and membership."""

    fold_id: str; order: int; train_start_utc: str; train_end_utc: str; validation_start_utc: str; validation_end_utc: str
    test_start_utc: str; test_end_utc: str; train_membership: tuple[str, ...]; validation_membership: tuple[str, ...]
    test_membership: tuple[str, ...]; selection_lock: Mapping[str, object]

    def mapping(self) -> dict[str, object]:
        return {"fold_id": self.fold_id, "order": self.order, "train_start_utc": self.train_start_utc, "train_end_utc": self.train_end_utc, "validation_start_utc": self.validation_start_utc, "validation_end_utc": self.validation_end_utc, "test_start_utc": self.test_start_utc, "test_end_utc": self.test_end_utc, "train_membership": list(self.train_membership), "validation_membership": list(self.validation_membership), "test_membership": list(self.test_membership), "selection_lock": dict(self.selection_lock)}


@dataclass(frozen=True, slots=True)
class SplitManifest:
    """A frozen population split plus the hash of its exact memberships."""

    policy: SplitPolicy; population_hash: str; folds: tuple[SplitFold, ...]; membership_hash: str

    def mapping(self) -> dict[str, object]:
        return {"schema_version": "gauntlet.walk-forward-split.v1", "policy": self.policy.mapping(), "policy_hash": self.policy.hash, "population_hash": self.population_hash, "fold_order": [fold.order for fold in self.folds], "expanding_window_policy": {"mode": "EXPANDING" if self.policy.expanding_window else "ROLLING", "selection_input": "validation_only"}, "folds": [fold.mapping() for fold in self.folds], "membership_hash": self.membership_hash}


def _z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00") if value.endswith("Z") else None
    except ValueError as error:
        raise SplitError("TIMESTAMP_INVALID", "timestamp must be UTC ISO-8601 ending in Z") from error
    if parsed is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0: raise SplitError("TIMESTAMP_INVALID", "timestamp must be UTC ISO-8601 ending in Z")
    return parsed


def _timestamp(policy: SplitPolicy, index: int) -> str:
    return _z(policy.start_at + timedelta(seconds=index * policy.bar_interval_seconds))


def _membership(population: FrozenPopulation, start: str, signal_end: str, completion_end: str) -> tuple[str, ...]:
    start_at, signal_end_at, end_at = _parse(start), _parse(signal_end), _parse(completion_end)
    rows, bar_times = [], {row.timestamp_utc for row in population.bars}
    for row in population.bars:
        observed = _parse(row.feature_observed_at_utc)
        completed = _parse(row.target_completed_at_utc)
        if observed > _parse(row.timestamp_utc):
            raise SplitError("FUTURE_FEATURE_REJECTED", f"feature for {row.row_id} is observed after its signal", f"$.bars.{row.row_id}")
        signal = _parse(row.timestamp_utc)
        if start_at <= signal < signal_end_at:
            expected_completion = signal + timedelta(seconds=population.policy.target_horizon_bars * population.policy.bar_interval_seconds)
            if row.target_completed_at_utc not in bar_times:
                raise SplitError("TARGET_BAR_MISSING", f"target for {row.row_id} has no bar at {row.target_completed_at_utc}", f"$.bars.{row.row_id}")
            if completed != expected_completion:
                raise SplitError("TARGET_HORIZON_INVALID", f"target for {row.row_id} is not the declared target horizon", f"$.bars.{row.row_id}")
            if completed >= end_at: raise SplitError("TARGET_CROSSES_BOUNDARY", f"target for {row.row_id} crosses the segment completion boundary", f"$.bars.{row.row_id}")
            if completed <= observed: raise SplitError("TARGET_INVALID", f"target for {row.row_id} does not complete after observation", f"$.bars.{row.row_id}")
            rows.append(row.row_id)
    return tuple(rows)


def build_split_manifest(policy: SplitPolicy, population: FrozenPopulation) -> SplitManifest:
    """Build strict, label-isolated memberships without mutating the population."""

    if population.policy != policy:
        raise SplitError("POPULATION_POLICY_MISMATCH", "population was not frozen for this split policy", "$.population")
    actual = population.digest()
    if population.population_hash != actual:
        raise SplitError("POPULATION_MUTATED", "recorded population hash no longer matches its contents", "$.population")
    by_id = {row.row_id: row for row in population.bars}
    if len(by_id) != len(population.bars):
        raise SplitError("ROW_ID_DUPLICATED", "bar row IDs must be unique", "$.bars")
    gap = policy.embargo_bars + policy.purge_bars
    cursor = 0
    folds: list[SplitFold] = []
    seen_tests: set[str] = set()
    for index in range(policy.fold_count):
        train_start = 0 if policy.expanding_window else cursor
        train_signal_end = cursor if index and policy.expanding_window else train_start + policy.train_bars
        train_end = train_signal_end + policy.target_horizon_bars
        validation_start = train_end + gap
        validation_signal_end = validation_start + policy.validation_bars
        validation_end = validation_signal_end + policy.target_horizon_bars
        test_start = validation_end + gap
        test_signal_end = test_start + policy.test_bars
        test_completion = test_signal_end + policy.target_horizon_bars
        boundaries = tuple(_timestamp(policy, item) for item in (train_start, train_end, validation_start, validation_end, test_start, test_completion))
        train = _membership(population, boundaries[0], _timestamp(policy, train_signal_end), boundaries[1])
        validation = _membership(population, boundaries[2], _timestamp(policy, validation_signal_end), boundaries[3])
        test = _membership(population, boundaries[4], _timestamp(policy, test_signal_end), boundaries[5])
        if not train or not validation or not test:
            raise SplitError("SPLIT_EMPTY", f"fold {index + 1} has an empty strict membership", "$.folds")
        if set(train) & set(validation) or set(train) & set(test) or set(validation) & set(test):
            raise SplitError("MEMBERSHIP_OVERLAP", f"fold {index + 1} segment memberships overlap", "$.folds")
        if seen_tests & set(test):
            raise SplitError("TEST_MEMBERSHIP_REUSED", f"fold {index + 1} reuses a prior test row", "$.folds")
        seen_tests.update(test)
        folds.append(SplitFold(f"fold-{index + 1:04d}", index + 1, *boundaries, train, validation, test, {"fold_id": f"fold-{index + 1:04d}", "state": "PENDING", "candidate_fingerprint": None, "locked_at_boundary": boundaries[3], "selection_input": "validation_only"}))
        cursor = test_completion
    manifest = SplitManifest(policy, population.population_hash, tuple(folds), "")
    object.__setattr__(manifest, "membership_hash", sha256_digest(canonical_json([fold.mapping() for fold in folds])))
    return manifest


__all__ = ["SplitError", "SplitFold", "SplitManifest", "SplitPolicy", "build_split_manifest"]
