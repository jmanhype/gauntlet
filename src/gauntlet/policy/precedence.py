"""Pure, order-independent precedence for evidence-gate rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RuleState(str, Enum):
    """Every state that an evidence-gate rule may emit."""

    PASS = "PASS"; FAIL = "FAIL"; BLOCKED = "BLOCKED"; PENDING = "PENDING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class GateState(str, Enum):
    """The deterministic aggregate gate state."""

    PASS = "PASS"; FAIL = "FAIL"; BLOCKED = "BLOCKED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True, slots=True)
class RuleResult:
    """One inspectable rule calculation supplied to the precedence kernel."""

    state: object
    rule_id: str = "precedence.kernel"; formula_id: str = "precedence.state"
    ruleset_hash: str = "sha256:" + "0" * 64; policy_hash: str = "sha256:" + "0" * 64
    artifact_id: str = "precedence.kernel"; artifact_hash: str = "sha256:" + "0" * 64
    observed_value: float = 0.0; comparator: str = ">="; threshold: float = 0.0
    observation_label: str = "OBSERVED"
    reason: str = "kernel precedence input"


_PRECEDENCE: tuple[tuple[frozenset[RuleState], GateState], ...] = (
    (frozenset((RuleState.BLOCKED,)), GateState.BLOCKED),
    (frozenset((RuleState.FAIL,)), GateState.FAIL),
    (frozenset((RuleState.PENDING, RuleState.INSUFFICIENT_EVIDENCE)), GateState.INSUFFICIENT_EVIDENCE),
)


def evaluate_precedence(rule_results: list[RuleResult]) -> GateState:
    """Apply the fixed fail-closed precedence order without rule-order effects.

    Unknown state values and structurally malformed result entries are treated
    as ``BLOCKED``.  The kernel performs no I/O and derives nothing except the
    aggregate state from the supplied results.
    """

    if not isinstance(rule_results, list):
        return GateState.BLOCKED
    states: list[RuleState] = []
    for result in rule_results:
        if not isinstance(result, RuleResult):
            return GateState.BLOCKED
        state = result.state
        if not isinstance(state, RuleState):
            return GateState.BLOCKED
        states.append(state)
    for emitted, aggregate in _PRECEDENCE:
        if any(state in emitted for state in states):
            return aggregate
    return GateState.PASS


__all__ = ["GateState", "RuleResult", "RuleState", "evaluate_precedence"]
