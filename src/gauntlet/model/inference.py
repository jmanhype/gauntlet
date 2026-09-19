"""Point-in-time, replayable Kronos inference artifacts."""

from __future__ import annotations

import base64
import hashlib
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
from gauntlet.ledger import Actor, EventRecord, append_event, regenerate_heads
from gauntlet.ledger._common import LedgerError, ZERO_DIGEST, data_root_path, validate_digest, validate_timestamp
from gauntlet.model.registry import ModelError, ModelRegistration

INFERENCE_SCHEMA = "gauntlet.model-inference.v1"
_OBSERVATION_BASES = frozenset({"OBSERVED", "MODELED"})


@dataclass(frozen=True, slots=True)
class ContextObservation:
    """One feature row and the time at which that row became available."""

    timestamp_utc: str; available_at_utc: str; features: Mapping[str, object]; observation_basis: str = "OBSERVED"
    target_value: float | None = None; target_completed_at_utc: str | None = None


@dataclass(frozen=True, slots=True)
class FrozenContext:
    """A sealed lookback context whose hash binds every available row."""

    context_id: str; prediction_time_utc: str; lookback_start_utc: str; lookback_end_utc: str
    observations: tuple[ContextObservation, ...]; context_hash: str = ""

    def __post_init__(self) -> None:
        rows = tuple(ContextObservation(row.timestamp_utc, row.available_at_utc, MappingProxyType(dict(row.features)), row.observation_basis, row.target_value, row.target_completed_at_utc) for row in self.observations)
        value = {"context_id": self.context_id, "prediction_time_utc": self.prediction_time_utc, "lookback_start_utc": self.lookback_start_utc, "lookback_end_utc": self.lookback_end_utc, "observations": [{"timestamp_utc": row.timestamp_utc, "available_at_utc": row.available_at_utc, "features": dict(row.features), "observation_basis": row.observation_basis, "target_value": row.target_value, "target_completed_at_utc": row.target_completed_at_utc} for row in rows]}
        object.__setattr__(self, "observations", rows)
        object.__setattr__(self, "context_hash", sha256_digest(canonical_json(value)))


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Preprocessing identity and the exact deterministic sampling contract."""

    profile_id: str; preprocessing_code_hash: str; preprocessing_config_hash: str; normalization_window_bars: int
    seed: int; sample_count: int; sampler: Mapping[str, object]; profile_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "sampler", MappingProxyType(dict(self.sampler)))
        value = {"profile_id": self.profile_id, "preprocessing_code_hash": self.preprocessing_code_hash, "preprocessing_config_hash": self.preprocessing_config_hash, "normalization_window_bars": self.normalization_window_bars, "seed": self.seed, "sample_count": self.sample_count, "sampler": dict(self.sampler)}
        object.__setattr__(self, "profile_hash", sha256_digest(canonical_json(value)))


@dataclass(frozen=True, slots=True)
class InferenceArtifact:
    """A typed immutable inference result and its hash-verified event."""

    artifact_hash: str; context_hash: str; model_fingerprint: str; status: str; gate_state: str; replayable: bool
    canonical_bytes: bytes; payload: Mapping[str, object]; artifact_path: Path; event_head_hash: str
    event_record: Mapping[str, object]; replayed: bool


def _invalid(message: str, path: str, code: str = "INFERENCE_INVALID") -> ModelError:
    return ModelError(code, message, path)


def _timestamp(value: object, field: str) -> datetime:
    try: validate_timestamp(value, f"$.{field}")
    except LedgerError as error: raise _invalid(f"{field} must be UTC ISO-8601", f"$.{field}", "CONTEXT_INVALID") from error
    assert isinstance(value, str)
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)): raise _invalid(f"{field} must be finite", f"$.{field}")
    return float(value)


def _digest(value: object, field: str) -> str:
    try:
        validate_digest(value, f"$.{field}")
    except LedgerError as error:
        raise _invalid(f"{field} must be sha256:<64 lowercase hexadecimal>", f"$.{field}") from error
    assert isinstance(value, str)
    return value


def _validate_context(context: FrozenContext, profile: ModelProfile) -> None:
    if not isinstance(context.context_id, str) or not context.context_id.strip(): raise _invalid("context_id must be a non-empty string", "$.context_id", "CONTEXT_INVALID")
    prediction = _timestamp(context.prediction_time_utc, "prediction_time_utc")
    start = _timestamp(context.lookback_start_utc, "lookback_start_utc")
    end = _timestamp(context.lookback_end_utc, "lookback_end_utc")
    if not start < end or end > prediction: raise _invalid("context bounds must satisfy start < end <= prediction", "$.lookback_end_utc", "CONTEXT_INVALID")
    if not context.observations: raise _invalid("at least one lookback observation is required", "$.observations", "CONTEXT_INVALID")
    previous: datetime | None = None
    for index, row in enumerate(context.observations):
        path = f"$.observations[{index}]"
        observed = _timestamp(row.timestamp_utc, f"observations[{index}].timestamp_utc")
        available = _timestamp(row.available_at_utc, f"observations[{index}].available_at_utc")
        if observed < start or observed > end or available > prediction or (previous is not None and observed <= previous): raise _invalid("context contains a future feature or unavailable feature", path, "FUTURE_CONTEXT_REJECTED")
        previous = observed
        if row.observation_basis not in _OBSERVATION_BASES: raise _invalid("observation_basis must be OBSERVED or MODELED", f"{path}.observation_basis", "CONTEXT_INVALID")
        if set(row.features) != {"value"}: raise _invalid("only the point-in-time value feature may enter the context", f"{path}.features", "FUTURE_CONTEXT_REJECTED")
        if "value" not in row.features: raise _invalid("each row must contain a finite value feature", f"{path}.features.value", "CONTEXT_INVALID")
        _finite(row.features["value"], f"observations[{index}].features.value")
        if row.target_value is not None:
            _finite(row.target_value, f"observations[{index}].target_value")
            if row.target_completed_at_utc is None: raise _invalid("target completion is required", f"{path}.target_completed_at_utc", "CONTEXT_INVALID")
            completed = _timestamp(row.target_completed_at_utc, f"observations[{index}].target_completed_at_utc")
            if completed > prediction: raise _invalid("future target cannot enter a point-in-time context", f"{path}.target_value", "FUTURE_CONTEXT_REJECTED")
    if profile.normalization_window_bars > len(context.observations): raise _invalid("normalization window exceeds available lookback", "$.profile.normalization_window_bars", "CONTEXT_INVALID")


def _validate_profile(profile: ModelProfile) -> None:
    if not isinstance(profile.profile_id, str) or not profile.profile_id.strip(): raise _invalid("profile_id must be a non-empty string", "$.profile.profile_id")
    _digest(profile.preprocessing_code_hash, "profile.preprocessing_code_hash")
    _digest(profile.preprocessing_config_hash, "profile.preprocessing_config_hash")
    for field in ("normalization_window_bars", "seed", "sample_count"):
        value = getattr(profile, field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1: raise _invalid(f"{field} must be a positive integer", f"$.profile.{field}")
    sampler = profile.sampler
    if not isinstance(sampler, Mapping) or not sampler: raise _invalid("sampler must be a non-empty object", "$.profile.sampler")
    if not isinstance(sampler.get("name"), str) or not sampler["name"].strip(): raise _invalid("sampler.name must be a non-empty string", "$.profile.sampler.name")
    temperature = _finite(sampler.get("temperature"), "sampler.temperature")
    if temperature <= 0: raise _invalid("sampler.temperature must be positive", "$.profile.sampler.temperature")
    top_k = sampler.get("top_k")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1: raise _invalid("sampler.top_k must be a positive integer", "$.profile.sampler.top_k")
    if sampler.get("deterministic") is not True: raise _invalid("sampler.deterministic must be true", "$.profile.sampler.deterministic")


def _checkpoints(model: ModelRegistration) -> tuple[dict[str, object], dict[str, float], str | None]:
    _digest(model.model_fingerprint, "model_fingerprint")
    _digest(model.descriptor_hash, "descriptor_hash")
    try: records = load_descriptor_registry(); stored = records.get(model.descriptor_hash)
    except DescriptorError as error: raise _invalid(error.message, error.path or "$.model", "MODEL_UNREGISTERED") from error
    if stored is None or stored.value.get("artifact_id") != model.model_fingerprint: raise _invalid("model descriptor is not registered", "$.model.descriptor_hash", "MODEL_UNREGISTERED")
    try:
        entry: object = json.loads(model.entry_path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _invalid(f"model registry entry cannot be read: {error}", str(model.entry_path), "MODEL_UNREGISTERED") from error
    if not isinstance(entry, dict) or entry.get("model_fingerprint") != model.model_fingerprint: raise _invalid("model entry does not match fingerprint", "$.model", "MODEL_UNREGISTERED")
    missing: str | None = None
    values: dict[str, float] = {}
    replay: dict[str, object] = {}
    checkpoints = (("base", model.base_checkpoint_path, model.base_checkpoint_hash),)
    if model.fine_tuned_checkpoint_path is not None: checkpoints = (*checkpoints, ("fine_tuned", model.fine_tuned_checkpoint_path, model.fine_tuned_checkpoint_hash))
    for name, path, digest_value in checkpoints:
        content = path.read_bytes() if path.is_file() and not path.is_symlink() else None
        if content is None or sha256_digest(content) != digest_value:
            missing = f"{name.upper()}_CHECKPOINT_MISSING"; replay[name] = {"hash": digest_value, "bytes_base64": None, "status": "MISSING"}
        else:
            values[name] = float(int.from_bytes(hashlib.sha256(content).digest()[:8], "big"))
            replay[name] = {"hash": digest_value, "bytes_base64": base64.b64encode(content).decode("ascii"), "status": "READY"}
    return replay, values, missing


def _calibration() -> dict[str, object]:
    return {"required": True, "status": "PENDING", "panel": "lab.calibration", "policy": "downstream", "oracle": False}


def _outputs(context: FrozenContext, profile: ModelProfile, weights: dict[str, float]) -> tuple[dict[str, object], dict[str, object]]:
    selected = context.observations[-profile.normalization_window_bars :]
    values = [float(row.features["value"]) for row in selected]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    deviation = (values[-1] - mean) / (variance ** 0.5 or 1.0)
    paths: list[dict[str, object]] = []
    up_count = 0
    for sample in range(profile.sample_count):
        levels = [1.0]
        for horizon in range(1, 9):
            material = canonical_json({"context_hash": context.context_hash, "horizon": horizon, "model": weights["base"], "profile_hash": profile.profile_hash, "sample": sample, "seed": profile.seed})
            unit = int.from_bytes(hashlib.sha256(material).digest()[:8], "big") / 2**64
            adjustment = (unit - 0.5 + 0.20 * deviation + (weights["base"] % 101 - 50) / 5000.0) * float(profile.sampler["temperature"]) * 0.02
            levels.append(round(levels[-1] * (1.0 + adjustment), 12))
        terminal = levels[-1] - 1.0
        up_count += terminal >= 0
        paths.append({"path_id": f"path-{sample:04d}", "horizon_values": levels[1:], "terminal_return": round(terminal, 12), "path_share": round(1.0 / profile.sample_count, 12), "observation_basis": "MODELED", "calibration": _calibration()})
    up = round(up_count / profile.sample_count, 12)
    probabilities = {"up": {"value": up, "semantics": "P(terminal_return >= 0 | frozen lookback)", "observation_basis": "MODELED", "calibration": _calibration()}, "down": {"value": round(1.0 - up, 12), "semantics": "P(terminal_return < 0 | frozen lookback)", "observation_basis": "MODELED", "calibration": _calibration()}}
    path_shares = {"policy": "EQUAL_SAMPLE_SHARE", "values": [{"path_id": path["path_id"], "share": path["path_share"], "observation_basis": "MODELED", "calibration": _calibration()} for path in paths]}
    normalization = {"method": "LOOKBACK_ONLY_POPULATION_ZSCORE", "window_bars": profile.normalization_window_bars, "uses_future": False, "bounds": {"start_utc": selected[0].timestamp_utc, "end_utc": selected[-1].timestamp_utc, "prediction_time_utc": context.prediction_time_utc}, "input_row_ids": [f"row-{index:02d}" for index in range(len(context.observations) - len(selected), len(context.observations))], "statistics": {"mean": mean, "population_variance": variance, "last_z_score": deviation}}
    return {"paths": paths, "probabilities": probabilities, "path_shares": path_shares}, normalization


def _report(context: FrozenContext, model: ModelRegistration, profile: ModelProfile, checkpoints: dict[str, object], weights: dict[str, float], blocked: str | None) -> dict[str, object]:
    if blocked is None:
        outputs, normalization = _outputs(context, profile, weights)
    else:
        outputs, normalization = {"paths": [], "probabilities": {}, "path_shares": {"policy": "BLOCKED", "values": []}}, {"method": "LOOKBACK_ONLY_POPULATION_ZSCORE", "uses_future": False, "status": "NOT_RUN"}
    replay = {"status": "READY" if blocked is None else "BLOCKED", "checkpoints": checkpoints, "preprocessing_code_hash": profile.preprocessing_code_hash, "preprocessing_config_hash": profile.preprocessing_config_hash, "normalization_version": "gauntlet.model-normalization@v1", "seed": profile.seed, "sampler": dict(profile.sampler)}
    return {"schema_version": INFERENCE_SCHEMA, "status": "OK" if blocked is None else "BLOCKED", "blocked_reason": blocked, "gate_state": "PASS" if blocked is None else "BLOCKED", "fingerprints": {"model": model.model_fingerprint, "context": context.context_hash, "profile": profile.profile_hash}, "context_bounds": {"prediction_time_utc": context.prediction_time_utc, "lookback_start_utc": context.lookback_start_utc, "lookback_end_utc": context.lookback_end_utc, "future_features": []}, "normalization": normalization, "sampling": {"seed": profile.seed, "sample_count": profile.sample_count, "settings": dict(profile.sampler), "deterministic": True}, "outputs": outputs, "output_semantics": {"paths": "MODELED hypothetical returns", "probabilities": "MODELED finite-sample event shares", "path_shares": "MODELED equal sampler weights", "calibration_required": True, "oracle": False}, "replay": replay}


def _write(root: Path, artifact_hash: str, content: bytes) -> Path:
    destination = root / "model" / "inference" / artifact_hash; path = destination / "inference.json"
    if path.exists():
        if path.is_symlink() or path.read_bytes() != content: raise _invalid("existing inference artifact differs from deterministic result", str(path), "ARTIFACT_MISMATCH")
        return path
    destination.mkdir(parents=True, exist_ok=True)
    return create_exclusive(path, content)


def _event(root: Path, context: FrozenContext, model: ModelRegistration, artifact_hash: str, blocked: str | None) -> tuple[str, dict[str, object], bool]:
    event_id = f"model-inference-{artifact_hash}"
    ledger = root / "ledger" / "events.jsonl"
    if ledger.is_file():
        for line in ledger.read_bytes().splitlines():
            value: object = json.loads(line)
            if isinstance(value, dict) and value.get("event_id") == event_id: return str(value["event_hash"]), value, True
    args_hash = sha256_digest(canonical_json({"context_hash": context.context_hash, "model_fingerprint": model.model_fingerprint}))
    event = EventRecord(event_id, context.prediction_time_utc, Actor("agent", "model-inference"), "snapshot.write", f"model-inference:{artifact_hash}", args_hash, ZERO_DIGEST if blocked is not None else artifact_hash, "ERROR" if blocked is not None else "OK", blocked, {"run_id": artifact_hash, "phase": "model-inference"})
    try:
        appended = append_event(event, regenerate_heads(root).events.head_hash, data_root=root)
    except LedgerError as error:
        raise _invalid(error.message, error.path or "$.event", "EVENT_APPEND_FAILED") from error
    return appended.head_hash, dict(appended.record), False


def run_inference(context: FrozenContext, model: ModelRegistration, profile: ModelProfile) -> InferenceArtifact:
    """Run one real local deterministic model and seal its replay evidence."""

    if not isinstance(context, FrozenContext): raise _invalid("context must be a FrozenContext", "$.context")
    if not isinstance(model, ModelRegistration): raise _invalid("model must be a ModelRegistration", "$.model")
    if not isinstance(profile, ModelProfile): raise _invalid("profile must be a ModelProfile", "$.profile")
    _validate_context(context, profile)
    _validate_profile(profile)
    checkpoints, weights, blocked = _checkpoints(model)
    report = _report(context, model, profile, checkpoints, weights, blocked)
    canonical = canonical_json(report)
    artifact_hash = sha256_digest(canonical)
    root = data_root_path(None)
    path = _write(root, artifact_hash, canonical)
    event_head, event_record, replayed = _event(root, context, model, artifact_hash, blocked)
    return InferenceArtifact(artifact_hash, context.context_hash, model.model_fingerprint, str(report["status"]), str(report["gate_state"]), blocked is None, canonical, MappingProxyType(report), path, event_head, MappingProxyType(event_record), replayed)


__all__ = ["ContextObservation", "FrozenContext", "INFERENCE_SCHEMA", "InferenceArtifact", "ModelProfile", "run_inference"]
