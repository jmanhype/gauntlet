"""Fail-closed validation for Phase 1 contract envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class ValidationError:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[ValidationError, ...]


DESCRIPTOR = "gauntlet.evidence.v1"
TRIAL = "gauntlet.trial.v1"
EVENT = "gauntlet.event.v1"
POLICY = "gauntlet.policy.v1"
MANIFEST = "gauntlet.manifest.v1"
SCHEMA_IDS = frozenset((DESCRIPTOR, TRIAL, EVENT, POLICY, MANIFEST))

_venues = frozenset(("solana_dex", "hyperliquid", "external", "cross_venue_transfer"))
_actors = frozenset(("human", "agent", "collector"))
_schemas: Mapping[str, Mapping[str, frozenset[str]]] = {
    DESCRIPTOR: {"descriptor_schema": frozenset((DESCRIPTOR,)), "kind": frozenset(("bars", "events", "reserves", "forecasts", "trades", "panel", "claim", "config", "model")), "venue_track": _venues, "observation_basis": frozenset(("OBSERVED", "MODELED")), "criticality": frozenset(("GATE_CRITICAL", "NON_CRITICAL", "UNKNOWN"))},
    TRIAL: {"schema_version": frozenset(("1",)), "entry_type": frozenset(("trial.registered", "trial.result", "trial.rejected", "trial.promoted", "family.stopped", "owner.exception")), "venue_track": _venues},
    EVENT: {"schema_version": frozenset(("1",)), "verb": frozenset(("trial.register", "dependency.evaluate", "gate.evaluate", "snapshot.write", "owner.decision", "evidence.project", "audit.export", "events.anchor")), "status": frozenset(("OK", "ERROR"))},
    POLICY: {"schema_version": frozenset(("1",)), "manifest_type": frozenset(("policy",)), "policy_type": frozenset(("evidence-policy", "gate-rules", "disposition-policy", "transitions", "effective-evidence", "alert-policy", "risk-policy")), "status": frozenset(("active", "superseded"))},
    MANIFEST: {"schema_version": frozenset(("1",)), "manifest_type": frozenset(("artifact-manifest",))},
}
_fields: Mapping[str, Mapping[str, tuple[str, ...]]] = {
    DESCRIPTOR: {"required": ("descriptor_schema", "artifact_id", "descriptor_id", "descriptor_version", "descriptor_hash", "effective_at_utc", "kind", "venue_track", "content_hash", "source", "observation_basis", "coverage", "freshness", "quality", "dependencies", "criticality", "downstream_metrics"), "strings": ("artifact_id", "descriptor_id", "effective_at_utc"), "digests": ("descriptor_hash", "content_hash"), "objects": ("source", "coverage", "freshness", "quality"), "arrays": ("dependencies", "downstream_metrics"), "positive_integers": ("descriptor_version",)},
    TRIAL: {"required": ("schema_version", "entry_type", "trial_id", "family_id", "venue_track", "recorded_at_utc", "actor", "payload_hash", "previous_head_hash", "entry_hash", "payload"), "strings": ("trial_id", "family_id", "recorded_at_utc"), "digests": ("payload_hash", "previous_head_hash", "entry_hash"), "objects": ("actor", "payload"), "arrays": (), "positive_integers": ()},
    EVENT: {"required": ("event_id", "schema_version", "timestamp_utc", "actor", "verb", "subject", "args_hash", "output_hash", "payload_hash", "previous_head_hash", "event_hash", "status", "trace"), "strings": ("event_id", "timestamp_utc", "subject"), "digests": ("args_hash", "output_hash", "payload_hash", "previous_head_hash", "event_hash"), "objects": ("actor", "trace"), "arrays": (), "positive_integers": ()},
    POLICY: {"required": ("schema_version", "manifest_type", "policy_type", "policy_id", "version", "creator", "created_at_utc", "changelog", "status", "rules", "content_hash"), "strings": ("policy_id", "creator", "created_at_utc"), "digests": ("content_hash",), "objects": ("rules",), "arrays": ("changelog",), "positive_integers": ("version",)},
    MANIFEST: {"required": ("schema_version", "manifest_type", "artifact_id", "created_at_utc", "files", "external_artifacts", "merkle_root"), "strings": ("artifact_id", "created_at_utc"), "digests": ("merkle_root",), "objects": (), "arrays": ("files", "external_artifacts"), "positive_integers": ()},
}


def _error(path: str, message: str, code: str = "TYPE_INVALID") -> ValidationError:
    return ValidationError(code, path, message)


def _digest(value: object, path: str, errors: list[ValidationError]) -> None:
    hexadecimal = value[7:] if isinstance(value, str) else b""
    valid = isinstance(value, str) and value.startswith("sha256:") and len(hexadecimal) == 64
    if not valid or any(char not in "0123456789abcdef" for char in hexadecimal):
        errors.append(_error(path, "must be sha256:<64 lowercase hexadecimal>", "DIGEST_INVALID"))


def _validate_fields(value: object, schema_id: str) -> tuple[ValidationError, ...]:
    errors: list[ValidationError] = []
    if not isinstance(value, dict):
        return (_error("$", "must be an object"),)
    spec = _fields[schema_id]
    checks = {"strings": lambda item: isinstance(item, str), "objects": lambda item: isinstance(item, dict), "arrays": lambda item: isinstance(item, list), "positive_integers": lambda item: not isinstance(item, bool) and isinstance(item, int) and item >= 1}
    names = {"strings": "string", "objects": "object", "arrays": "array", "positive_integers": "positive integer"}
    for kind, check in checks.items():
        for key in spec[kind]:
            if not check(value.get(key)):
                errors.append(_error(f"$.{key}", f"must be a {names[kind]}"))
    for key in spec["digests"]:
        _digest(value.get(key), f"$.{key}", errors)
    for key in spec["required"]:
        if key not in value:
            errors.append(_error(f"$.{key}", "is required", "FIELD_REQUIRED"))
    for key, allowed in _schemas[schema_id].items():
        item = value.get(key)
        if not isinstance(item, str):
            errors.append(_error(f"$.{key}", "must be a string"))
        elif item not in allowed:
            errors.append(_error(f"$.{key}", f"must be one of {sorted(allowed)}", "UNKNOWN_DISCRIMINATOR"))
    return tuple(errors)


def _artifact_entries(value: object, path: str) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if not isinstance(value, list):
        return [_error(path, "must be an array")]
    for index, entry in enumerate(value):
        entry_path = f"{path}[{index}]"
        if not isinstance(entry, dict):
            errors.append(_error(entry_path, "must be an object"))
            continue
        for key in ("path", "hash"):
            if key not in entry:
                errors.append(_error(f"{entry_path}.{key}", "is required", "FIELD_REQUIRED"))
        _digest(entry.get("hash"), f"{entry_path}.hash", errors)
        relative = entry.get("path")
        invalid = not isinstance(relative, str) or relative.startswith("/") or "\\" in relative
        invalid = invalid or (isinstance(relative, str) and any(part in ("", ".", "..") for part in relative.split("/")))
        if invalid:
            errors.append(_error(f"{entry_path}.path", "must be storage-relative POSIX path", "PATH_INVALID"))
    return errors


def validate(instance: object, schema_id: str) -> ValidationResult:
    """Validate a registered Phase 1 envelope and reject unknown schemas."""

    if schema_id not in SCHEMA_IDS:
        return ValidationResult(False, (_error("$", f"schema {schema_id!r} is not registered", "UNKNOWN_SCHEMA"),))
    errors = list(_validate_fields(instance, schema_id))
    if schema_id == MANIFEST and isinstance(instance, dict):
        errors.extend(_artifact_entries(instance.get("files"), "$.files"))
        errors.extend(_artifact_entries(instance.get("external_artifacts"), "$.external_artifacts"))
    if schema_id in (TRIAL, EVENT) and isinstance(instance, dict):
        actor = instance.get("actor")
        if not isinstance(actor, dict):
            errors.append(_error("$.actor", "must be an object"))
        elif not isinstance(actor.get("kind"), str) or actor["kind"] not in _actors:
            errors.append(_error("$.actor.kind", f"must be one of {sorted(_actors)}", "UNKNOWN_DISCRIMINATOR"))
    return ValidationResult(not errors, tuple(errors))
