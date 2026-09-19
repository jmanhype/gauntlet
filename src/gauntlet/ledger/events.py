"""Typed append-only operation event records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from ._common import Actor, EVENTS_CHAIN, LedgerAppendResult, LedgerError, ZERO_DIGEST, actor_mapping, append_canonical_line, event_body_hash, schema_errors, sealed_hash, validate_event_envelope, validate_timestamp, validate_digest


@dataclass(frozen=True)
class EventRecord:
    """A non-secret operation body; chain hashes are derived at append time."""

    event_id: str; timestamp_utc: str; actor: Actor; verb: str; subject: str
    args_hash: str; output_hash: str | None; status: str; error_class: str | None
    trace: Mapping[str, object]


def append_event(
    event: EventRecord,
    previous_head: str | None,
    *,
    data_root: Path | None = None,
) -> LedgerAppendResult:
    """Append one canonical, hash-chained operation event."""

    if not event.event_id.strip() or not event.subject.strip():
        raise LedgerError("EVENT_ID_INVALID", "event_id and subject must be non-empty", "$")
    if event.status not in ("OK", "ERROR"):
        raise LedgerError("STATUS_INVALID", "status must be OK or ERROR", "$.status")
    if previous_head is not None:
        validate_digest(previous_head, "previous_head")
    validate_timestamp(event.timestamp_utc, "$.timestamp_utc")
    output_hash = event.output_hash if event.output_hash is not None else ZERO_DIGEST
    body: dict[str, object] = {
        "event_id": event.event_id,
        "schema_version": "1",
        "timestamp_utc": event.timestamp_utc,
        "actor": actor_mapping(event.actor),
        "verb": event.verb,
        "subject": event.subject,
        "args_hash": event.args_hash,
        "output_hash": output_hash,
        "status": event.status,
        "error_class": event.error_class,
        "trace": dict(event.trace),
    }
    envelope = dict(body)
    envelope.update({"payload_hash": event_body_hash(body), "previous_head_hash": previous_head if previous_head is not None else ZERO_DIGEST, "event_hash": ZERO_DIGEST})
    schema_error = schema_errors(envelope, "gauntlet.event.v1")
    if schema_error is not None:
        raise LedgerError("SCHEMA_INVALID", schema_error.message, schema_error.path)
    validate_event_envelope(envelope)
    envelope["event_hash"] = sealed_hash(envelope, "event_hash")
    validate_event_envelope(envelope)
    return append_canonical_line(data_root, EVENTS_CHAIN, envelope, previous_head)


__all__ = ["Actor", "EventRecord", "LedgerAppendResult", "append_event"]
