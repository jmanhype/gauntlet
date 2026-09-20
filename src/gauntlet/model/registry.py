"""Immutable Kronos model-lineage registration."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.contracts.manifests import create_exclusive
from gauntlet.data.descriptors import EvidenceDescriptor, descriptor_digest, load_descriptor_registry, register_descriptor
from gauntlet.ledger import Actor, EventRecord, append_event, regenerate_heads, verify_chains
from gauntlet.ledger._common import LedgerError, actor_mapping, data_root_path, validate_digest, validate_timestamp

MODEL_SCHEMA = "gauntlet.model-registry.v1"
_REQUIRED_WINDOWS = frozenset({"start", "end"})


class ModelError(RuntimeError):
    """A machine-readable, fail-closed model-contract rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


@dataclass(frozen=True, slots=True)
class ModelRegistryEntry:
    """Every lineage fact required to identify and replay exact model bytes."""

    model_id: str; model_version: int; architecture: Mapping[str, object]; architecture_config_hash: str
    base_checkpoint_bytes: bytes; training_window: Mapping[str, object]; domain_window: Mapping[str, object]
    license: Mapping[str, object]; provenance: Mapping[str, object]; hardware: Mapping[str, object]; seeds: Mapping[str, object]
    fine_tuned_checkpoint_bytes: bytes | None = None; base_checkpoint_hash: str | None = None
    fine_tuned_checkpoint_hash: str | None = None; registered_at_utc: str | None = None; actor: Actor | None = None


@dataclass(frozen=True, slots=True)
class ModelRegistration:
    """The immutable registry observation and its verified local artifacts."""

    model_fingerprint: str; model_id: str; model_version: int; descriptor_hash: str; descriptor_path: Path; entry_path: Path
    base_checkpoint_hash: str; base_checkpoint_path: Path; fine_tuned_checkpoint_hash: str | None; fine_tuned_checkpoint_path: Path | None
    event_head_hash: str; replayed: bool

    @property
    def entry(self) -> Mapping[str, object]:
        value: object = json.loads(self.entry_path.read_bytes())
        if not isinstance(value, dict): raise ModelError("REGISTRY_UNVERIFIED", "model entry is not canonical JSON", str(self.entry_path))
        return value


def _invalid(message: str, path: str, code: str = "REGISTRY_INVALID") -> ModelError:
    return ModelError(code, message, path)


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise _invalid(f"{field} must be a non-empty string", f"$.{field}")
    return value


def _digest(value: object, field: str) -> str:
    try:
        validate_digest(value, f"$.{field}")
    except LedgerError as error:
        raise _invalid(f"{field} must be sha256:<64 lowercase hexadecimal>", f"$.{field}") from error
    assert isinstance(value, str)
    return value


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not value: raise _invalid(f"{field} must be a non-empty object", f"$.{field}")
    return value


def _window(value: object, field: str) -> Mapping[str, object]:
    window = _mapping(value, field)
    missing = sorted(_REQUIRED_WINDOWS - set(window))
    if missing: raise _invalid(f"{field} is missing {missing}", f"$.{field}")
    for bound in ("start", "end"):
        if not isinstance(window[bound], str) or not window[bound].strip(): raise _invalid(f"{field}.{bound} must be a non-empty ISO-8601 value", f"$.{field}.{bound}")
    if str(window["start"]) >= str(window["end"]): raise _invalid(f"{field}.end must follow start", f"$.{field}.end")
    return window


def _checkpoint(value: object, expected: str | None, field: str) -> tuple[bytes, str]:
    if not isinstance(value, bytes) or not value: raise _invalid(f"{field} bytes are required", f"$.{field}")
    actual = sha256_digest(value)
    if expected is not None and _digest(expected, f"{field}_hash") != actual: raise _invalid(f"{field}_hash does not match exact bytes", f"$.{field}_hash")
    return value, actual


def _seeds(value: object) -> Mapping[str, object]:
    seeds = _mapping(value, "seeds")
    for name, seed in seeds.items():
        if not isinstance(name, str) or not name.strip():
            raise _invalid("seed names must be non-empty strings", "$.seeds")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise _invalid(f"seed {name!r} must be a non-negative integer", f"$.seeds.{name}")
    return seeds


def _fingerprint(entry: ModelRegistryEntry, base_hash: str, fine_hash: str | None) -> str:
    value = {"architecture": dict(entry.architecture), "architecture_config_hash": entry.architecture_config_hash, "base_checkpoint_hash": base_hash, "domain_window": dict(entry.domain_window), "fine_tuned_checkpoint_hash": fine_hash, "hardware": dict(entry.hardware), "license": dict(entry.license), "model_id": entry.model_id, "model_version": entry.model_version, "provenance": dict(entry.provenance), "seeds": dict(entry.seeds), "training_window": dict(entry.training_window)}
    return sha256_digest(canonical_json(value))


def entry_mapping(entry: ModelRegistryEntry, fingerprint: str, base_hash: str, fine_hash: str | None, registered_at: str) -> dict[str, object]:
    """Serialize the exact registry payload without mutable checkpoint paths."""

    checkpoints = {"base": {"hash": base_hash, "byte_length": len(entry.base_checkpoint_bytes), "path": f"model/checkpoints/{base_hash}.bin"}, **({"fine_tuned": {"hash": fine_hash, "byte_length": len(entry.fine_tuned_checkpoint_bytes or b""), "path": f"model/checkpoints/{fine_hash}.bin"}} if fine_hash is not None else {})}
    return {"schema_version": MODEL_SCHEMA, "model_id": entry.model_id, "model_version": entry.model_version, "model_fingerprint": fingerprint, "architecture": dict(entry.architecture), "architecture_config_hash": entry.architecture_config_hash, "checkpoints": checkpoints, "training_window": dict(entry.training_window), "domain_window": dict(entry.domain_window), "license": dict(entry.license), "provenance": dict(entry.provenance), "hardware": dict(entry.hardware), "seeds": dict(entry.seeds), "registered_at_utc": registered_at}


def validate_model_entry(entry: ModelRegistryEntry) -> tuple[str, str, str | None, str]:
    """Validate lineage and return fingerprint, checkpoint hashes, and timestamp."""

    _nonempty_string(entry.model_id, "model_id")
    if isinstance(entry.model_version, bool) or not isinstance(entry.model_version, int) or entry.model_version < 1: raise _invalid("model_version must be a positive integer", "$.model_version")
    architecture = _mapping(entry.architecture, "architecture")
    _nonempty_string(architecture.get("name"), "architecture.name")
    config_hash = _digest(entry.architecture_config_hash, "architecture_config_hash")
    if config_hash != sha256_digest(canonical_json(dict(architecture))): raise _invalid("architecture_config_hash does not match architecture", "$.architecture_config_hash")
    _, base_hash = _checkpoint(entry.base_checkpoint_bytes, entry.base_checkpoint_hash, "base_checkpoint_bytes")
    fine_hash: str | None = None
    if entry.fine_tuned_checkpoint_bytes is not None or entry.fine_tuned_checkpoint_hash is not None:
        _, fine_hash = _checkpoint(entry.fine_tuned_checkpoint_bytes, entry.fine_tuned_checkpoint_hash, "fine_tuned_checkpoint_bytes")
    _window(entry.training_window, "training_window")
    _window(entry.domain_window, "domain_window")
    _mapping(entry.license, "license")
    _mapping(entry.provenance, "provenance")
    _mapping(entry.hardware, "hardware")
    _seeds(entry.seeds)
    if entry.actor is not None:
        actor_mapping(entry.actor)
    if entry.registered_at_utc is None:
        registered_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    else:
        registered_at = _nonempty_string(entry.registered_at_utc, "registered_at_utc")
        try:
            validate_timestamp(registered_at, "$.registered_at_utc")
        except LedgerError as error:
            raise _invalid("registered_at_utc must be UTC ISO-8601", "$.registered_at_utc") from error
    fingerprint = _fingerprint(entry, base_hash, fine_hash)
    return fingerprint, base_hash, fine_hash, registered_at


def _store_checkpoint(root: Path, digest: str, content: bytes) -> tuple[Path, bool]:
    path = root / "model" / "checkpoints" / f"{digest}.bin"
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
            raise _invalid("existing checkpoint bytes do not match their hash", str(path), "CHECKPOINT_HASH_MISMATCH")
        return path, False
    return create_exclusive(path, content), True


def _descriptor(entry: ModelRegistryEntry, payload: dict[str, object], fingerprint: str, registered_at: str) -> EvidenceDescriptor:
    content = canonical_json(payload)
    descriptor = EvidenceDescriptor(
        descriptor_schema="gauntlet.evidence.v1", artifact_id=fingerprint, descriptor_id=f"model-{entry.model_id}-{fingerprint[7:19]}",
        descriptor_version=1, descriptor_hash="sha256:" + "0" * 64, supersedes_descriptor_hash=None, effective_at_utc=registered_at,
        superseded_at_utc=None, kind="model", venue_track="external", content_hash=sha256_digest(content),
        source={"collector": "model-registry", "uri_or_lineage": str(entry.provenance.get("lineage", fingerprint))},
        observation_basis="OBSERVED",
        coverage={"training": dict(entry.training_window), "domain": dict(entry.domain_window)},
        freshness={"watermark_at": registered_at, "max_age": "P36500D"},
        quality={"state": "VALID", "checks": [{"name": "lineage-complete", "status": "PASS"}]},
        dependencies=(), criticality="GATE_CRITICAL", downstream_metrics=("model.replay", "model.calibration"),
        content_bytes=content, actor=entry.actor or Actor("collector", "model-registry"),
    )
    return replace(descriptor, descriptor_hash=descriptor_digest(descriptor))


def _event(root: Path, entry: ModelRegistryEntry, fingerprint: str, descriptor_hash: str, registered_at: str) -> tuple[str, bool]:
    event_id = f"model-register-{fingerprint}"
    ledger = root / "ledger" / "events.jsonl"
    if ledger.is_file():
        for line in ledger.read_bytes().splitlines():
            value: object = json.loads(line)
            if isinstance(value, dict) and value.get("event_id") == event_id:
                return str(value["event_hash"]), True
    event = EventRecord(event_id, registered_at, entry.actor or Actor("collector", "model-registry"), "snapshot.write", f"model:{fingerprint}", descriptor_hash, descriptor_hash, "OK", None, {"run_id": fingerprint, "kind": "model-registration"})
    try:
        appended = append_event(event, regenerate_heads(root).events.head_hash, data_root=root)
    except LedgerError as error:
        raise _invalid(error.message, error.path or "$.event", "EVENT_APPEND_FAILED") from error
    return appended.head_hash, False


def _registration_from_descriptor(root: Path, entry: ModelRegistryEntry, fingerprint: str, base_hash: str, fine_hash: str | None, payload: dict[str, object], descriptor_hash: str, event_head: str, replayed: bool) -> ModelRegistration:
    checkpoints = payload["checkpoints"]
    assert isinstance(checkpoints, dict)
    base = checkpoints["base"]
    assert isinstance(base, dict)
    base_path = root / str(base["path"])
    fine_path = None
    if fine_hash is not None:
        fine = checkpoints["fine_tuned"]
        assert isinstance(fine, dict)
        fine_path = root / str(fine["path"])
    return ModelRegistration(fingerprint, entry.model_id, entry.model_version, descriptor_hash, root / "descriptors" / f"{descriptor_hash}.json", root / "artifacts" / f"{sha256_digest(canonical_json(payload))}.bin", base_hash, base_path, fine_hash, fine_path, event_head, replayed)


def register_model(entry: ModelRegistryEntry) -> ModelRegistration:
    """Register one immutable model-lineage observation without replacing duplicates."""

    fingerprint, base_hash, fine_hash, registered_at = validate_model_entry(entry)
    root = data_root_path(None)
    payload = entry_mapping(entry, fingerprint, base_hash, fine_hash, registered_at)
    descriptor = _descriptor(entry, payload, fingerprint, registered_at)
    records = load_descriptor_registry(root)
    existing = records.get(descriptor.descriptor_hash)
    if existing is not None:
        event_head, replayed = _event(root, entry, fingerprint, descriptor.descriptor_hash, registered_at)
        return _registration_from_descriptor(root, entry, fingerprint, base_hash, fine_hash, payload, descriptor.descriptor_hash, event_head, replayed)

    base_path, created_base = _store_checkpoint(root, base_hash, entry.base_checkpoint_bytes)
    fine_path = None
    created_fine = False
    if fine_hash is not None:
        fine_path, created_fine = _store_checkpoint(root, fine_hash, entry.fine_tuned_checkpoint_bytes or b"")
    try:
        registration = register_descriptor(descriptor)  # type: ignore[arg-type]
        event_head, replayed = _event(root, entry, fingerprint, registration.descriptor_hash, registered_at)
    except BaseException:
        if created_base and base_path.exists():
            base_path.unlink()
        if created_fine and fine_path is not None and fine_path.exists():
            fine_path.unlink()
        raise
    if not verify_chains(root).valid: raise _invalid("ledger verification failed after registration", "$", "REGISTRY_UNVERIFIED")
    return _registration_from_descriptor(root, entry, fingerprint, base_hash, fine_hash, payload, registration.descriptor_hash, event_head, replayed)


__all__ = ["ModelError", "ModelRegistration", "ModelRegistryEntry", "MODEL_SCHEMA", "entry_mapping", "register_model", "validate_model_entry"]
