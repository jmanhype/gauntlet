"""Append-only quarantine transitions for evidence descriptors."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from gauntlet.ledger import Actor
from gauntlet.ledger._common import actor_mapping

from .descriptors import DescriptorError, DescriptorRegistration, EvidenceDescriptor, _register, descriptor_digest, load_descriptor_registry


@dataclass(frozen=True)
class QuarantineReason:
    """The inspectable reason and scope recorded in a quarantine transition."""

    code: str; message: str
    affected_artifacts: tuple[str, ...] = ()

    def mapping(self) -> dict[str, object]:
        return {"code": self.code, "message": self.message, "affected_artifacts": list(self.affected_artifacts)}


def _validated_reason(reason: QuarantineReason) -> QuarantineReason:
    if not reason.code.strip() or not reason.message.strip():
        raise DescriptorError("QUARANTINE_REASON_INVALID", "code and message must be non-empty", "$.reason")
    if any(not isinstance(item, str) or not item.strip() for item in reason.affected_artifacts):
        raise DescriptorError("QUARANTINE_REASON_INVALID", "affected artifacts must be non-empty strings", "$.reason.affected_artifacts")
    return reason


def quarantine_descriptor(
    original_hash: str,
    reason: QuarantineReason,
    actor: Actor,
) -> DescriptorRegistration:
    """Create a new immutable QUARANTINED version without changing the original."""

    _validated_reason(reason)
    actor_mapping(actor)
    records = load_descriptor_registry()
    original = records.get(original_hash)
    if original is None:
        raise DescriptorError("DESCRIPTOR_UNVERIFIED", "original descriptor hash is not registered", "$.original_hash")
    value = original.value
    original_effective = datetime.fromisoformat(value["effective_at_utc"].replace("Z", "+00:00"))  # type: ignore[arg-type]
    effective_at = max(datetime.now(timezone.utc).replace(microsecond=0), original_effective + timedelta(microseconds=1)).isoformat().replace("+00:00", "Z")
    quality: dict[str, object] = dict(value["quality"])  # type: ignore[arg-type]
    quality.update({"state": "QUARANTINED", "reason": reason.mapping(), "original_descriptor_hash": original_hash})
    replacement = EvidenceDescriptor(
        descriptor_schema=str(value["descriptor_schema"]), artifact_id=str(value["artifact_id"]), descriptor_id=str(value["descriptor_id"]),
        descriptor_version=int(value["descriptor_version"]) + 1, descriptor_hash="sha256:" + "0" * 64, supersedes_descriptor_hash=original_hash,  # type: ignore[arg-type]
        effective_at_utc=effective_at, superseded_at_utc=None, kind=str(value["kind"]), venue_track=str(value["venue_track"]), content_hash=str(value["content_hash"]),
        source=dict(value["source"]), observation_basis=str(value["observation_basis"]), coverage=dict(value["coverage"]), freshness=dict(value["freshness"]),  # type: ignore[arg-type]
        quality=quality, dependencies=tuple(dict(item) for item in value["dependencies"]), criticality=str(value["criticality"]),  # type: ignore[arg-type]
        downstream_metrics=tuple(str(item) for item in value["downstream_metrics"]), content_bytes=original.content_path.read_bytes(), actor=actor,  # type: ignore[arg-type]
    )
    sealed = replace(replacement, descriptor_hash=descriptor_digest(replacement))
    return _register(sealed, actor, {"quarantine_reason": reason.mapping()})


__all__ = ["QuarantineReason", "quarantine_descriptor"]
