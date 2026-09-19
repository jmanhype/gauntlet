"""Immutable evidence descriptor registration and storage."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.contracts.manifests import create_exclusive
from gauntlet.contracts.schemas import DESCRIPTOR, validate
from gauntlet.ledger import Actor, TrialPayload, append_trial, regenerate_heads, verify_chains
from gauntlet.ledger._common import LedgerError, ZERO_DIGEST, actor_mapping, data_root_path, validate_digest, validate_timestamp


DESCRIPTOR_FIELDS = ("descriptor_schema", "artifact_id", "descriptor_id", "descriptor_version", "descriptor_hash", "supersedes_descriptor_hash", "effective_at_utc", "superseded_at_utc", "kind", "venue_track", "content_hash", "source", "observation_basis", "coverage", "freshness", "quality", "dependencies", "criticality", "downstream_metrics")
_QUALITY_STATES = frozenset(("VALID", "STALE", "CORRUPT", "INCOMPLETE", "QUARANTINED"))
_RELATIONS = frozenset(("requires",))
_DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:([0-9]+(?:\.[0-9]+)?)S)?)?$")


@dataclass(frozen=True)
class EvidenceDescriptor:
    """A complete descriptor envelope plus the bytes it commits to."""

    descriptor_schema: str; artifact_id: str; descriptor_id: str; descriptor_version: int; descriptor_hash: str
    supersedes_descriptor_hash: str | None; effective_at_utc: str; superseded_at_utc: str | None; kind: str; venue_track: str
    content_hash: str; source: Mapping[str, object]; observation_basis: str; coverage: Mapping[str, object]
    freshness: Mapping[str, object]; quality: Mapping[str, object]; dependencies: tuple[Mapping[str, object], ...]
    criticality: str; downstream_metrics: tuple[str, ...]
    content_bytes: bytes = b""
    actor: Actor | None = None


@dataclass(frozen=True)
class DescriptorRegistration:
    """Physical and ledger evidence produced by one immutable registration."""

    descriptor_hash: str; artifact_id: str; descriptor_id: str; descriptor_version: int; descriptor_path: Path
    content_path: Path; ledger_path: Path; head_path: Path; trial_id: str; recorded_at_utc: str; trial_head_hash: str


@dataclass(frozen=True)
class StoredDescriptor:
    """A verified descriptor and the dependency hashes bound at registration."""

    value: Mapping[str, object]; resolved_dependencies: tuple[Mapping[str, object], ...]
    descriptor_path: Path; content_path: Path; trial_id: str; recorded_at_utc: str


class DescriptorError(RuntimeError):
    """A machine-readable, fail-closed descriptor rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message); self.code = code; self.message = message; self.path = path


def descriptor_mapping(descriptor: EvidenceDescriptor) -> dict[str, object]:
    """Serialize the exact ``gauntlet.evidence.v1`` field set."""

    value = {field: getattr(descriptor, field) for field in DESCRIPTOR_FIELDS}
    return value | {"source": dict(descriptor.source), "coverage": dict(descriptor.coverage), "freshness": dict(descriptor.freshness), "quality": dict(descriptor.quality), "dependencies": [dict(dependency) for dependency in descriptor.dependencies], "downstream_metrics": list(descriptor.downstream_metrics)}


def descriptor_digest(descriptor: EvidenceDescriptor | Mapping[str, object]) -> str:
    """Return the sealed canonical hash of a descriptor envelope."""

    value = descriptor_mapping(descriptor) if isinstance(descriptor, EvidenceDescriptor) else descriptor
    unsealed = {key: item for key, item in value.items() if key != "descriptor_hash"}
    return sha256_digest(canonical_json(unsealed))


def _nonempty_string(value: object, field: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reject(condition: bool, code: str, message: str, path: str) -> None:
    if condition: raise DescriptorError(code, message, path)


def _duration_seconds(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    match = _DURATION.fullmatch(value)
    if match is None or not any(group is not None for group in match.groups()): return None
    days, hours, minutes, seconds = (float(group or 0) for group in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _dependency_error(value: Mapping[str, object]) -> DescriptorError | None:
    dependencies = value["dependencies"]
    assert isinstance(dependencies, list)
    for index, item in enumerate(dependencies):
        path = f"$.dependencies[{index}]"
        if not isinstance(item, dict):
            return DescriptorError("DEPENDENCY_INVALID", "dependency must be an object", path)
        allowed = {"artifact_id", "relation", "descriptor_hash", "descriptor_id"}
        if set(item) - allowed: return DescriptorError("DEPENDENCY_INVALID", "dependency contains unknown fields", path)
        if not _nonempty_string(item.get("artifact_id"), "artifact_id"): return DescriptorError("DEPENDENCY_INVALID", "artifact_id must be a non-empty string", f"{path}.artifact_id")
        if item.get("relation") not in _RELATIONS: return DescriptorError("DEPENDENCY_INVALID", "relation must be 'requires'", f"{path}.relation")
        if "descriptor_hash" in item:
            try: validate_digest(item["descriptor_hash"], f"{path}.descriptor_hash")
            except LedgerError as error: return DescriptorError(error.code, error.message, error.path or path)
        if "descriptor_id" in item and not _nonempty_string(item.get("descriptor_id"), "descriptor_id"): return DescriptorError("DEPENDENCY_INVALID", "descriptor_id must be a non-empty string", f"{path}.descriptor_id")
    return None


def validate_descriptor(value: Mapping[str, object], content_bytes: bytes | None = None) -> None:
    """Apply the complete descriptor contract before any state is written."""

    if set(value) != set(DESCRIPTOR_FIELDS):
        missing = sorted(set(DESCRIPTOR_FIELDS) - set(value)); extra = sorted(set(value) - set(DESCRIPTOR_FIELDS))
        _reject(True, "DESCRIPTOR_FIELDS_INVALID", f"missing fields: {missing}" if missing else f"unknown fields: {extra}", "$")
    result = validate(value, DESCRIPTOR)
    if not result.valid:
        first = result.errors[0]
        raise DescriptorError("SCHEMA_INVALID", first.message, first.path)
    for field in ("artifact_id", "descriptor_id", "effective_at_utc"):
        _reject(not _nonempty_string(value[field], field), "DESCRIPTOR_INVALID", f"{field} must be a non-empty string", f"${field}")
    validate_timestamp(value["effective_at_utc"], "$.effective_at_utc")
    _reject(value["superseded_at_utc"] is not None, "DESCRIPTOR_INVALID", "new descriptor versions cannot declare superseded_at_utc", "$.superseded_at_utc")
    if value["supersedes_descriptor_hash"] is not None:
        validate_digest(value["supersedes_descriptor_hash"], "$.supersedes_descriptor_hash")
    source = value["source"]; assert isinstance(source, dict)
    _reject(not _nonempty_string(source.get("collector"), "collector") or not _nonempty_string(source.get("uri_or_lineage"), "uri_or_lineage"), "PROVENANCE_INVALID", "source collector and uri_or_lineage are required", "$.source")
    quality = value["quality"]; assert isinstance(quality, dict)
    _reject(quality.get("state") not in _QUALITY_STATES, "QUALITY_INVALID", f"state must be one of {sorted(_QUALITY_STATES)}", "$.quality.state")
    freshness = value["freshness"]; assert isinstance(freshness, dict)
    _reject(not _nonempty_string(freshness.get("watermark_at"), "watermark_at") or not _nonempty_string(freshness.get("max_age"), "max_age"), "FRESHNESS_INVALID", "watermark_at and max_age are required", "$.freshness")
    validate_timestamp(freshness["watermark_at"], "$.freshness.watermark_at")
    _reject(_duration_seconds(freshness.get("max_age")) is None, "FRESHNESS_INVALID", "max_age must be a positive ISO-8601 duration", "$.freshness.max_age")
    checks = quality.get("checks", [])
    _reject(not isinstance(checks, list) or any(not isinstance(check, dict) or not _nonempty_string(check.get("name"), "name") or check.get("status") not in ("PASS", "FAIL") for check in checks), "QUALITY_INVALID", "checks must be objects with name and PASS/FAIL status", "$.quality.checks")
    metrics = value["downstream_metrics"]; assert isinstance(metrics, list)
    _reject(any(not isinstance(metric, str) or not metric.strip() for metric in metrics) or len(set(metrics)) != len(metrics), "DESCRIPTOR_INVALID", "downstream_metrics must be unique non-empty strings", "$.downstream_metrics")
    error = _dependency_error(value)
    if error is not None: raise error
    expected = descriptor_digest(value)
    if value["descriptor_hash"] != expected:
        raise DescriptorError("DESCRIPTOR_HASH_MISMATCH", f"expected {expected}, got {value['descriptor_hash']}", "$.descriptor_hash")
    if content_bytes is not None and sha256_digest(content_bytes) != value["content_hash"]:
        raise DescriptorError("CONTENT_HASH_MISMATCH", "content bytes do not match content_hash", "$.content_hash")


def _trial_payload(envelope: Mapping[str, object], resolved: tuple[Mapping[str, object], ...], recorded_at_utc: str, parameters: Mapping[str, object]) -> TrialPayload:
    return TrialPayload(
        trial_id=f"descriptor-{envelope['descriptor_hash']}", family_id=str(envelope["artifact_id"]), venue_track=str(envelope["venue_track"]), recorded_at_utc=recorded_at_utc,
        hypothesis="Register immutable evidence descriptor", success_interpretation="Descriptor bytes, content, dependencies, and ledger entry agree", failure_interpretation="Descriptor registration is rejected without ledger mutation",
        strategy_family="evidence-integrity", parent_trial_ids=(), transfer_hypothesis=None, data_window=dict(envelope["coverage"]), split_manifest_hash=ZERO_DIGEST,
        source_descriptor_hashes=(str(envelope["descriptor_hash"]),), frozen=True, feature_manifest_hash=ZERO_DIGEST, preprocessing_hash=ZERO_DIGEST, parameters=dict(parameters),
        search_space={}, execution_assumptions={}, adverse_scenarios=(), benchmark_identity="descriptor-registration", benchmark_role="integrity-record",
        budgets={"descriptor_registrations": 1}, stop_condition={"condition": "validation-or-ledger-failure"}, axis_control={"mode": "none"}, policy_versions={"descriptor_schema": "1"},
        resolved_config_hash=ZERO_DIGEST, dependencies=tuple(resolved), criticality=str(envelope["criticality"]),
    )


def _verify_stored(value: Mapping[str, object], path: Path, content_path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise DescriptorError("DESCRIPTOR_UNVERIFIED", "descriptor is missing or not a regular file", str(path))
    if path.read_bytes() != canonical_json(value):
        raise DescriptorError("GRAPH_MALFORMED", "stored descriptor does not match its ledgered canonical envelope", str(path))
    if not content_path.is_file() or content_path.is_symlink():
        raise DescriptorError("CONTENT_MISSING", "committed content is missing or not a regular file", str(content_path))
    if sha256_digest(content_path.read_bytes()) != value["content_hash"]:
        raise DescriptorError("CONTENT_HASH_MISMATCH", "committed content no longer matches content_hash", str(content_path))


def load_descriptor_registry(data_root: Path | None = None) -> dict[str, StoredDescriptor]:
    """Rebuild the descriptor index from verified immutable storage and ledger entries."""

    root = data_root_path(data_root); verification = verify_chains(root)
    if not verification.valid or verification.failure is not None:
        failure = verification.failure
        raise DescriptorError("LEDGER_INVALID", failure.message if failure else "ledger verification failed", failure.path if failure else "$")
    ledger = root / "ledger" / "trials.jsonl"
    if not ledger.exists():
        empty: dict[str, StoredDescriptor] = {}
        return empty
    records: dict[str, StoredDescriptor] = {}
    try:
        for line in ledger.read_bytes().splitlines():
            record: object = json.loads(line)
            if not isinstance(record, dict):
                raise DescriptorError("LEDGER_INVALID", "trial record is not an object")
            payload = record.get("payload")
            if not isinstance(payload, dict) or not isinstance(payload.get("parameters"), dict):
                continue
            candidate = payload["parameters"].get("descriptor")
            if candidate is None: continue
            _reject(not isinstance(candidate, dict), "GRAPH_MALFORMED", "ledgered descriptor is not an object", "$")
            try: validate_descriptor(candidate)
            except DescriptorError as error: raise DescriptorError("GRAPH_MALFORMED", f"ledgered descriptor is invalid: {error.message}", error.path) from error
            resolved = payload["parameters"].get("resolved_dependencies", [])
            _reject(not isinstance(resolved, list) or any(not isinstance(item, dict) for item in resolved), "GRAPH_MALFORMED", "resolved dependency projection is malformed", "$")
            digest = str(candidate["descriptor_hash"]); _reject(digest in records, "GRAPH_MALFORMED", "descriptor hash occurs more than once", "$")
            descriptor_path = root / "descriptors" / f"{digest}.json"; content_path = root / "artifacts" / f"{candidate['content_hash']}.bin"
            try: _verify_stored(candidate, descriptor_path, content_path)
            except DescriptorError as error: raise DescriptorError(error.code, error.message, error.path) from error
            records[digest] = StoredDescriptor(candidate, tuple(resolved), descriptor_path, content_path, str(record["trial_id"]), str(record["recorded_at_utc"]))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DescriptorError("LEDGER_READ_FAILED", str(error), str(ledger)) from error
    return records


def _parse_timestamp(value: object) -> datetime:
    _reject(not isinstance(value, str) or not value.endswith("Z"), "TIMESTAMP_INVALID", "timestamp must end with Z", "$")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise DescriptorError("TIMESTAMP_INVALID", "timestamp is not valid ISO-8601") from error
    return parsed


def _active_for_artifact(records: dict[str, StoredDescriptor], artifact_id: str, as_of: datetime) -> StoredDescriptor | None:
    versions = [stored for stored in records.values() if stored.value.get("artifact_id") == artifact_id]
    eligible = [(effective, stored) for stored in versions if (effective := _parse_timestamp(stored.value["effective_at_utc"])) <= as_of]
    active = {stored.value["descriptor_hash"] for _, stored in eligible}
    selected = [stored for _, stored in eligible if stored.value.get("supersedes_descriptor_hash") not in active]
    return max(selected, key=lambda item: _parse_timestamp(item.value["effective_at_utc"])) if selected else None


def _resolve_dependencies(records: dict[str, StoredDescriptor], envelope: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    effective = _parse_timestamp(envelope["effective_at_utc"])
    resolved: list[Mapping[str, object]] = []
    dependencies = envelope["dependencies"]
    assert isinstance(dependencies, list)
    for dependency in dependencies:
        assert isinstance(dependency, dict)
        exact_hash = dependency.get("descriptor_hash"); target: StoredDescriptor | None = records.get(exact_hash) if isinstance(exact_hash, str) else None
        if target is None:
            target = _active_for_artifact(records, str(dependency["artifact_id"]), effective)
        if target is None or target.value.get("artifact_id") != dependency["artifact_id"]:
            raise DescriptorError("DEPENDENCY_UNREGISTERED", f"dependency {dependency['artifact_id']!r} is not registered at effective time", "$.dependencies")
        if "descriptor_id" in dependency and target.value.get("descriptor_id") != dependency["descriptor_id"]:
            raise DescriptorError("DEPENDENCY_CONFLICT", "dependency descriptor_id does not match artifact", "$.dependencies")
        resolved.append({**dependency, "descriptor_hash": target.value["descriptor_hash"], "descriptor_id": target.value["descriptor_id"]})
    return tuple(resolved)


def _register(descriptor: EvidenceDescriptor, actor: Actor | None, extra_parameters: Mapping[str, object]) -> DescriptorRegistration:
    validate_descriptor(descriptor_mapping(descriptor), descriptor.content_bytes)
    records = load_descriptor_registry()
    digest = descriptor.descriptor_hash
    if digest in records:
        raise DescriptorError("DESCRIPTOR_EXISTS", "immutable descriptor hash is already registered", "$.descriptor_hash")
    versions = [stored for stored in records.values() if stored.value.get("descriptor_id") == descriptor.descriptor_id]
    if versions:
        latest = max(versions, key=lambda item: int(item.value["descriptor_version"]))  # type: ignore[arg-type]
        _reject(latest.value.get("artifact_id") != descriptor.artifact_id, "DESCRIPTOR_ID_CONFLICT", "descriptor_id cannot move between artifacts", "$.descriptor_id")
        _reject(descriptor.descriptor_version != int(latest.value["descriptor_version"]) + 1, "DESCRIPTOR_VERSION_INVALID", "descriptor_version must increment by one", "$.descriptor_version")  # type: ignore[arg-type]
        _reject(descriptor.supersedes_descriptor_hash != latest.value["descriptor_hash"], "SUPERCEDES_INVALID", "new version must supersede the current descriptor hash", "$.supersedes_descriptor_hash")
        _reject(_parse_timestamp(descriptor.effective_at_utc) <= _parse_timestamp(latest.value["effective_at_utc"]), "EFFECTIVE_TIME_INVALID", "descriptor effective time must move forward", "$.effective_at_utc")
    elif descriptor.descriptor_version != 1 or descriptor.supersedes_descriptor_hash is not None:
        raise DescriptorError("DESCRIPTOR_VERSION_INVALID", "initial descriptor must be version 1 without a predecessor", "$.descriptor_version")
    _reject(any(dependency.get("artifact_id") == descriptor.artifact_id for dependency in descriptor.dependencies), "GRAPH_MALFORMED", "descriptor cannot depend on itself", "$.dependencies")

    root = data_root_path(None); envelope = descriptor_mapping(descriptor); resolved = _resolve_dependencies(records, envelope)
    descriptor_path = root / "descriptors" / f"{digest}.json"; content_path = root / "artifacts" / f"{descriptor.content_hash}.bin"
    created_descriptor = created_content = False
    try:
        if not descriptor_path.exists(): create_exclusive(descriptor_path, canonical_json(envelope)); created_descriptor = True
        if not content_path.exists(): create_exclusive(content_path, descriptor.content_bytes); created_content = True
        recorded_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        parameters = {"descriptor": envelope, "resolved_dependencies": [dict(item) for item in resolved], **dict(extra_parameters)}
        payload = _trial_payload(envelope, resolved, recorded_at, parameters)
        state = regenerate_heads(root)
        result = append_trial(payload, actor or Actor("collector", str(descriptor.source["collector"])), state.trials.head_hash, data_root=root)
    except BaseException:
        if created_descriptor and descriptor_path.exists(): descriptor_path.unlink()
        if created_content and content_path.exists(): content_path.unlink()
        raise
    return DescriptorRegistration(digest, descriptor.artifact_id, descriptor.descriptor_id, descriptor.descriptor_version, descriptor_path, content_path, result.ledger_path, result.head_path, str(result.record["trial_id"]), recorded_at, result.head_hash)


def register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration:
    """Validate and append one immutable descriptor version with its trial-ledger record."""

    actor = descriptor.actor
    if actor is not None: actor_mapping(actor)
    return _register(descriptor, actor, {})


__all__ = ["DescriptorError", "DescriptorRegistration", "EvidenceDescriptor", "StoredDescriptor", "descriptor_digest", "descriptor_mapping", "load_descriptor_registry", "register_descriptor", "validate_descriptor"]
