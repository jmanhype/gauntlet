"""Append-only prospective signals and later outcome resolution."""

from __future__ import annotations

import fcntl
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from gauntlet.config.resolver import ResolvedConfig
from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.contracts.manifests import IntegrityFailure
from gauntlet.data.descriptors import load_descriptor_registry
from gauntlet.ledger import Actor, EventRecord, append_event, regenerate_heads
from gauntlet.ledger._common import ZERO_DIGEST, actor_mapping, data_root_path, validate_digest, validate_timestamp

PROSPECTIVE_SCHEMA = "gauntlet.prospective-signal.v1"
OUTCOME_SCHEMA = "gauntlet.prospective-outcome.v1"
_STATUSES = frozenset({"OPEN", "RESOLVED", "SKIPPED", "EXECUTION_FAILED"})
_OBSERVATION_BASES = frozenset({"OBSERVED", "MODELED"})
_VENUES = frozenset({"solana_dex", "hyperliquid", "external", "cross_venue_transfer"})


class ProspectiveError(RuntimeError):
    """Machine-readable prospective recorder rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message); self.code = code; self.message = message; self.path = path


@dataclass(frozen=True)
class ProspectiveDependency:
    descriptor_hash: str; artifact_id: str; observation_basis: str; status: str; as_of_utc: str


@dataclass(frozen=True)
class ProspectiveDependencySnapshot:
    state: str; entries: tuple[ProspectiveDependency, ...]


@dataclass(frozen=True)
class ProspectiveSignal:
    record_id: str; available_at_utc: str; recorded_at_utc: str; label_available_at_utc: str
    venue_track: str; instrument: str; candidate_fingerprint: str; model_fingerprint: str
    config: ResolvedConfig; policy_fingerprint: str; context: Mapping[str, object]
    intended_action: str; notional: float; horizon_bars: int; horizon_seconds: int
    execution_assumptions: Mapping[str, object]; confidence: float; path_share: float
    confidence_semantics: str; dependencies: ProspectiveDependencySnapshot; actor: Actor; initial_reason: str


@dataclass(frozen=True)
class ProspectiveOutcome:
    record_id: str; status: str; actor: Actor; reason: str; timestamp_utc: str
    venue_state: Mapping[str, object]; venue_state_hash: str; realized_value: float | None
    observation_basis: str; related_records: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class ProspectiveRecord:
    record_id: str; status: str; classification: str; eligible_for_prospective_gate_credit: bool
    signal_path: Path; outcome_path: Path | None; signal_hash: str; outcome_hash: str | None
    status_history: tuple[Mapping[str, object], ...]; payload: Mapping[str, object]

    def mapping(self) -> dict[str, object]:
        return dict(self.payload)


@dataclass(frozen=True)
class ProspectiveVerification:
    valid: bool; signal_count: int; outcome_count: int; failure: IntegrityFailure | None


def _invalid(code: str, message: str, path: str = "$") -> ProspectiveError:
    return ProspectiveError(code, message, path)


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _invalid(f"{field.upper()}_INVALID", f"{field} must be a non-empty string", f"$.{field}")
    return value


def _timestamp(value: object, field: str) -> datetime:
    try:
        validate_timestamp(value, f"$.{field}")
    except Exception as error:
        raise _invalid("TIMESTAMP_INVALID", f"{field} must be a UTC ISO-8601 timestamp", f"$.{field}") from error
    assert isinstance(value, str)
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _digest(value: object, field: str) -> str:
    try:
        validate_digest(value, f"$.{field}")
    except Exception as error:
        raise _invalid("FINGERPRINT_INVALID", f"{field} must be sha256:<64 lowercase hexadecimal>", f"$.{field}") from error
    assert isinstance(value, str)
    return value


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _invalid(f"{field.upper()}_INVALID", f"{field} must be an object", f"$.{field}")
    return value


def _finite(value: object, field: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise _invalid(f"{field.upper()}_INVALID", f"{field} must be finite", f"$.{field}")
    result = float(value)
    if minimum is not None and result < minimum:
        raise _invalid(f"{field.upper()}_INVALID", f"{field} must be >= {minimum}", f"$.{field}")
    return result


def _dependency_mapping(snapshot: ProspectiveDependencySnapshot) -> dict[str, object]:
    return {
        "state": snapshot.state,
        "values": [{"descriptor_hash": item.descriptor_hash, "artifact_id": item.artifact_id,
                    "observation_basis": item.observation_basis, "status": item.status,
                    "as_of_utc": item.as_of_utc} for item in snapshot.entries],
    }


def _signal_payload(signal: ProspectiveSignal, classification: str, eligible: bool) -> dict[str, object]:
    return {
        "record_id": signal.record_id,
        "available_at_utc": signal.available_at_utc, "recorded_at_utc": signal.recorded_at_utc,
        "label_available_at_utc": signal.label_available_at_utc, "venue_track": signal.venue_track,
        "instrument": signal.instrument,
        "fingerprints": {
            "candidate": signal.candidate_fingerprint,
            "model": signal.model_fingerprint,
            "config": signal.config.config_hash,
            "policy": signal.policy_fingerprint,
        },
        "context": dict(signal.context),
        "action": {
            "intended": signal.intended_action, "notional": signal.notional,
            "horizon_bars": signal.horizon_bars, "horizon_seconds": signal.horizon_seconds,
            "execution_assumptions": dict(signal.execution_assumptions),
        },
        "confidence": {
            "value": signal.confidence, "path_share": signal.path_share,
            "semantics": signal.confidence_semantics,
        },
        "dependency_snapshot": _dependency_mapping(signal.dependencies), "classification": classification,
        "eligible_for_prospective_gate_credit": eligible,
    }


def _outcome_payload(outcome: ProspectiveOutcome) -> dict[str, object]:
    return {
        "record_id": outcome.record_id, "status": outcome.status, "actor": actor_mapping(outcome.actor),
        "reason": outcome.reason, "timestamp_utc": outcome.timestamp_utc,
        "venue_state": dict(outcome.venue_state), "venue_state_hash": outcome.venue_state_hash,
        "realized_value": outcome.realized_value, "observation_basis": outcome.observation_basis,
        "related_records": [dict(item) for item in outcome.related_records],
    }


def _validate_signal(signal: ProspectiveSignal, data_root: Path) -> tuple[str, bool]:
    _nonempty(signal.record_id, "record_id")
    available = _timestamp(signal.available_at_utc, "available_at_utc")
    recorded = _timestamp(signal.recorded_at_utc, "recorded_at_utc")
    label_available = _timestamp(signal.label_available_at_utc, "label_available_at_utc")
    if available > recorded:
        raise _invalid("TEMPORAL_INVALID", "available_at_utc cannot follow recorded_at_utc", "$.available_at_utc")
    if label_available <= recorded:
        classification, eligible = "HISTORICAL", False
    else:
        classification, eligible = "PROSPECTIVE", True
    if signal.venue_track not in _VENUES:
        raise _invalid("VENUE_INVALID", "venue_track is not registered", "$.venue_track")
    _nonempty(signal.instrument, "instrument")
    _digest(signal.candidate_fingerprint, "candidate_fingerprint")
    _digest(signal.model_fingerprint, "model_fingerprint")
    _digest(signal.policy_fingerprint, "policy_fingerprint")
    if not isinstance(signal.config, ResolvedConfig):
        raise _invalid("CONFIG_INVALID", "config must be a ResolvedConfig", "$.config")
    _mapping(signal.context, "context")
    _nonempty(signal.intended_action, "intended_action")
    _finite(signal.notional, "notional", minimum=0.0)
    if isinstance(signal.horizon_bars, bool) or not isinstance(signal.horizon_bars, int) or signal.horizon_bars < 1:
        raise _invalid("HORIZON_INVALID", "horizon_bars must be a positive integer", "$.horizon_bars")
    if isinstance(signal.horizon_seconds, bool) or not isinstance(signal.horizon_seconds, int) or signal.horizon_seconds < 1:
        raise _invalid("HORIZON_INVALID", "horizon_seconds must be a positive integer", "$.horizon_seconds")
    _mapping(signal.execution_assumptions, "execution_assumptions")
    confidence = _finite(signal.confidence, "confidence", minimum=0.0)
    path_share = _finite(signal.path_share, "path_share", minimum=0.0)
    if confidence > 1.0 or path_share > 1.0:
        raise _invalid("CONFIDENCE_INVALID", "confidence and path_share must be between zero and one", "$.confidence")
    _nonempty(signal.confidence_semantics, "confidence_semantics")
    _nonempty(signal.initial_reason, "initial_reason")
    actor_mapping(signal.actor)
    if not isinstance(signal.dependencies, ProspectiveDependencySnapshot):
        raise _invalid("DEPENDENCY_SNAPSHOT_INVALID", "dependencies must be a ProspectiveDependencySnapshot", "$.dependencies")
    _nonempty(signal.dependencies.state, "dependencies.state")
    if not signal.dependencies.entries:
        raise _invalid("DEPENDENCY_SNAPSHOT_INVALID", "at least one dependency entry is required", "$.dependencies.entries")
    registry = load_descriptor_registry(data_root)
    for index, item in enumerate(signal.dependencies.entries):
        path = f"$.dependencies.entries[{index}]"
        _digest(item.descriptor_hash, f"dependencies.entries[{index}].descriptor_hash")
        _nonempty(item.artifact_id, f"dependencies.entries[{index}].artifact_id")
        if item.observation_basis not in _OBSERVATION_BASES:
            raise _invalid("OBSERVATION_BASIS_INVALID", "observation_basis must be OBSERVED or MODELED", f"{path}.observation_basis")
        _nonempty(item.status, f"dependencies.entries[{index}].status")
        _timestamp(item.as_of_utc, f"dependencies.entries[{index}].as_of_utc")
        stored = registry.get(item.descriptor_hash)
        if stored is None:
            raise _invalid("DEPENDENCY_UNREGISTERED", f"dependency {item.artifact_id!r} is not registered", f"{path}.descriptor_hash")
        if stored.value.get("artifact_id") != item.artifact_id:
            raise _invalid("DEPENDENCY_CONFLICT", "artifact_id does not match registered descriptor", f"{path}.artifact_id")
        if stored.value.get("observation_basis") != item.observation_basis:
            raise _invalid("DEPENDENCY_CONFLICT", "observation_basis does not match registered descriptor", f"{path}.observation_basis")
    return classification, eligible


def _validate_outcome(outcome: ProspectiveOutcome) -> None:
    _nonempty(outcome.record_id, "record_id")
    if outcome.status not in _STATUSES or outcome.status == "OPEN":
        raise _invalid("STATUS_INVALID", "outcome status is not registered", "$.status")
    actor_mapping(outcome.actor)
    _nonempty(outcome.reason, "reason")
    _timestamp(outcome.timestamp_utc, "timestamp_utc")
    state = _mapping(outcome.venue_state, "venue_state")
    _digest(outcome.venue_state_hash, "venue_state_hash")
    if sha256_digest(canonical_json(state)) != outcome.venue_state_hash:
        raise _invalid("VENUE_STATE_HASH_MISMATCH", "venue_state_hash does not match canonical venue_state", "$.venue_state_hash")
    if outcome.status == "RESOLVED":
        _finite(outcome.realized_value, "realized_value")
    elif outcome.realized_value is not None:
        raise _invalid("REALIZED_VALUE_INVALID", "only RESOLVED may carry realized_value", "$.realized_value")
    if outcome.observation_basis not in _OBSERVATION_BASES:
        raise _invalid("OBSERVATION_BASIS_INVALID", "observation_basis must be OBSERVED or MODELED", "$.observation_basis")
    for index, item in enumerate(outcome.related_records):
        _mapping(item, f"related_records[{index}]")


def _paths(data_root: Path) -> tuple[Path, Path, Path]:
    root = data_root / "prospective"
    return root / "signals.jsonl", root / "outcomes.jsonl", root / ".prospective.lock"


def _read_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        rows: list[dict[str, object]] = []
        return rows
    rows: list[dict[str, object]] = []
    for line in path.read_bytes().splitlines():
        value: object = json.loads(line)
        if not isinstance(value, dict):
            raise _invalid("RECORD_INVALID", "prospective record must be an object", str(path))
        rows.append(value)
    return rows


def _head(rows: list[dict[str, object]], field: str) -> str | None:
    return str(rows[-1][field]) if rows else None


def _seal(envelope: dict[str, object], field: str) -> str:
    unsealed = {key: value for key, value in envelope.items() if key != field}
    return sha256_digest(canonical_json(unsealed))


def _append_locked(path: Path, envelope: dict[str, object], field: str) -> None:
    line = canonical_json(envelope) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        if os.write(descriptor, line) != len(line):
            raise _invalid("WRITE_FAILED", "short prospective record write", str(path))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _event(record_id: str, *, timestamp: str, actor: Actor, payload_hash: str,
           output_hash: str, data_root: Path, kind: str) -> None:
    heads = regenerate_heads(data_root)
    event = EventRecord(
        event_id=f"prospective-{kind}-{record_id}",
        timestamp_utc=timestamp,
        actor=actor,
        verb="snapshot.write",
        subject=f"prospective:{record_id}",
        args_hash=payload_hash,
        output_hash=output_hash,
        status="OK",
        error_class=None,
        trace={"run_id": record_id, "kind": kind},
    )
    append_event(event, heads.events.head_hash, data_root=data_root)


def append_signal(signal: ProspectiveSignal) -> ProspectiveRecord:
    root = data_root_path(None)
    classification, eligible = _validate_signal(signal, root)
    signals, outcomes, lock = _paths(root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        verification = verify_prospective(root)
        if not verification.valid:
            failure = verification.failure
            raise _invalid("CHAIN_INVALID", failure.message if failure else "prospective chain is invalid", failure.path if failure else "$")
        rows = _read_lines(signals)
        if any(row.get("record_id") == signal.record_id for row in rows):
            raise _invalid("RECORD_EXISTS", f"prospective signal {signal.record_id!r} already exists")
        payload = _signal_payload(signal, classification, eligible)
        history: tuple[dict[str, object], ...] = ({
            "from": None,
            "to": "OPEN",
            "actor": actor_mapping(signal.actor),
            "reason": signal.initial_reason,
            "timestamp_utc": signal.recorded_at_utc,
        },)
        envelope: dict[str, object] = {
            "schema_version": PROSPECTIVE_SCHEMA,
            "record_id": signal.record_id,
            "classification": classification,
            "eligible_for_prospective_gate_credit": eligible,
            "status": "OPEN",
            "status_history": list(history),
            "payload": payload,
            "payload_hash": sha256_digest(canonical_json(payload)),
            "previous_head_hash": _head(rows, "signal_hash") or ZERO_DIGEST,
            "signal_hash": ZERO_DIGEST,
        }
        envelope["signal_hash"] = _seal(envelope, "signal_hash")
        _append_locked(signals, envelope, "signal_hash")
        _event(signal.record_id, timestamp=signal.recorded_at_utc, actor=signal.actor,
               payload_hash=str(envelope["payload_hash"]), output_hash=str(envelope["signal_hash"]),
               data_root=root, kind="signal")
        return ProspectiveRecord(
            record_id=signal.record_id,
            status="OPEN",
            classification=classification,
            eligible_for_prospective_gate_credit=eligible,
            signal_path=signals,
            outcome_path=outcomes if outcomes.exists() else None,
            signal_hash=str(envelope["signal_hash"]),
            outcome_hash=None,
            status_history=history,
            payload=payload,
        )


def resolve_outcome(record_id: str, outcome: ProspectiveOutcome) -> ProspectiveRecord:
    _nonempty(record_id, "record_id")
    root = data_root_path(None)
    signals, outcomes, lock = _paths(root)
    if not signals.exists():
        raise _invalid("OUTCOME_NOT_FOUND", f"prospective signal {outcome.record_id!r} does not exist")
    with lock.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        verification = verify_prospective(root)
        if not verification.valid:
            failure = verification.failure
            raise _invalid("CHAIN_INVALID", failure.message if failure else "prospective chain is invalid", failure.path if failure else "$")
        signal_rows = _read_lines(signals)
        signal = next((row for row in signal_rows if row.get("record_id") == record_id), None)
        if signal is None:
            raise _invalid("OUTCOME_NOT_FOUND", f"prospective signal {record_id!r} does not exist")
        _validate_outcome(outcome)
        if record_id != outcome.record_id:
            raise _invalid("RECORD_MISMATCH", "record_id and outcome.record_id must match", "$.record_id")
        outcome_rows = _read_lines(outcomes)
        payload = _outcome_payload(outcome)
        payload_hash = sha256_digest(canonical_json(payload))
        prior_outcome = next((row for row in outcome_rows if row.get("record_id") == record_id), None)
        if prior_outcome is not None and prior_outcome.get("payload_hash") == payload_hash:
            raise _invalid("TRANSITION_EXISTS", f"outcome for {record_id!r} already exists")
        if prior_outcome is not None or signal.get("status") != "OPEN":
            raise _invalid("TRANSITION_TERMINAL", f"signal {record_id!r} is already terminal")
        prior_history = signal.get("status_history")
        if not isinstance(prior_history, list):
            raise _invalid("RECORD_INVALID", "signal status_history is malformed", str(signals))
        history = (*prior_history, {
            "from": signal.get("status"),
            "to": outcome.status,
            "actor": actor_mapping(outcome.actor),
            "reason": outcome.reason,
            "timestamp_utc": outcome.timestamp_utc,
        })
        envelope: dict[str, object] = {
            "schema_version": OUTCOME_SCHEMA,
            "record_id": outcome.record_id,
            "signal_hash": signal.get("signal_hash"),
            "status": outcome.status,
            "payload": payload,
            "payload_hash": payload_hash,
            "previous_head_hash": _head(outcome_rows, "outcome_hash") or ZERO_DIGEST,
            "outcome_hash": ZERO_DIGEST,
        }
        envelope["outcome_hash"] = _seal(envelope, "outcome_hash")
        _append_locked(outcomes, envelope, "outcome_hash")
        _event(record_id, timestamp=outcome.timestamp_utc, actor=outcome.actor,
               payload_hash=str(envelope["payload_hash"]), output_hash=str(envelope["outcome_hash"]),
               data_root=root, kind="outcome")
        signal_payload = signal.get("payload")
        assert isinstance(signal_payload, dict)
        return ProspectiveRecord(
            record_id=record_id,
            status=outcome.status,
            classification=str(signal_payload.get("classification")),
            eligible_for_prospective_gate_credit=bool(signal_payload.get("eligible_for_prospective_gate_credit")),
            signal_path=signals,
            outcome_path=outcomes,
            signal_hash=str(signal["signal_hash"]),
            outcome_hash=str(envelope["outcome_hash"]),
            status_history=history,
            payload=payload,
        )


def verify_prospective(data_root: Path | None = None) -> ProspectiveVerification:
    root = data_root_path(data_root)
    signals, outcomes, _ = _paths(root)
    if signals.is_symlink() or outcomes.is_symlink():
        return ProspectiveVerification(False, 0, 0, IntegrityFailure("PATH_INVALID", "prospective history is not a regular file", str(root)))
    for path in (signals, outcomes):
        if path.exists() and (not path.is_file() or (path.read_bytes() and not path.read_bytes().endswith(b"\n"))):
            return ProspectiveVerification(False, 0, 0, IntegrityFailure("TRUNCATED", "prospective history is truncated", str(path)))

    def check(path: Path, rows: list[dict[str, object]], schema: str,
              hash_field: str) -> IntegrityFailure | None:
        previous = ZERO_DIGEST
        seen: set[str] = set()
        for index, row in enumerate(rows):
            location = f"{path}:{index}"
            line = canonical_json(row)
            actual_line = path.read_bytes().splitlines()[index]
            if line != actual_line:
                return IntegrityFailure("CANONICAL_INVALID", "record is not canonical JSON", location)
            if row.get("schema_version") != schema:
                return IntegrityFailure("SCHEMA_INVALID", "unexpected prospective schema", location)
            record_id = row.get("record_id")
            if not isinstance(record_id, str) or not record_id or record_id in seen:
                return IntegrityFailure("RECORD_ID_INVALID", "record_id is missing or duplicated", location)
            seen.add(record_id)
            if row.get("previous_head_hash") != previous:
                return IntegrityFailure("PREVIOUS_HEAD_MISMATCH", "record does not extend prior head", location)
            payload = row.get("payload")
            if not isinstance(payload, dict) or sha256_digest(canonical_json(payload)) != row.get("payload_hash"):
                return IntegrityFailure("PAYLOAD_HASH_MISMATCH", "payload hash mismatch", location)
            expected = _seal(row, hash_field)
            if row.get(hash_field) != expected:
                return IntegrityFailure("ENTRY_HASH_MISMATCH", "terminal hash mismatch", location)
            previous = str(row[hash_field])
        return None

    try:
        signal_rows = _read_lines(signals)
        outcome_rows = _read_lines(outcomes)
    except (OSError, UnicodeError, json.JSONDecodeError, ProspectiveError) as error:
        return ProspectiveVerification(False, 0, 0, IntegrityFailure("READ_FAILED", str(error), str(root)))
    signal_failure = check(signals, signal_rows, PROSPECTIVE_SCHEMA, "signal_hash")
    if signal_failure is not None:
        return ProspectiveVerification(False, len(signal_rows), len(outcome_rows), signal_failure)
    outcome_failure = check(outcomes, outcome_rows, OUTCOME_SCHEMA, "outcome_hash")
    if outcome_failure is not None:
        return ProspectiveVerification(False, len(signal_rows), len(outcome_rows), outcome_failure)
    signal_ids = {str(row.get("record_id")) for row in signal_rows}
    signal_hashes = {str(row.get("signal_hash")) for row in signal_rows}
    for index, row in enumerate(outcome_rows):
        location = f"{outcomes}:{index}"
        if row.get("record_id") not in signal_ids or row.get("signal_hash") not in signal_hashes:
            return ProspectiveVerification(False, len(signal_rows), len(outcome_rows), IntegrityFailure("REFERENCE_INVALID", "outcome does not reference a signal", location))
    return ProspectiveVerification(True, len(signal_rows), len(outcome_rows), None)


__all__ = [
    "OUTCOME_SCHEMA",
    "PROSPECTIVE_SCHEMA",
    "ProspectiveDependency",
    "ProspectiveDependencySnapshot",
    "ProspectiveError",
    "ProspectiveOutcome",
    "ProspectiveRecord",
    "ProspectiveSignal",
    "ProspectiveVerification",
    "append_signal",
    "resolve_outcome",
    "verify_prospective",
]
