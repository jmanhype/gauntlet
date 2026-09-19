from __future__ import annotations

import ast
import inspect
import json
from itertools import permutations, product
from typing import Any

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.contracts.schemas import SYNTHETIC_BUNDLE, validate
from gauntlet.policy.precedence import GateState, RuleResult, RuleState, evaluate_precedence
from gauntlet.policy.synthetic import build_synthetic_panel_bundle


RULE_STATES = (RuleState.PASS, RuleState.FAIL, RuleState.BLOCKED, RuleState.PENDING, RuleState.INSUFFICIENT_EVIDENCE)


def expected_state(states: tuple[RuleState, ...]) -> GateState:
    if RuleState.BLOCKED in states: return GateState.BLOCKED
    if RuleState.FAIL in states: return GateState.FAIL
    if RuleState.PENDING in states or RuleState.INSUFFICIENT_EVIDENCE in states: return GateState.INSUFFICIENT_EVIDENCE
    return GateState.PASS


def test_exhaustive_state_combinations_and_multiplicities_use_fixed_precedence() -> None:
    for size in range(4):
        for states in product(RULE_STATES, repeat=size):
            results = [RuleResult(state=state) for state in states]
            assert evaluate_precedence(results) is expected_state(states)


def test_precedence_is_independent_of_rule_order() -> None:
    states = [RuleState.PASS, RuleState.INSUFFICIENT_EVIDENCE, RuleState.PENDING, RuleState.FAIL, RuleState.BLOCKED]
    for ordering in permutations(states):
        assert evaluate_precedence([RuleResult(state=state) for state in ordering]) is GateState.BLOCKED
    states = [RuleState.PASS, RuleState.PENDING, RuleState.FAIL, RuleState.FAIL]
    for ordering in permutations(states):
        assert evaluate_precedence([RuleResult(state=state) for state in ordering]) is GateState.FAIL


def test_unknown_or_malformed_rule_output_is_blocked() -> None:
    malformed_states: list[object] = ["UNKNOWN", None, 7, RuleState.PASS.value]
    for state in malformed_states:
        assert evaluate_precedence([RuleResult(state=RuleState.PASS), RuleResult(state=state)]) is GateState.BLOCKED
    valid_shape = RuleResult(state=RuleState.PASS)
    structurally_malformed = [type("NotARule", (), {"state": RuleState.PASS})(), None, "PASS"]
    for item in structurally_malformed:
        assert evaluate_precedence([valid_shape, item]) is GateState.BLOCKED  # type: ignore[list-item]
    assert evaluate_precedence((valid_shape,)) is GateState.BLOCKED  # type: ignore[arg-type]


def test_policy_kernel_has_no_io_time_network_llm_or_threshold_inference_calls() -> None:
    for module in (evaluate_precedence, build_synthetic_panel_bundle):
        tree = ast.parse(inspect.getsource(module))
        banned_imports = {"os", "pathlib", "socket", "http", "urllib", "requests", "subprocess", "time", "datetime"}
        banned_calls = {"open", "input", "now", "today", "time", "sleep", "get", "post", "create"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name.split(".")[0] in banned_imports for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in banned_imports
            if isinstance(node, ast.Call):
                function = node.func
                name = function.attr if isinstance(function, ast.Attribute) else function.id if isinstance(function, ast.Name) else ""
                assert name not in banned_calls


def test_synthetic_bundle_shape_hashes_and_registered_schema() -> None:
    bundle = build_synthetic_panel_bundle(4)
    document = bundle.mapping()
    validation = validate(document, SYNTHETIC_BUNDLE)
    assert validation.valid, validation.errors
    assert document.keys() == {"schema_version", "bundle_type", "generator_version", "seed", "rule_results", "gate_state", "output", "content_hash", "output_hash"}
    assert len(document["rule_results"]) == 4
    for rule in document["rule_results"]:
        assert isinstance(rule, dict)
        assert rule.keys() == {"rule_id", "formula_id", "ruleset_hash", "policy_hash", "artifact_id", "artifact_hash", "observed_value", "comparator", "threshold", "observation_label", "state", "reason"}
    assert bundle.gate_state is GateState.BLOCKED
    assert bundle.output_hash == sha256_digest(canonical_json(document["output"]))
    unsigned = dict(document)
    del unsigned["content_hash"]
    assert bundle.content_hash == sha256_digest(canonical_json(unsigned))
    assert bundle.canonical_bytes == canonical_json(document)
    assert json.loads(bundle.canonical_bytes) == document


def test_seed_reproduces_exact_bundle_and_different_seed_changes_content() -> None:
    first = build_synthetic_panel_bundle(19)
    same = build_synthetic_panel_bundle(19)
    different = build_synthetic_panel_bundle(20)
    assert first == same
    assert first.canonical_bytes == same.canonical_bytes
    assert first.content_hash == same.content_hash
    assert first.output_hash == same.output_hash
    assert different.canonical_bytes != first.canonical_bytes
    assert different.content_hash != first.content_hash


def test_malformed_synthetic_bundle_rejects_fail_closed() -> None:
    valid = build_synthetic_panel_bundle(4).mapping()
    mutations: list[dict[str, Any]] = [{**valid, key: value} for key, value in (("gate_state", "MAYBE"), ("content_hash", "not-a-digest"), ("seed", -1), ("generator_version", ""), ("extra", True))]
    missing = dict(valid); del missing["output"]; mutations.append(missing)
    bad_rule = dict(valid)
    rules = list(bad_rule["rule_results"])
    rules[0] = {**rules[0], "state": "MAYBE"}
    mutations.append({**bad_rule, "rule_results": rules})
    duplicate = dict(valid)
    rules = list(duplicate["rule_results"])
    rules[1] = {**rules[1], "rule_id": rules[0]["rule_id"]}
    mutations.append({**duplicate, "rule_results": rules})
    for mutation in mutations:
        result = validate(mutation, SYNTHETIC_BUNDLE)
        assert not result.valid and result.errors


def test_real_synthetic_bundle_end_to_end_displays_branch_and_blocking_rules(capsys: Any) -> None:
    bundle = build_synthetic_panel_bundle(4)
    selected = evaluate_precedence(list(bundle.rule_results))
    failed_or_blocked = [rule for rule in bundle.rule_results if rule.state in (RuleState.FAIL, RuleState.BLOCKED)]
    lines = [
        f"AGGREGATE: {selected.value} ({bundle.output['selected_precedence_branch']})",
        f"OUTPUT_HASH: {bundle.output_hash}",
        "FAILED_OR_BLOCKED_RULES:",
        *(f"- {rule.rule_id}: {rule.state.value} — {rule.reason}" for rule in failed_or_blocked),
    ]
    report = "\n".join(lines)
    with capsys.disabled():
        print(report)
    assert selected is GateState.BLOCKED
    assert len(failed_or_blocked) == 2
    assert bundle.canonical_bytes == canonical_json(bundle.mapping())
    for rule in failed_or_blocked:
        assert rule.rule_id in report and rule.reason in report
