"""Private shared primitives for the append-only ledgers."""
from __future__ import annotations
import fcntl
import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping
from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.contracts.schemas import EVENT, TRIAL, ValidationError, validate
from gauntlet.contracts.manifests import IntegrityFailure, create_exclusive
ZERO_DIGEST = "sha256:" + "0" * 64
TRIALS_CHAIN = "trials"
EVENTS_CHAIN = "events"
TRIAL_HASH_FIELD = "entry_hash"
EVENT_HASH_FIELD = "event_hash"
_actor_kinds = frozenset(("human", "agent", "collector"))
_venues = frozenset(("solana_dex", "hyperliquid", "external", "cross_venue_transfer"))
_criticalities = frozenset(("GATE_CRITICAL", "NON_CRITICAL", "UNKNOWN"))
_sensitive_key_parts = ("password", "secret", "credential", "private_key", "api_key", "signature", "authorization")
_sensitive_key_names = frozenset(("access_token", "refresh_token", "id_token", "api_token"))
_unredacted_key_names = frozenset(("raw_payload", "external_payload", "request_body", "response_body", "unredacted_payload"))
_trial_payload_keys = frozenset(("hypothesis", "success_interpretation", "failure_interpretation", "strategy_family", "parent_trial_ids", "transfer_hypothesis", "data_window", "split_manifest_hash", "source_descriptor_hashes", "frozen", "feature_manifest_hash", "preprocessing_hash", "parameters", "search_space", "execution_assumptions", "adverse_scenarios", "benchmark_identity", "benchmark_role", "budgets", "stop_condition", "axis_control", "policy_versions", "resolved_config_hash", "dependencies", "criticality"))
_event_envelope_keys = frozenset(("event_id", "schema_version", "timestamp_utc", "actor", "verb", "subject", "args_hash", "output_hash", "payload_hash", "previous_head_hash", "event_hash", "status", "error_class", "trace"))
_trial_envelope_keys = frozenset(("schema_version", "entry_type", "trial_id", "family_id", "venue_track", "recorded_at_utc", "actor", "payload_hash", "previous_head_hash", "entry_hash", "payload"))
@dataclass(frozen=True)
class Actor:
    """A non-secret identity that caused a ledger mutation."""
    kind: str; identity: str
@dataclass(frozen=True)
class LedgerAppendResult:
    """The immutable record and physical extent produced by one append."""
    record: Mapping[str, object]; ledger_path: Path; head_path: Path
    head_hash: str; byte_start: int; byte_end: int
@dataclass(frozen=True)
class ChainHead:
    """The verified head and byte range of one JSONL chain."""
    head_hash: str | None; entry_count: int; byte_start: int | None; byte_end: int
@dataclass(frozen=True)
class HeadState:
    """Both deterministic ledger-head projections."""
    trials: ChainHead; events: ChainHead
@dataclass(frozen=True)
class ChainState:
    """An internal verification result for one physical chain."""
    valid: bool; head: ChainHead; failure: IntegrityFailure | None
class LedgerError(RuntimeError):
    """A machine-readable, fail-closed ledger rejection."""
    def __init__(self, code: str, message: str, path: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path
def data_root_path(data_root: Path | None) -> Path:
    """Resolve the explicit or environment-configured local data root."""
    configured = os.environ.get("GAUNTLET_DATA_ROOT")
    return Path(data_root) if data_root is not None else Path(configured or "data")
def ledger_path(data_root: Path | None, chain: str) -> Path:
    """Return the canonical JSONL path for *chain* under *data_root*."""
    return data_root_path(data_root) / "ledger" / f"{chain}.jsonl"
def head_path(data_root: Path | None, chain: str) -> Path:
    """Return the regenerable head path for *chain* under *data_root*."""
    projection = "trial-head" if chain == TRIALS_CHAIN else f"{chain}-head"
    return data_root_path(data_root) / "ledger" / f"{projection}.json"
def actor_mapping(actor: Actor) -> dict[str, str]:
    """Validate and convert an actor without permitting extra fields."""
    if actor.kind not in _actor_kinds or not actor.identity.strip():
        raise LedgerError("ACTOR_CONTEXT_INVALID", "actor kind must be registered and identity must be non-empty", "$.actor")
    value = {"kind": actor.kind, "identity": actor.identity}
    _reject_sensitive_material(value, "$.actor")
    return value
def validate_actor(value: object, path: str = "$.actor") -> None:
    """Validate an already serialized actor envelope."""
    if not isinstance(value, dict) or set(value) != {"kind", "identity"}:
        raise LedgerError("ACTOR_CONTEXT_INVALID", "actor must contain exactly kind and identity", path)
    kind = value.get("kind")
    identity = value.get("identity")
    if kind not in _actor_kinds or not isinstance(identity, str) or not identity.strip():
        raise LedgerError("ACTOR_CONTEXT_INVALID", "actor kind must be registered and identity must be non-empty", path)
    _reject_sensitive_material(value, path)
def validate_digest(value: object, path: str) -> None:
    """Require the canonical lowercase SHA-256 digest form."""
    valid = isinstance(value, str) and value.startswith("sha256:") and len(value) == 71
    hexadecimal = value[7:] if isinstance(value, str) else ""
    if not valid or any(character not in "0123456789abcdef" for character in hexadecimal):
        raise LedgerError("DIGEST_INVALID", "must be sha256:<64 lowercase hexadecimal>", path)
def validate_timestamp(value: object, path: str) -> None:
    """Require a timezone-aware UTC timestamp serialized with a Z suffix."""
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00") if isinstance(value, str) and value.endswith("Z") else None
    except ValueError as parsed_error:
        raise LedgerError("TIMESTAMP_INVALID", "must be a valid ISO-8601 UTC timestamp", path) from parsed_error
    if parsed is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise LedgerError("TIMESTAMP_INVALID", "must be a UTC timestamp ending in Z", path)
def trial_payload_mapping(payload: object) -> dict[str, object]:
    """Validate the complete typed ``trial.registered`` payload."""
    value = asdict(payload) if hasattr(payload, "__dataclass_fields__") else payload
    if not isinstance(value, Mapping):
        raise LedgerError("TRIAL_PAYLOAD_INVALID", "must be an object", "$.payload")
    if hasattr(payload, "__dataclass_fields__"):
        value = {key: item for key, item in value.items() if key not in {"trial_id", "family_id", "venue_track", "recorded_at_utc"}}
    missing = sorted(_trial_payload_keys - set(value))
    unknown = sorted(set(value) - _trial_payload_keys)
    if missing or unknown:
        code = "TRIAL_PAYLOAD_INCOMPLETE" if missing else "TRIAL_PAYLOAD_UNKNOWN_FIELD"
        detail = f"missing fields: {missing}" if missing else f"unknown fields: {unknown}"
        raise LedgerError(code, detail, "$.payload")
    strings = ("hypothesis", "success_interpretation", "failure_interpretation", "strategy_family", "split_manifest_hash", "feature_manifest_hash", "preprocessing_hash", "benchmark_identity", "benchmark_role", "resolved_config_hash")
    for field in strings:
        if not isinstance(value[field], str) or not value[field].strip():
            raise LedgerError("TRIAL_PAYLOAD_INVALID", f"{field} must be a non-empty string", f"$.payload.{field}")
    for field in ("split_manifest_hash", "feature_manifest_hash", "preprocessing_hash", "resolved_config_hash"):
        validate_digest(value[field], f"$.payload.{field}")
    for field in ("data_window", "parameters", "search_space", "execution_assumptions", "budgets", "stop_condition", "axis_control", "policy_versions"):
        if not isinstance(value[field], dict):
            raise LedgerError("TRIAL_PAYLOAD_INVALID", f"{field} must be an object", f"$.payload.{field}")
    arrays = {"parent_trial_ids": str, "source_descriptor_hashes": str, "adverse_scenarios": dict, "dependencies": dict}
    for field, item_type in arrays.items():
        if not isinstance(value[field], (list, tuple)) or not all(isinstance(item, item_type) for item in value[field]):
            raise LedgerError("TRIAL_PAYLOAD_INVALID", f"{field} must be an array of {item_type.__name__} values", f"$.payload.{field}")
    if not value["source_descriptor_hashes"]:
        raise LedgerError("TRIAL_PAYLOAD_INVALID", "at least one source descriptor hash is required", "$.payload.source_descriptor_hashes")
    for index, item in enumerate(value["source_descriptor_hashes"]):
        validate_digest(item, f"$.payload.source_descriptor_hashes[{index}]")
    if type(value["frozen"]) is not bool or value["criticality"] not in _criticalities:
        raise LedgerError("TRIAL_PAYLOAD_INVALID", "frozen or criticality is invalid", "$.payload")
    _reject_sensitive_material(value, "$.payload")
    return {key: value[key] for key in sorted(_trial_payload_keys)}
def schema_errors(record: Mapping[str, object], schema_id: str) -> ValidationError | None:
    """Return the first registered schema rejection, if any."""
    result = validate(record, schema_id)
    return result.errors[0] if result.errors else None
def validate_trial_envelope(value: object) -> None:
    """Apply ledger-specific envelope rules after the registered schema."""
    if not isinstance(value, dict) or set(value) != _trial_envelope_keys:
        raise LedgerError("SCHEMA_INVALID", "trial envelope fields do not match gauntlet.trial.v1", "$")
    if value.get("schema_version") != "1" or value.get("entry_type") != "trial.registered":
        raise LedgerError("SCHEMA_INVALID", "only trial.registered entries are produced by append_trial", "$.entry_type")
    if value.get("venue_track") not in _venues:
        raise LedgerError("UNKNOWN_DISCRIMINATOR", "venue_track is not registered", "$.venue_track")
    for field in ("trial_id", "family_id"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise LedgerError("TYPE_INVALID", f"{field} must be a non-empty string", f"$.{field}")
    validate_timestamp(value.get("recorded_at_utc"), "$.recorded_at_utc")
    validate_actor(value.get("actor"))
    trial_payload_mapping(value.get("payload"))
    _reject_sensitive_material(value, "$")
def validate_event_envelope(value: object) -> None:
    """Apply ledger-specific event envelope rules after the registered schema."""
    if not isinstance(value, dict) or set(value) != _event_envelope_keys:
        raise LedgerError("SCHEMA_INVALID", "event envelope fields do not match gauntlet.event.v1", "$")
    if value.get("schema_version") != "1":
        raise LedgerError("SCHEMA_INVALID", "schema_version must be 1", "$.schema_version")
    for field in ("event_id", "subject"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise LedgerError("TYPE_INVALID", f"{field} must be a non-empty string", f"$.{field}")
    validate_timestamp(value.get("timestamp_utc"), "$.timestamp_utc")
    validate_actor(value.get("actor"))
    for field in ("args_hash", "output_hash", "payload_hash", "previous_head_hash", "event_hash"):
        validate_digest(value.get(field), f"$.{field}")
    status = value.get("status")
    error_class = value.get("error_class")
    invalid_error = status == "ERROR" and (not isinstance(error_class, str) or not error_class.strip() or value.get("output_hash") != ZERO_DIGEST)
    invalid_error = invalid_error or (status == "OK" and error_class is not None)
    if invalid_error:
        raise LedgerError("EVENT_ERROR_INVALID", "event status and error contract are incompatible", "$.error_class")
    trace = value.get("trace")
    if not isinstance(trace, dict) or not trace or not isinstance(trace.get("run_id"), str) or not trace["run_id"].strip():
        raise LedgerError("TRACE_INVALID", "trace must contain a non-empty run_id", "$.trace")
    _reject_sensitive_material(value, "$")
def event_body_hash(envelope: Mapping[str, object]) -> str:
    """Hash the event body with all three integrity fields omitted."""
    body = {key: value for key, value in envelope.items() if key not in {"payload_hash", "previous_head_hash", "event_hash"}}
    return sha256_digest(canonical_json(body))
def sealed_hash(envelope: Mapping[str, object], hash_field: str) -> str:
    """Hash an envelope with only its own terminal hash omitted."""
    unsealed = {key: value for key, value in envelope.items() if key != hash_field}
    return sha256_digest(canonical_json(unsealed))
def _reject_sensitive_material(value: object, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise LedgerError("NON_STRING_OBJECT_KEY", "object keys must be strings", path)
            child_path = f"{path}.{key}"
            normalized = key.casefold().replace("-", "_").replace(" ", "_")
            parts = normalized.split("_")
            sensitive = normalized in _sensitive_key_names or normalized in _unredacted_key_names
            sensitive = sensitive or any(part in normalized for part in _sensitive_key_parts)
            if sensitive:
                raise LedgerError("SECRET_MATERIAL_REJECTED", "credential, key, signature, or unredacted payload material is not ledger-safe", child_path)
            _reject_sensitive_material(item, child_path)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_sensitive_material(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if "-----BEGIN" in value.upper() and "PRIVATE KEY-----" in value.upper():
            raise LedgerError("SECRET_MATERIAL_REJECTED", "private-key material is not ledger-safe", path)
        if value.startswith("sk-") and len(value) >= 20:
            raise LedgerError("SECRET_MATERIAL_REJECTED", "possible API-key material is not ledger-safe", path)
def verify_chain_bytes(path: Path, chain: str) -> ChainState:
    """Verify canonical bytes, payloads, terminal hashes, and prior-head links."""
    if path.is_symlink() or (path.exists() and not path.is_file()):
        return _chain_failure(path, chain, "LEDGER_READ_FAILED", "ledger is not a regular file")
    if not path.exists():
        return ChainState(True, ChainHead(None, 0, None, 0), None)
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        return _chain_failure(path, chain, "LEDGER_TRUNCATED", "final JSONL record has no newline")
    expected_head: str | None = None
    previous_head = ZERO_DIGEST
    byte_start: int | None = None
    byte_end = 0
    entry_count = 0
    trial_ids: set[str] = set()
    event_ids: set[str] = set()
    for line in data.splitlines() if data else []:
        line_start = byte_end
        try:
            record: object = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as error:
            return _chain_failure(path, chain, "JSON_INVALID", str(error), f"$[{entry_count}]")
        if not isinstance(record, dict) or canonical_json(record) != line:
            return _chain_failure(path, chain, "CANONICAL_INVALID", "record is not canonical JSON", f"$[{entry_count}]")
        schema_error = schema_errors(record, TRIAL if chain == TRIALS_CHAIN else EVENT)
        if schema_error is not None:
            return _chain_failure(path, chain, "SCHEMA_INVALID", schema_error.message, schema_error.path)
        try:
            if chain == TRIALS_CHAIN:
                validate_trial_envelope(record)
            else:
                validate_event_envelope(record)
        except LedgerError as error:
            return _chain_failure(path, chain, error.code, error.message, error.path or f"$[{entry_count}]")
        if record.get("previous_head_hash") != previous_head:
            return _chain_failure(path, chain, "PREVIOUS_HEAD_MISMATCH", "record does not extend the preceding head", f"$[{entry_count}].previous_head_hash")
        terminal_field = TRIAL_HASH_FIELD if chain == TRIALS_CHAIN else EVENT_HASH_FIELD
        identifier = record.get("trial_id" if chain == TRIALS_CHAIN else "event_id")
        seen = trial_ids if chain == TRIALS_CHAIN else event_ids
        assert isinstance(identifier, str)
        if identifier in seen:
            return _chain_failure(path, chain, "DUPLICATE_TRIAL" if chain == TRIALS_CHAIN else "DUPLICATE_EVENT", "stable identifier is already present", f"$[{entry_count}]")
        seen.add(identifier)
        payload_hash = sha256_digest(canonical_json(record["payload"])) if chain == TRIALS_CHAIN else event_body_hash(record)
        if payload_hash != record.get("payload_hash"):
            return _chain_failure(path, chain, "PAYLOAD_HASH_MISMATCH", "payload hash does not match canonical bytes", f"$[{entry_count}].payload_hash")
        actual_hash = sealed_hash(record, terminal_field)
        if actual_hash != record.get(terminal_field):
            return _chain_failure(path, chain, "ENTRY_HASH_MISMATCH" if chain == TRIALS_CHAIN else "EVENT_HASH_MISMATCH", "terminal hash does not match canonical envelope", f"$[{entry_count}].{terminal_field}")
        previous_head = record[terminal_field]
        assert isinstance(previous_head, str)
        expected_head = previous_head
        byte_start = line_start
        byte_end += len(line) + 1
        entry_count += 1
    return ChainState(True, ChainHead(expected_head, entry_count, byte_start, byte_end), None)
def _chain_failure(path: Path, chain: str, code: str, message: str, record_path: str | None = None) -> ChainState:
    location = str(path) if record_path is None else f"{path}:{record_path}"
    return ChainState(False, ChainHead(None, 0, None, 0), IntegrityFailure(code, message, location))
def append_canonical_line(
    data_root: Path,
    chain: str,
    record: Mapping[str, object],
    previous_head: str | None,
) -> LedgerAppendResult:
    """Serialize one append under the shared local ledger lock."""
    root = data_root_path(data_root)
    directory = root / "ledger"
    destination = directory / f"{chain}.jsonl"
    projection = head_path(root, chain)
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise LedgerError("LEDGER_PATH_INVALID", "ledger directory is not a real directory", str(directory))
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".ledger.lock"
    if lock_path.is_symlink():
        raise LedgerError("LEDGER_PATH_INVALID", "ledger lock may not be a symlink", str(lock_path))
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = verify_chain_bytes(destination, chain)
        if not state.valid or state.failure is not None:
            failure = state.failure
            raise LedgerError(failure.code if failure else "CHAIN_INVALID", failure.message if failure else "chain is invalid", failure.path if failure else str(destination))
        if previous_head is not None:
            validate_digest(previous_head, "previous_head")
        if previous_head != state.head.head_hash:
            raise LedgerError("LEDGER_CONFLICT", "previous_head does not match the verified current head", str(destination))
        line = canonical_json(record) + b"\n"
        byte_start = state.head.byte_end
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(destination, flags, 0o600)
        try:
            if os.write(descriptor, line) != len(line):
                raise LedgerError("LEDGER_WRITE_FAILED", "short write left the ledger incomplete", str(destination))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        terminal_field = TRIAL_HASH_FIELD if chain == TRIALS_CHAIN else EVENT_HASH_FIELD
        head_hash = record[terminal_field]
        assert isinstance(head_hash, str)
        try:
            write_head_projection(projection, chain, ChainHead(head_hash, state.head.entry_count + 1, byte_start, byte_start + len(line)))
        except LedgerError as error:
            raise LedgerError("HEAD_WRITE_FAILED", f"ledger record was appended but head was not updated: {error.message}", str(projection)) from error
        return LedgerAppendResult(record, destination, projection, head_hash, byte_start, byte_start + len(line))
def write_head_projection(destination: Path, chain: str, head: ChainHead) -> None:
    """Atomically replace one deterministic, regenerable head projection."""
    if destination.is_symlink():
        raise LedgerError("LEDGER_PATH_INVALID", "head projection may not be a symlink", str(destination))
    encoded = canonical_json(_head_value(chain, head))
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        create_exclusive(temporary, encoded)
        os.replace(temporary, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        os.fsync(directory_fd)
        os.close(directory_fd)
    except BaseException as error:
        if temporary.exists():
            temporary.unlink()
        if not isinstance(error, LedgerError):
            raise LedgerError("HEAD_WRITE_FAILED", str(error), str(destination)) from error
        raise
def read_head_projection(destination: Path, chain: str, expected: ChainHead) -> IntegrityFailure | None:
    """Verify one head projection against verified ledger bytes."""
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        return IntegrityFailure("HEAD_READ_FAILED", "head projection is not a regular file", str(destination))
    if not destination.exists():
        if expected.entry_count == 0:
            return None
        return IntegrityFailure("HEAD_MISSING", "head projection has not been generated", str(destination))
    try:
        value: object = json.loads(destination.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return IntegrityFailure("HEAD_READ_FAILED", str(error), str(destination))
    if not isinstance(value, dict) or canonical_json(value) != destination.read_bytes():
        return IntegrityFailure("HEAD_CANONICAL_INVALID", "head projection is not canonical JSON", str(destination))
    if value != _head_value(chain, expected):
        return IntegrityFailure("HEAD_MISMATCH", "head projection does not match verified ledger bytes", str(destination))
    return None
def _head_value(chain: str, head: ChainHead) -> dict[str, object]:
    return {"schema_version": "1", "chain": chain, "head_hash": head.head_hash, "entry_count": head.entry_count, "byte_start": head.byte_start, "byte_end": head.byte_end}
