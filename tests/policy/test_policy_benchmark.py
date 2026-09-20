from __future__ import annotations

import ast, copy, json, math, statistics
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

import pytest

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.ledger import verify_chains
from gauntlet.policy.benchmark import (
    DecisionCostPolicy, PolicyBenchmarkError, PolicyArmKind, PolicyBenchmarkConfig, SlippagePolicy,
    build_default_policy_arms, default_policy_benchmark_config, load_frozen_evidence_rows,
    run_policy_benchmark, write_policy_benchmark_report,
)
from gauntlet.risk import load_risk_policy


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "policy" / "frozen-evidence-v1.json"
EVIDENCE = ROOT / "evidence" / "policy-benchmark" / "policy-benchmark-v1.json"
METRIC_FIELDS = {
    "observations", "eligible_observations", "model_decision_coverage", "accepted_action_coverage",
    "abstention_rate", "fallback_count", "gross_return_usd", "net_return_usd", "slippage_cost_usd",
    "decision_cost_usd", "decision_cost_per_million_usd", "total_modeled_cost_usd", "hit_rate",
    "sharpe_ratio", "sortino_ratio", "max_drawdown_usd", "incorrect_accepted_decisions", "risk_vetoes",
}


def row(row_id: str, action: str, size: float, modeled_return: float) -> dict[str, Any]:
    return {
        "schema_version": "1", "row_id": row_id, "timestamp_utc": "2026-09-18T00:15:00Z",
        "symbol": "BTC/USDT", "observation_basis": "MODELED", "eligible": True,
        "hand_action": action, "llm_action": action, "jev_action": action,
        "jev_confidence": 0.9, "requested_size_usd": size, "modeled_return": modeled_return,
    }


def benchmark(rows: list[dict[str, Any]], config: PolicyBenchmarkConfig | None = None) -> Any:
    return run_policy_benchmark(rows, build_default_policy_arms(), config or default_policy_benchmark_config())


def cost_config(periods: int = 252) -> PolicyBenchmarkConfig:
    return replace(default_policy_benchmark_config(), cost_policy=DecisionCostPolicy(10.0), slippage_policy=SlippagePolicy(1.0), return_periods_per_year=periods)


def metrics(result: Any, kind: PolicyArmKind) -> Any:
    return result.arm_reports[kind.value].metrics


def test_four_real_arms_use_one_frozen_snapshot_and_declared_basis() -> None:
    first = benchmark(load_frozen_evidence_rows())
    second = benchmark(load_frozen_evidence_rows())
    assert [arm.arm_id for arm in first.arm_reports.values()] == ["HAND_RULE", "LLM_LAYER", "UNGATED_JEV", "GATED_JEV"]
    assert len({arm.input_snapshot_hash for arm in first.arm_reports.values()}) == 1
    assert first.input_snapshot_hash == sha256_digest(canonical_json(list(load_frozen_evidence_rows())))
    assert first.observation_basis == "MODELED" and all(arm.observation_basis == "MODELED" for arm in first.arm_reports.values())
    assert first.canonical_bytes == second.canonical_bytes and first.report_hash == second.report_hash


def test_default_fixture_is_synthetic_and_identical_to_registered_rows() -> None:
    fixture = json.loads(FIXTURE.read_text())
    assert fixture == [dict(item) for item in load_frozen_evidence_rows()] and all(item["observation_basis"] == "MODELED" for item in fixture)


def test_checked_in_evidence_matches_current_fixture_result() -> None:
    result = benchmark(load_frozen_evidence_rows())
    assert EVIDENCE.read_bytes() == result.canonical_bytes + b"\n"


def test_required_metric_fields_and_equal_shared_policy_inputs() -> None:
    result = benchmark(load_frozen_evidence_rows())
    assert set(result.arm_reports) == {kind.value for kind in PolicyArmKind}
    for arm in result.arm_reports.values():
        assert set(arm.metrics.mapping()) == METRIC_FIELDS
        assert arm.policy_hash == result.policy_hash and arm.cost_hash == result.cost_hash and arm.risk_hash == result.risk_hash
    assert result.risk_hash == load_risk_policy().policy_hash


def test_cost_hash_binds_decision_and_slippage_policy() -> None:
    baseline = default_policy_benchmark_config()
    changed = replace(baseline, slippage_policy=SlippagePolicy(1.0))
    baseline_result = benchmark(load_frozen_evidence_rows(), baseline)
    changed_result = benchmark(load_frozen_evidence_rows(), changed)
    expected = sha256_digest(canonical_json({"cost_policy": changed.cost_policy.mapping(), "slippage_policy": changed.slippage_policy.mapping()}))
    assert changed_result.cost_hash == expected and changed_result.cost_hash != baseline_result.cost_hash
    assert all(arm.cost_hash == changed_result.cost_hash for arm in changed_result.arm_reports.values())


def test_ungated_model_coverage_differs_from_accepted_coverage_and_gate_falls_back() -> None:
    result = benchmark(load_frozen_evidence_rows())
    ungated = metrics(result, PolicyArmKind.UNGATED_JEV)
    gated = metrics(result, PolicyArmKind.GATED_JEV)
    assert ungated.model_decision_coverage == 1.0
    assert ungated.accepted_action_coverage == 6 / 8
    assert ungated.fallback_count == 0
    assert gated.fallback_count == 1
    assert gated.accepted_action_coverage == 4 / 8
    low_confidence = gated.outcomes[5]
    assert low_confidence.raw_action == "LONG" and low_confidence.raw_size_usd == 40.0
    assert low_confidence.executed_action == "HOLD" and low_confidence.approved_size_usd == 0.0
    assert low_confidence.fallback is True and low_confidence.risk_veto is False


def test_risk_veto_zeroes_exposure_but_preserves_raw_decision_evidence() -> None:
    result = benchmark(load_frozen_evidence_rows())
    for arm in result.arm_reports.values():
        outcome = arm.outcomes[7]
        assert outcome.risk_veto is True
        assert outcome.approved_size_usd == 0.0 and outcome.executed_action == "HOLD"
        assert arm.metrics.risk_vetoes == 1
    ungated = result.arm_reports[PolicyArmKind.UNGATED_JEV.value].outcomes[7]
    assert ungated.raw_action == "LONG" and ungated.raw_size_usd == 70.0


def test_cost_and_slippage_are_charged_on_accepted_notional_only() -> None:
    config = cost_config()
    result = benchmark([row("one", "LONG", 50.0, 0.02), row("two", "LONG", 25.0, 0.0)], config)
    arm = result.arm_reports[PolicyArmKind.UNGATED_JEV.value]
    assert arm.metrics.gross_return_usd == pytest.approx(1.0)
    assert arm.metrics.decision_cost_usd == pytest.approx(0.00075)
    assert arm.metrics.decision_cost_per_million_usd == 10.0
    assert arm.metrics.slippage_cost_usd == pytest.approx(0.0075)
    assert arm.metrics.total_modeled_cost_usd == pytest.approx(0.00825)
    assert arm.metrics.net_return_usd == pytest.approx(0.99175)


def test_risk_adjusted_metric_formulas_use_realized_net_returns() -> None:
    config = cost_config(1)
    rows = [
        row("one", "LONG", 50.0, 0.02),
        row("two", "LONG", 50.0, 0.0),
        row("three", "LONG", 50.0, -0.01),
    ]
    arm = benchmark(rows, config).arm_reports[PolicyArmKind.UNGATED_JEV.value]
    returns = [0.9945, -0.0055, -0.5055]
    sharpe = statistics.mean(returns) / statistics.stdev(returns)
    downside = math.sqrt(sum(min(value, 0.0) ** 2 for value in returns) / len(returns))
    assert arm.metrics.sharpe_ratio == pytest.approx(sharpe)
    assert arm.metrics.sortino_ratio == pytest.approx(statistics.mean(returns) / downside)
    assert arm.metrics.max_drawdown_usd == pytest.approx(0.511)
    assert arm.metrics.hit_rate == pytest.approx(1 / 3)
    assert arm.metrics.incorrect_accepted_decisions == 2


def test_risk_adjusted_metrics_include_hold_periods() -> None:
    config = cost_config(1)
    rows = [
        row("win", "LONG", 50.0, 0.02),
        row("hold", "HOLD", 50.0, 0.10),
        row("loss", "LONG", 50.0, -0.01),
    ]
    arm = benchmark(rows, config).arm_reports[PolicyArmKind.UNGATED_JEV.value]
    returns = [0.9945, 0.0, -0.5055]
    expected_sharpe = statistics.mean(returns) / statistics.stdev(returns)
    downside = math.sqrt(sum(min(value, 0.0) ** 2 for value in returns) / len(returns))
    assert arm.metrics.sharpe_ratio == pytest.approx(expected_sharpe)
    assert arm.metrics.sortino_ratio == pytest.approx(statistics.mean(returns) / downside)
    assert arm.metrics.max_drawdown_usd == pytest.approx(0.5055)


def test_empty_and_zero_variance_cases_use_explicit_nulls() -> None:
    empty = benchmark([])
    for arm in empty.arm_reports.values():
        assert arm.metrics.sharpe_ratio is None and arm.metrics.sortino_ratio is None
        assert arm.metrics.hit_rate is None and arm.metrics.max_drawdown_usd == 0.0
        assert arm.metrics.accepted_action_coverage == 0.0
    config = cost_config()
    flat = benchmark([row("one", "LONG", 50.0, 0.01), row("two", "LONG", 50.0, 0.01)], config)
    arm = flat.arm_reports[PolicyArmKind.UNGATED_JEV.value]
    assert arm.metrics.gross_return_usd == pytest.approx(1.0)
    assert arm.metrics.sharpe_ratio is None and arm.metrics.sortino_ratio is None


@pytest.mark.parametrize(
    ("label", "mutate"),
    (
        ("arm", lambda arms, config, rows: ([replace(arms[0], arm_id="HAND_RULE_V2"), *arms[1:]], config, rows)),
        ("cost", lambda arms, config, rows: (arms, replace(config, cost_policy=DecisionCostPolicy(11.0)), rows)),
        ("slippage", lambda arms, config, rows: (arms, replace(config, slippage_policy=SlippagePolicy(1.0)), rows)),
        ("gated-threshold", lambda arms, config, rows: ([*arms[:3], replace(arms[3], confidence_threshold=0.76)], config, rows)),
        ("fallback", lambda arms, config, rows: (arms, replace(config, fallback_action="LONG"), rows)),
        ("seed", lambda arms, config, rows: (arms, replace(config, seed=config.seed + 1), rows)),
        ("row", lambda arms, config, rows: (arms, config, [{**rows[0], "modeled_return": 0.031}, *rows[1:]])),
    ),
)
def test_material_mutations_change_report_identity(label: str, mutate: Callable[[list[Any], PolicyBenchmarkConfig, list[dict[str, Any]]], tuple[list[Any], PolicyBenchmarkConfig, list[dict[str, Any]]]]) -> None:
    original_arms = list(build_default_policy_arms())
    original_config = default_policy_benchmark_config()
    original_rows = load_frozen_evidence_rows()
    baseline = run_policy_benchmark(copy.deepcopy(original_rows), tuple(original_arms), original_config)
    changed_arms, changed_config, changed_rows = mutate(copy.deepcopy(original_arms), original_config, copy.deepcopy(original_rows))
    changed = run_policy_benchmark(changed_rows, tuple(changed_arms), changed_config)

    def verify_independent_hash(report: Any) -> None:
        mapping = report.mapping()
        body = {key: value for key, value in mapping.items() if key != "report_hash"}
        assert sha256_digest(canonical_json(body)) == report.report_hash
        assert canonical_json(mapping) == report.canonical_bytes

    verify_independent_hash(baseline)
    verify_independent_hash(changed)
    assert changed.report_hash != baseline.report_hash
    assert label


def test_inputs_are_not_mutated_by_benchmark_orchestration() -> None:
    rows = load_frozen_evidence_rows()
    arms = build_default_policy_arms()
    config = default_policy_benchmark_config()
    row_bytes = canonical_json([dict(item) for item in rows])
    arm_bytes = canonical_json([arm.mapping() for arm in arms])
    config_bytes = canonical_json(config.mapping())
    run_policy_benchmark(rows, arms, config)
    assert canonical_json([dict(item) for item in rows]) == row_bytes
    assert canonical_json([arm.mapping() for arm in arms]) == arm_bytes
    assert canonical_json(config.mapping()) == config_bytes


def test_risk_kernel_ledger_io_is_confined_to_process_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent_root = tmp_path / "parent-controlled-root"
    monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(parent_root))
    result = benchmark(load_frozen_evidence_rows())
    assert any(outcome.risk_veto for arm in result.arm_reports.values() for outcome in arm.outcomes)
    assert not (parent_root / "ledger").exists()


def test_e2e_writer_produces_canonical_report_and_appends_event_evidence(tmp_path: Path) -> None:
    result = benchmark(load_frozen_evidence_rows())
    destination = tmp_path / "reports" / "policy-benchmark-v1.json"
    written, event = write_policy_benchmark_report(result, destination, data_root=tmp_path / "data")
    assert written.read_bytes() == result.canonical_bytes + b"\n"
    assert json.loads(written.read_text()) == result.mapping()
    assert event is not None and event.record["output_hash"] == result.report_hash
    assert event.record["verb"] == "evidence.project"
    assert verify_chains(tmp_path / "data").valid


def test_writer_rejects_tampered_report_before_file_or_event_io(tmp_path: Path) -> None:
    result = benchmark(load_frozen_evidence_rows())
    tampered = replace(result, report_hash=sha256_digest(b"tampered"))
    destination = tmp_path / "reports" / "policy-benchmark-v1.json"
    data_root = tmp_path / "data"
    with pytest.raises(PolicyBenchmarkError):
        write_policy_benchmark_report(tampered, destination, data_root=data_root)
    assert not destination.exists()
    assert not (data_root / "ledger").exists()


def test_writer_rejects_resealed_nested_identity_tampering(tmp_path: Path) -> None:
    result = benchmark(load_frozen_evidence_rows())
    key = PolicyArmKind.UNGATED_JEV.value
    arm = replace(result.arm_reports[key], risk_hash=sha256_digest(b"nested-tamper"))
    staged = replace(result, arm_reports={**result.arm_reports, key: arm})
    mapping = staged.mapping()
    body = {field: value for field, value in mapping.items() if field != "report_hash"}
    tampered = replace(
        staged,
        report_hash=sha256_digest(canonical_json(body)),
        canonical_bytes=canonical_json(mapping),
    )
    with pytest.raises(PolicyBenchmarkError):
        write_policy_benchmark_report(tampered, tmp_path / "report.json")
    assert not (tmp_path / "report.json").exists()


def test_benchmark_has_no_order_or_real_money_interface() -> None:
    source = Path(__file__).resolve().parents[2] / "src" / "gauntlet" / "policy" / "benchmark.py"
    tree = ast.parse(source.read_text())
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for node in ast.walk(tree) if isinstance(node, ast.Call)
    }
    assert not calls & {"submit_order", "place_order", "send_order", "authorize_real_money"}
    assert "real_money_authorized" not in source.read_text()
