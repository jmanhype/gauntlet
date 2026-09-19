"""Verification for the trial and operation-event hash chains."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gauntlet.contracts.manifests import IntegrityFailure

from ._common import EVENTS_CHAIN, TRIALS_CHAIN, ChainHead, HeadState, head_path, ledger_path, read_head_projection, verify_chain_bytes


@dataclass(frozen=True)
class ChainVerification:
    """A machine-readable result for both physical ledgers and their heads."""

    valid: bool; trials: ChainHead; events: ChainHead; failure: IntegrityFailure | None


def verify_chains(data_root: Path) -> ChainVerification:
    """Recompute both ledger chains and compare their head projections."""

    root = Path(data_root)
    trial_state = verify_chain_bytes(ledger_path(root, TRIALS_CHAIN), TRIALS_CHAIN)
    if not trial_state.valid or trial_state.failure is not None:
        failure = trial_state.failure or IntegrityFailure("CHAIN_INVALID", "trial chain is invalid", str(ledger_path(root, TRIALS_CHAIN)))
        return ChainVerification(False, trial_state.head, ChainHead(None, 0, None, 0), failure)
    event_state = verify_chain_bytes(ledger_path(root, EVENTS_CHAIN), EVENTS_CHAIN)
    if not event_state.valid or event_state.failure is not None:
        failure = event_state.failure or IntegrityFailure("CHAIN_INVALID", "event chain is invalid", str(ledger_path(root, EVENTS_CHAIN)))
        return ChainVerification(False, trial_state.head, event_state.head, failure)
    failures = (
        read_head_projection(head_path(root, TRIALS_CHAIN), TRIALS_CHAIN, trial_state.head),
        read_head_projection(head_path(root, EVENTS_CHAIN), EVENTS_CHAIN, event_state.head),
    )
    if any(failure is not None for failure in failures):
        return ChainVerification(False, trial_state.head, event_state.head, next(failure for failure in failures if failure is not None))
    return ChainVerification(True, trial_state.head, event_state.head, None)


__all__ = ["ChainVerification", "verify_chains"]
