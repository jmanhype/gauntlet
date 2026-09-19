"""Typed append-only registration of GAUNTLET trials."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest

from ._common import Actor, LedgerAppendResult, LedgerError, TRIALS_CHAIN, ZERO_DIGEST, actor_mapping, append_canonical_line, schema_errors, sealed_hash, validate_digest, trial_payload_mapping, validate_trial_envelope


@dataclass(frozen=True)
class TrialPayload:
    """The complete pre-outcome contract for a ``trial.registered`` entry."""

    trial_id: str; family_id: str; venue_track: str; recorded_at_utc: str; hypothesis: str
    success_interpretation: str; failure_interpretation: str; strategy_family: str; parent_trial_ids: tuple[str, ...]
    transfer_hypothesis: str | None; data_window: Mapping[str, object]; split_manifest_hash: str
    source_descriptor_hashes: tuple[str, ...]; frozen: bool; feature_manifest_hash: str; preprocessing_hash: str
    parameters: Mapping[str, object]; search_space: Mapping[str, object]; execution_assumptions: Mapping[str, object]
    adverse_scenarios: tuple[Mapping[str, object], ...]; benchmark_identity: str; benchmark_role: str
    budgets: Mapping[str, object]; stop_condition: Mapping[str, object]; axis_control: Mapping[str, object]
    policy_versions: Mapping[str, object]; resolved_config_hash: str; dependencies: tuple[Mapping[str, object], ...]
    criticality: str


def append_trial(
    payload: TrialPayload,
    actor: Actor,
    previous_head: str | None,
    *,
    data_root: Path | None = None,
) -> LedgerAppendResult:
    """Append one canonical, hash-chained ``trial.registered`` record."""

    if not payload.trial_id.strip() or not payload.family_id.strip():
        raise LedgerError("TRIAL_ID_INVALID", "trial_id and family_id must be non-empty", "$")
    if previous_head is not None:
        validate_digest(previous_head, "previous_head")
    serialized_payload = trial_payload_mapping(payload)
    envelope: dict[str, object] = {
        "schema_version": "1",
        "entry_type": "trial.registered",
        "trial_id": payload.trial_id,
        "family_id": payload.family_id,
        "venue_track": payload.venue_track,
        "recorded_at_utc": payload.recorded_at_utc,
        "actor": actor_mapping(actor),
        "payload_hash": sha256_digest(canonical_json(serialized_payload)),
        "previous_head_hash": previous_head if previous_head is not None else ZERO_DIGEST,
        "entry_hash": ZERO_DIGEST,
        "payload": serialized_payload,
    }
    schema_error = schema_errors(envelope, "gauntlet.trial.v1")
    if schema_error is not None:
        raise LedgerError("SCHEMA_INVALID", schema_error.message, schema_error.path)
    validate_trial_envelope(envelope)
    envelope["entry_hash"] = sealed_hash(envelope, "entry_hash")
    validate_trial_envelope(envelope)
    return append_canonical_line(data_root, TRIALS_CHAIN, envelope, previous_head)


__all__ = ["Actor", "LedgerAppendResult", "TrialPayload", "append_trial"]
