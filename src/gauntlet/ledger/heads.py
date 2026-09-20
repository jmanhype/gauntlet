"""Deterministic regeneration of ledger head projections."""

from __future__ import annotations

from pathlib import Path

from ._common import EVENTS_CHAIN, TRIALS_CHAIN, HeadState, LedgerError, head_path, ledger_path, verify_chain_bytes, write_head_projection


def regenerate_heads(data_root: Path) -> HeadState:
    """Regenerate both head files only after their ledger bytes verify."""

    root = Path(data_root)
    trial_state = verify_chain_bytes(ledger_path(root, TRIALS_CHAIN), TRIALS_CHAIN)
    event_state = verify_chain_bytes(ledger_path(root, EVENTS_CHAIN), EVENTS_CHAIN)
    for chain, state in ((TRIALS_CHAIN, trial_state), (EVENTS_CHAIN, event_state)):
        if not state.valid or state.failure is not None:
            failure = state.failure
            raise LedgerError(failure.code if failure else "CHAIN_INVALID", failure.message if failure else "chain is invalid", failure.path if failure else str(ledger_path(root, chain)))
    write_head_projection(head_path(root, TRIALS_CHAIN), TRIALS_CHAIN, trial_state.head)
    write_head_projection(head_path(root, EVENTS_CHAIN), EVENTS_CHAIN, event_state.head)
    return HeadState(trial_state.head, event_state.head)


__all__ = ["regenerate_heads"]
