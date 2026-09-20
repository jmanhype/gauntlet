"""Seeded, local-only synthetic panel contracts for the gate skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from gauntlet.contracts.canonical import CanonicalJSONError, canonical_json, sha256_digest
from gauntlet.contracts.schemas import SYNTHETIC_BUNDLE, validate

from .precedence import GateState, RuleResult, RuleState, evaluate_precedence


BUNDLE_SCHEMA = SYNTHETIC_BUNDLE
_GENERATOR_VERSION = "1"
_RULESET_HASH = sha256_digest(
    canonical_json(
        {
            "formula_ids": ["effective-observations.minimum", "expectancy.positive", "prospective-window.complete", "replay-integrity.valid"],
            "precedence": ["BLOCKED", "FAIL", "INSUFFICIENT_EVIDENCE", "PASS"],
            "schema_version": "1",
        }
    )
)
_POLICY_HASH = sha256_digest(
    canonical_json(
        {
            "generator": "gauntlet.synthetic-panel@v1",
            "observation_labels": ["OBSERVED", "MODELED"],
            "schema_version": "1",
        }
    )
)
_RULE_SPECS: tuple[dict[str, object], ...] = (
    {"rule_id": "synthetic.effective_observations", "formula_id": "effective-observations.minimum", "observed_value": 220, "comparator": ">=", "threshold": 200, "observation_label": "OBSERVED", "state": RuleState.PASS, "reason": "synthetic effective observations meet the fixed threshold"},
    {"rule_id": "synthetic.expectancy", "formula_id": "expectancy.positive", "observed_value": -12.5, "comparator": ">", "threshold": 0, "observation_label": "OBSERVED", "state": RuleState.FAIL, "reason": "synthetic expectancy is below zero"},
    {"rule_id": "synthetic.prospective_window", "formula_id": "prospective-window.complete", "observed_value": 80, "comparator": ">=", "threshold": 100, "observation_label": "OBSERVED", "state": RuleState.PENDING, "reason": "the synthetic prospective window is intentionally incomplete"},
    {"rule_id": "synthetic.replay_integrity", "formula_id": "replay-integrity.valid", "observed_value": 0, "comparator": "==", "threshold": 1, "observation_label": "OBSERVED", "state": RuleState.BLOCKED, "reason": "one synthetic replay input is intentionally unavailable"},
)


class SyntheticError(RuntimeError):
    """A machine-readable synthetic-panel rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


@dataclass(frozen=True, slots=True)
class SyntheticEvidenceBundle:
    """A canonical synthetic bundle and its real precedence output."""

    schema_version: str; bundle_type: str; generator_version: str; seed: int
    rule_results: tuple[RuleResult, ...]; gate_state: GateState; output: Mapping[str, object]
    content_hash: str; output_hash: str; canonical_bytes: bytes

    def mapping(self) -> dict[str, object]:
        """Return the registered, canonical bundle envelope as plain JSON data."""

        return {
            "schema_version": self.schema_version,
            "bundle_type": self.bundle_type,
            "generator_version": self.generator_version,
            "seed": self.seed,
            "rule_results": [_mapping(rule) for rule in self.rule_results],
            "gate_state": self.gate_state.value,
            "output": dict(self.output),
            "content_hash": self.content_hash,
            "output_hash": self.output_hash,
        }


def _artifact_hash(seed: int, spec: Mapping[str, object]) -> str:
    payload = {"artifact_id": f"{spec['rule_id']}@{seed}", "formula_id": spec["formula_id"], "seed": seed}
    return sha256_digest(canonical_json(payload))


def _rule(seed: int, spec: Mapping[str, object]) -> RuleResult:
    artifact_id = f"{spec['rule_id']}@{seed}"
    return RuleResult(
        state=spec["state"],
        rule_id=str(spec["rule_id"]),
        formula_id=str(spec["formula_id"]),
        ruleset_hash=_RULESET_HASH,
        policy_hash=_POLICY_HASH,
        artifact_id=artifact_id,
        artifact_hash=_artifact_hash(seed, spec),
        observed_value=float(spec["observed_value"]),  # type: ignore[arg-type]
        comparator=str(spec["comparator"]),
        threshold=float(spec["threshold"]),  # type: ignore[arg-type]
        observation_label=str(spec["observation_label"]),
        reason=str(spec["reason"]),
    )


def _mapping(rule: RuleResult) -> dict[str, object]:
    return {
        "rule_id": rule.rule_id,
        "formula_id": rule.formula_id,
        "ruleset_hash": rule.ruleset_hash,
        "policy_hash": rule.policy_hash,
        "artifact_id": rule.artifact_id,
        "artifact_hash": rule.artifact_hash,
        "observed_value": rule.observed_value,
        "comparator": rule.comparator,
        "threshold": rule.threshold,
        "observation_label": rule.observation_label,
        "state": rule.state.value,
        "reason": rule.reason,
    }


def build_synthetic_panel_bundle(seed: int) -> SyntheticEvidenceBundle:
    """Build the fixed-contract, deterministic synthetic panel for *seed*."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise SyntheticError("SEED_INVALID", "seed must be a finite integer", "$.seed")
    rules = tuple(_rule(seed, spec) for spec in _RULE_SPECS)
    gate_state = evaluate_precedence(list(rules))
    output: dict[str, object] = {
        "failed_or_blocked_rules": [_mapping(rule) for rule in rules if rule.state in (RuleState.FAIL, RuleState.BLOCKED)],
        "gate_state": gate_state.value,
        "rule_states": [{"rule_id": rule.rule_id, "state": rule.state.value} for rule in rules],
        "selected_precedence_branch": {
            GateState.BLOCKED: "any BLOCKED",
            GateState.FAIL: "else any FAIL",
            GateState.INSUFFICIENT_EVIDENCE: "else any PENDING or INSUFFICIENT_EVIDENCE",
            GateState.PASS: "else PASS",
        }[gate_state],
    }
    output_hash = sha256_digest(canonical_json(output))
    payload: dict[str, object] = {
        "schema_version": "1",
        "bundle_type": "synthetic-panel",
        "generator_version": _GENERATOR_VERSION,
        "seed": seed,
        "rule_results": [_mapping(rule) for rule in rules],
        "gate_state": gate_state.value,
        "output": output,
        "output_hash": output_hash,
    }
    content_hash = sha256_digest(canonical_json(payload))
    document = {**payload, "content_hash": content_hash}
    try:
        canonical = canonical_json(document)
    except CanonicalJSONError as error:
        raise SyntheticError("CANONICAL_INVALID", f"synthetic bundle cannot be canonicalized: {error.message}", error.path) from error
    validation = validate(document, BUNDLE_SCHEMA)
    if not validation.valid:
        first = validation.errors[0]
        raise SyntheticError("SCHEMA_INVALID", f"{first.path}: {first.message}", first.path)
    return SyntheticEvidenceBundle(
        schema_version="1",
        bundle_type="synthetic-panel",
        generator_version=_GENERATOR_VERSION,
        seed=seed,
        rule_results=rules,
        gate_state=gate_state,
        output=MappingProxyType(output),
        content_hash=content_hash,
        output_hash=output_hash,
        canonical_bytes=canonical,
    )


__all__ = ["BUNDLE_SCHEMA", "SyntheticError", "SyntheticEvidenceBundle", "build_synthetic_panel_bundle"]
