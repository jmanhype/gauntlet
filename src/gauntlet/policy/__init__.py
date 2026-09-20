"""Deterministic evidence-gate policy kernels."""

from .precedence import GateState, RuleResult, RuleState, evaluate_precedence
from .synthetic import SyntheticError, SyntheticEvidenceBundle, build_synthetic_panel_bundle

__all__ = [
    "GateState",
    "RuleResult",
    "RuleState",
    "SyntheticError",
    "SyntheticEvidenceBundle",
    "build_synthetic_panel_bundle",
    "evaluate_precedence",
]
