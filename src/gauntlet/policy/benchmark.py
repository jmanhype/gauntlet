"""Deterministic four-arm benchmarks over one frozen MODELED evidence snapshot."""

from __future__ import annotations

import json
import math
import os
import statistics
import tempfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from multiprocessing import get_context
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.ledger import Actor, EventRecord, append_event, regenerate_heads
from gauntlet.ledger.events import LedgerAppendResult
from gauntlet.risk import PaperPortfolio, RiskPolicyVersion, RiskRequest, evaluate_risk, load_risk_policy


class PolicyBenchmarkError(RuntimeError):
    """A machine-readable, fail-closed policy benchmark rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


_BENCHMARK_SCHEMA_VERSION = "1"
_BENCHMARK_ID = "gauntlet.policy-benchmark.v1"
_FIXTURE_NAME = "frozen-evidence-v1.json"
_DEFAULT_EVENT_TIMESTAMP = "2026-09-18T00:00:00Z"
_MINIMUM_MODEL_CONFIDENCE = 0.70
_ACTIONS = frozenset(("LONG", "SHORT", "HOLD"))
_REQUIRED_ROW_FIELDS = (
    "schema_version", "row_id", "timestamp_utc", "symbol", "observation_basis", "eligible",
    "hand_action", "llm_action", "jev_action", "jev_confidence", "requested_size_usd", "modeled_return",
)
_FEATURE_FIELDS = tuple(field for field in _REQUIRED_ROW_FIELDS if field != "schema_version")


def _plain(value: object) -> object:
    """Convert nested typed contracts to canonical-friendly plain JSON values."""

    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


class PolicyArmKind(str, Enum):
    """The four registered policy benchmark arms."""

    HAND_RULE = "HAND_RULE"
    LLM_LAYER = "LLM_LAYER"
    UNGATED_JEV = "UNGATED_JEV"
    GATED_JEV = "GATED_JEV"


@dataclass(frozen=True, slots=True)
class PolicyArmSpec:
    """The immutable decision policy declaration for one benchmark arm."""

    arm_id: str; kind: PolicyArmKind; decision_field: str
    confidence_field: str | None = None
    confidence_threshold: float | None = None
    fallback_on_low_confidence: bool = False

    def mapping(self) -> dict[str, object]:
        """Return the canonical policy declaration as plain JSON data."""

        return dict(_plain(self))  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class DecisionCostPolicy:
    """Decision cost charged against accepted action notional."""

    decision_cost_per_million_usd: float

    def mapping(self) -> dict[str, object]:
        """Return the canonical cost policy as plain JSON data."""

        return dict(_plain(self))  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class SlippagePolicy:
    """Directional execution slippage charged on accepted action notional."""

    long_short_basis_points: float

    def mapping(self) -> dict[str, object]:
        """Return the canonical slippage policy as plain JSON data."""

        return dict(_plain(self))  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class PolicyBenchmarkConfig:
    """Shared immutable inputs supplied identically to every arm."""

    seed: int; fallback_action: str; return_periods_per_year: int; risk_policy: RiskPolicyVersion
    minimum_decision_confidence: float = _MINIMUM_MODEL_CONFIDENCE
    cost_policy: DecisionCostPolicy = field(default_factory=lambda: DecisionCostPolicy(0.0))
    slippage_policy: SlippagePolicy = field(default_factory=lambda: SlippagePolicy(0.0))

    def mapping(self) -> dict[str, object]:
        """Return the canonical benchmark configuration as plain JSON data."""

        return {
            "seed": self.seed,
            "fallback_action": self.fallback_action,
            "return_periods_per_year": self.return_periods_per_year,
            "minimum_decision_confidence": self.minimum_decision_confidence,
            "feature_fields": list(_FEATURE_FIELDS),
            "cost_policy": self.cost_policy.mapping(),
            "slippage_policy": self.slippage_policy.mapping(),
            "risk_policy": {
                "policy_id": self.risk_policy.policy_id,
                "version": self.risk_policy.version,
                "status": self.risk_policy.status,
                "policy_hash": self.risk_policy.policy_hash,
            },
        }


@dataclass(frozen=True, slots=True)
class PolicyArmMetrics:
    """All required policy-level benchmark metrics for one arm."""

    observations: int; eligible_observations: int; model_decision_coverage: float
    accepted_action_coverage: float; abstention_rate: float; fallback_count: int
    gross_return_usd: float; net_return_usd: float; slippage_cost_usd: float
    decision_cost_usd: float; decision_cost_per_million_usd: float; total_modeled_cost_usd: float
    hit_rate: float | None; sharpe_ratio: float | None; sortino_ratio: float | None
    max_drawdown_usd: float; incorrect_accepted_decisions: int; risk_vetoes: int
    outcomes: tuple[PolicyDecisionOutcome, ...] = ()

    def mapping(self) -> dict[str, object]:
        """Return the metric envelope as plain canonical JSON data."""

        return {key: value for key, value in _plain(self).items() if key != "outcomes"}  # type: ignore[union-attr]


@dataclass(frozen=True, slots=True)
class PolicyDecisionOutcome:
    """One immutable raw decision and its deterministic local disposition."""

    row_id: str; timestamp_utc: str; symbol: str; observation_basis: str; eligible: bool
    raw_action: str; raw_size_usd: float; fallback: bool; abstained: bool
    executed_action: str; approved_size_usd: float; modeled_return: float
    realized_return_usd: float; decision_cost_usd: float; slippage_cost_usd: float
    risk_veto: bool; risk_disposition: str

    def mapping(self) -> dict[str, object]:
        """Return one inspectable arm outcome as plain JSON data."""

        return dict(_plain(self))  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class PolicyArmReport:
    """One arm's report over the exact shared frozen snapshot."""

    arm_id: str; kind: PolicyArmKind; observation_basis: str
    input_snapshot_hash: str; policy_hash: str; cost_hash: str; risk_hash: str
    feature_fields: tuple[str, ...]; metrics: PolicyArmMetrics
    outcomes: tuple[PolicyDecisionOutcome, ...]; content_hash: str

    def mapping(self) -> dict[str, object]:
        """Return the full arm report as plain canonical JSON data."""

        value = dict(_plain(self))  # type: ignore[arg-type]
        value["metrics"] = self.metrics.mapping()
        return value


@dataclass(frozen=True, slots=True)
class PolicyBenchmarkResult:
    """The canonical result for all four arms over one frozen snapshot."""

    schema_version: str; benchmark_id: str; seed: int; observation_basis: str
    input_snapshot_hash: str; policy_hash: str; cost_hash: str; risk_hash: str
    fallback_action: str; feature_fields: tuple[str, ...]
    configuration: PolicyBenchmarkConfig; configuration_hash: str
    arm_reports: Mapping[str, PolicyArmReport]; report_hash: str; canonical_bytes: bytes

    def mapping(self) -> dict[str, object]:
        """Return the complete report as plain canonical JSON data."""

        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "seed": self.seed,
            "observation_basis": self.observation_basis,
            "input_snapshot_hash": self.input_snapshot_hash,
            "policy_hash": self.policy_hash,
            "cost_hash": self.cost_hash,
            "risk_hash": self.risk_hash,
            "fallback_action": self.fallback_action,
            "feature_fields": list(self.feature_fields),
            "configuration": self.configuration.mapping(),
            "configuration_hash": self.configuration_hash,
            "arm_reports": [report.mapping() for report in self.arm_reports.values()],
            "report_hash": self.report_hash,
        }


def build_default_policy_arms() -> tuple[PolicyArmSpec, ...]:
    """Return the four declared synthetic benchmark arms."""

    return (
        PolicyArmSpec("HAND_RULE", PolicyArmKind.HAND_RULE, "hand_action"),
        PolicyArmSpec("LLM_LAYER", PolicyArmKind.LLM_LAYER, "llm_action"),
        PolicyArmSpec("UNGATED_JEV", PolicyArmKind.UNGATED_JEV, "jev_action", "jev_confidence"),
        PolicyArmSpec("GATED_JEV", PolicyArmKind.GATED_JEV, "jev_action", "jev_confidence", 0.75, True),
    )


def default_policy_benchmark_config() -> PolicyBenchmarkConfig:
    """Return the deterministic shared policy benchmark configuration."""

    return PolicyBenchmarkConfig(
        seed=20260918,
        fallback_action="HOLD",
        return_periods_per_year=252,
        risk_policy=load_risk_policy(),
        cost_policy=DecisionCostPolicy(0.0),
        slippage_policy=SlippagePolicy(0.0),
    )


def _number(value: object, path: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise PolicyBenchmarkError("NUMBER_INVALID", f"{path} must be a finite number", path)
    number = float(value)
    if minimum is not None and number < minimum:
        raise PolicyBenchmarkError("NUMBER_INVALID", f"{path} must be at least {minimum}", path)
    if maximum is not None and number > maximum:
        raise PolicyBenchmarkError("NUMBER_INVALID", f"{path} must be at most {maximum}", path)
    return number


def _content_hash(value: Mapping[str, object]) -> str:
    return sha256_digest(canonical_json(dict(value)))


def _timestamp(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise PolicyBenchmarkError("TIMESTAMP_INVALID", f"{path} must be a UTC ISO-8601 string", path)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00") if value.endswith("Z") else None
    except ValueError as error:
        raise PolicyBenchmarkError("TIMESTAMP_INVALID", f"{path} must be a UTC ISO-8601 string", path) from error
    if parsed is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise PolicyBenchmarkError("TIMESTAMP_INVALID", f"{path} must end in Z and use UTC", path)
    return value


def _validate_rows(rows: object) -> tuple[list[dict[str, object]], bytes, str]:
    if not isinstance(rows, (list, tuple)):
        raise PolicyBenchmarkError("ROWS_INVALID", "frozen_rows must be a list or tuple", "$.frozen_rows")
    validated: list[dict[str, object]] = []
    row_ids: set[str] = set()
    for index, source in enumerate(rows):
        path = f"$.frozen_rows[{index}]"
        if not isinstance(source, Mapping):
            raise PolicyBenchmarkError("ROW_INVALID", "each frozen row must be an object", path)
        missing = [field for field in _REQUIRED_ROW_FIELDS if field not in source]
        if missing: raise PolicyBenchmarkError("ROW_INCOMPLETE", f"missing fields: {missing}", path)
        row = dict(source)
        if row["schema_version"] != "1": raise PolicyBenchmarkError("ROW_INVALID", "schema_version must be 1", f"{path}.schema_version")
        row_id = row["row_id"]
        if not isinstance(row_id, str) or not row_id.strip() or row_id in row_ids: raise PolicyBenchmarkError("ROW_ID_INVALID", "row_id must be non-empty and unique", f"{path}.row_id")
        row_ids.add(row_id)
        _timestamp(row["timestamp_utc"], f"{path}.timestamp_utc")
        if not isinstance(row["symbol"], str) or not row["symbol"].strip(): raise PolicyBenchmarkError("ROW_INVALID", "symbol must be a non-empty string", f"{path}.symbol")
        if row["observation_basis"] != "MODELED": raise PolicyBenchmarkError("BASIS_INVALID", "policy benchmark rows must use MODELED evidence", f"{path}.observation_basis")
        if type(row["eligible"]) is not bool: raise PolicyBenchmarkError("ROW_INVALID", "eligible must be boolean", f"{path}.eligible")
        for action_field in ("hand_action", "llm_action", "jev_action"):
            if row[action_field] not in _ACTIONS:
                raise PolicyBenchmarkError("ACTION_INVALID", f"{action_field} must be LONG, SHORT, or HOLD", f"{path}.{action_field}")
        _number(row["jev_confidence"], f"{path}.jev_confidence", minimum=0.0, maximum=1.0)
        _number(row["requested_size_usd"], f"{path}.requested_size_usd", minimum=0.0)
        _number(row["modeled_return"], f"{path}.modeled_return")
        validated.append(row)
    try:
        snapshot_bytes = canonical_json(validated)
    except (TypeError, ValueError) as error:
        raise PolicyBenchmarkError("CANONICAL_INVALID", f"frozen rows cannot be canonicalized: {error}", "$.frozen_rows") from error
    return validated, snapshot_bytes, sha256_digest(snapshot_bytes)


def _validate_arms(arms: tuple[PolicyArmSpec, ...] | list[PolicyArmSpec]) -> tuple[PolicyArmSpec, ...]:
    if not isinstance(arms, (list, tuple)):
        raise PolicyBenchmarkError("ARMS_INVALID", "arms must be a list or tuple", "$.arms")
    declarations = tuple(arms)
    if {arm.kind for arm in declarations} != set(PolicyArmKind) or len(declarations) != len(PolicyArmKind):
        raise PolicyBenchmarkError("ARMS_INVALID", "exactly one declaration is required for each registered arm", "$.arms")
    arm_ids: set[str] = set()
    expected_fields = {
        PolicyArmKind.HAND_RULE: "hand_action",
        PolicyArmKind.LLM_LAYER: "llm_action",
        PolicyArmKind.UNGATED_JEV: "jev_action",
        PolicyArmKind.GATED_JEV: "jev_action",
    }
    for index, arm in enumerate(declarations):
        path = f"$.arms[{index}]"
        if not isinstance(arm, PolicyArmSpec): raise PolicyBenchmarkError("ARM_INVALID", "each arm must be a PolicyArmSpec", path)
        if not isinstance(arm.arm_id, str) or not arm.arm_id.strip() or arm.arm_id in arm_ids: raise PolicyBenchmarkError("ARM_ID_INVALID", "arm_id must be non-empty and unique", f"{path}.arm_id")
        arm_ids.add(arm.arm_id)
        if arm.decision_field != expected_fields[arm.kind]:
            raise PolicyBenchmarkError("ARM_INVALID", f"{arm.kind.value} must consume {expected_fields[arm.kind]}", f"{path}.decision_field")
        if arm.kind in (PolicyArmKind.UNGATED_JEV, PolicyArmKind.GATED_JEV):
            if arm.confidence_field != "jev_confidence": raise PolicyBenchmarkError("ARM_INVALID", "Jev arms must consume jev_confidence", f"{path}.confidence_field")
        elif arm.confidence_field is not None:
            raise PolicyBenchmarkError("ARM_INVALID", "non-Jev arms must not declare a confidence field", f"{path}.confidence_field")
        if arm.fallback_on_low_confidence:
            if arm.kind != PolicyArmKind.GATED_JEV: raise PolicyBenchmarkError("ARM_INVALID", "only GATED_JEV may fall back on confidence", f"{path}.fallback_on_low_confidence")
            if arm.confidence_threshold is None: raise PolicyBenchmarkError("ARM_INVALID", "a gated arm requires a threshold", f"{path}.confidence_threshold")
            _number(arm.confidence_threshold, f"{path}.confidence_threshold", minimum=0.0, maximum=1.0)
        elif arm.confidence_threshold is not None:
            raise PolicyBenchmarkError("ARM_INVALID", "an ungated arm must not declare a threshold", f"{path}.confidence_threshold")
    return declarations


def _validate_config(config: PolicyBenchmarkConfig) -> PolicyBenchmarkConfig:
    if not isinstance(config, PolicyBenchmarkConfig):
        raise PolicyBenchmarkError("CONFIG_INVALID", "config must be a PolicyBenchmarkConfig", "$.config")
    if isinstance(config.seed, bool) or not isinstance(config.seed, int):
        raise PolicyBenchmarkError("SEED_INVALID", "seed must be an integer", "$.config.seed")
    if config.fallback_action not in _ACTIONS:
        raise PolicyBenchmarkError("ACTION_INVALID", "fallback_action must be LONG, SHORT, or HOLD", "$.config.fallback_action")
    if isinstance(config.return_periods_per_year, bool) or not isinstance(config.return_periods_per_year, int) or config.return_periods_per_year < 1:
        raise PolicyBenchmarkError("PERIODS_INVALID", "return_periods_per_year must be a positive integer", "$.config.return_periods_per_year")
    _number(config.minimum_decision_confidence, "$.config.minimum_decision_confidence", minimum=0.0, maximum=1.0)
    _number(config.cost_policy.decision_cost_per_million_usd, "$.config.cost_policy.decision_cost_per_million_usd", minimum=0.0)
    _number(config.slippage_policy.long_short_basis_points, "$.config.slippage_policy.long_short_basis_points", minimum=0.0)
    tracked_risk_policy = load_risk_policy()
    risk_policy = config.risk_policy
    if not isinstance(risk_policy, RiskPolicyVersion):
        raise PolicyBenchmarkError("RISK_POLICY_INVALID", "risk_policy must be a RiskPolicyVersion", "$.config.risk_policy")
    if (
        risk_policy.policy_id != tracked_risk_policy.policy_id
        or risk_policy.version != tracked_risk_policy.version
        or risk_policy.status != tracked_risk_policy.status
        or risk_policy.policy_hash != tracked_risk_policy.policy_hash
        or risk_policy.canonical_bytes != tracked_risk_policy.canonical_bytes
    ):
        raise PolicyBenchmarkError("RISK_POLICY_MISMATCH", "risk_policy must be the tracked qts.risk@v1 policy", "$.config.risk_policy")
    return config


@dataclass(frozen=True, slots=True)
class _PolicyDecision:
    """Pre-risk policy output retained separately from raw row evidence."""

    row_id: str; timestamp_utc: str; symbol: str; eligible: bool
    raw_action: str; raw_size_usd: float; selected_action: str; selected_size_usd: float
    modeled_return: float; fallback: bool; abstained: bool


@dataclass(frozen=True, slots=True)
class _RiskCandidate:
    """The picklable material used to construct typed risk contracts off-process."""

    arm_id: str; decision: _PolicyDecision


@dataclass(frozen=True, slots=True)
class _RiskEvaluation:
    """The picklable subset of the typed risk result needed by the report."""

    disposition: str; approved_size_usd: float; policy_hash: str


_NO_RISK_RESULTS: tuple[_RiskEvaluation, ...] = ()


def _risk_worker_initializer(data_root: str) -> None:
    """Confine the risk kernel's environment-derived ledger I/O to a sandbox."""

    os.environ["GAUNTLET_DATA_ROOT"] = data_root


def _evaluate_risk_candidates(policy_path: Path, candidates: list[_RiskCandidate]) -> list[_RiskEvaluation]:
    """Construct typed risk inputs and evaluate the declared kernel in the worker."""

    policy = load_risk_policy(policy_path)
    actor = Actor("agent", "gauntlet-policy-benchmark")
    results: list[_RiskEvaluation] = []
    for candidate in candidates:
        decision = candidate.decision
        portfolio = PaperPortfolio(
            as_of_utc=decision.timestamp_utc,
            equity_usd=1_000_000.0,
            peak_equity_usd=1_000_000.0,
            daily_pnl_usd=0.0,
        )
        request = RiskRequest(
            request_id=f"policy-benchmark-{candidate.arm_id}-{decision.row_id}",
            actor=actor,
            symbol=decision.symbol,
            requested_size_usd=decision.selected_size_usd,
            requested_leverage=1.0,
            risk_amount_usd=abs(decision.modeled_return) * decision.selected_size_usd,
            correlation=0.0,
            evidence_gate_state="PASS",
        )
        result = evaluate_risk(request, portfolio, policy)
        results.append(_RiskEvaluation(result.disposition, result.approved_size_usd, result.policy_hash))
    return results


def _run_risk_kernel(policy: RiskPolicyVersion, candidates: list[_RiskCandidate]) -> tuple[_RiskEvaluation, ...]:
    """Evaluate risk in a one-worker child with an isolated temporary data root."""

    if not candidates:
        return _NO_RISK_RESULTS
    with tempfile.TemporaryDirectory(prefix="gauntlet-policy-risk-") as data_root:
        with ProcessPoolExecutor(
            max_workers=1,
            initializer=_risk_worker_initializer,
            initargs=(data_root,),
            mp_context=get_context("fork"),
        ) as executor:
            results = executor.submit(_evaluate_risk_candidates, policy.path, candidates).result(timeout=60)
    if len(results) != len(candidates):
        raise PolicyBenchmarkError("RISK_RESULT_INVALID", "risk kernel returned an incomplete result set", "$.risk")
    if any(result.policy_hash != policy.policy_hash for result in results):
        raise PolicyBenchmarkError("RISK_POLICY_MISMATCH", "risk kernel result does not bind the tracked policy", "$.risk_policy")
    return tuple(results)


def _decision(row: Mapping[str, object], arm: PolicyArmSpec, config: PolicyBenchmarkConfig) -> _PolicyDecision:
    """Apply only row eligibility and arm gating before deterministic risk."""

    raw_action = str(row[arm.decision_field])
    raw_size = float(row["requested_size_usd"]) if raw_action != "HOLD" else 0.0
    selected_action = raw_action
    selected_size = raw_size
    fallback = False
    abstained = False
    recorded_eligible = row["eligible"] is True
    confidence = float(row["jev_confidence"])
    if not recorded_eligible:
        selected_action = "HOLD"
        selected_size = 0.0
    elif arm.fallback_on_low_confidence:
        assert arm.confidence_threshold is not None
        if confidence < arm.confidence_threshold:
            abstained = True
            if confidence < config.minimum_decision_confidence:
                fallback = True
                selected_action = config.fallback_action
                selected_size = raw_size if selected_action != "HOLD" else 0.0
                abstained = selected_action == "HOLD"
            else:
                selected_action = "HOLD"
                selected_size = 0.0
    return _PolicyDecision(
        row_id=str(row["row_id"]),
        timestamp_utc=str(row["timestamp_utc"]),
        symbol=str(row["symbol"]),
        eligible=recorded_eligible,
        raw_action=raw_action,
        raw_size_usd=raw_size,
        selected_action=selected_action,
        selected_size_usd=selected_size,
        modeled_return=float(row["modeled_return"]),
        fallback=fallback,
        abstained=abstained,
    )


def _finalize_outcome(
    decision: _PolicyDecision,
    config: PolicyBenchmarkConfig,
    risk_result: _RiskEvaluation | None,
) -> PolicyDecisionOutcome:
    """Apply the kernel's hard disposition without changing raw policy evidence."""

    selected_action = decision.selected_action
    selected_size = decision.selected_size_usd
    risk_veto = False
    disposition = "NOT_CHECKED"
    if risk_result is not None:
        disposition = risk_result.disposition
        if disposition != "CONTINUE":
            risk_veto = True
            selected_action = "HOLD"
            selected_size = 0.0
        else:
            selected_size = risk_result.approved_size_usd
            if selected_size == 0.0:
                selected_action = "HOLD"
    accepted = selected_action != "HOLD" and selected_size > 0.0
    direction = 1.0 if selected_action == "LONG" else -1.0 if selected_action == "SHORT" else 0.0
    gross_return = decision.modeled_return * selected_size * direction if accepted else 0.0
    decision_cost = selected_size * config.cost_policy.decision_cost_per_million_usd / 1_000_000.0 if accepted else 0.0
    slippage = selected_size * config.slippage_policy.long_short_basis_points / 10_000.0 if accepted else 0.0
    body: dict[str, object] = {
        "row_id": decision.row_id,
        "timestamp_utc": decision.timestamp_utc,
        "symbol": decision.symbol,
        "observation_basis": "MODELED",
        "eligible": decision.eligible,
        "raw_action": decision.raw_action,
        "raw_size_usd": decision.raw_size_usd,
        "fallback": decision.fallback,
        "abstained": decision.abstained,
        "executed_action": selected_action,
        "approved_size_usd": selected_size,
        "modeled_return": decision.modeled_return,
        "realized_return_usd": gross_return - decision_cost - slippage,
        "decision_cost_usd": decision_cost,
        "slippage_cost_usd": slippage,
        "risk_veto": risk_veto,
        "risk_disposition": disposition,
    }
    return PolicyDecisionOutcome(**body)  # type: ignore[arg-type]


def _metrics(
    rows: list[dict[str, object]],
    outcomes: tuple[PolicyDecisionOutcome, ...],
    config: PolicyBenchmarkConfig,
) -> PolicyArmMetrics:
    observations = len(rows)
    eligible = sum(row["eligible"] is True for row in rows)
    model_decisions = sum(outcome.raw_action != "HOLD" for outcome in outcomes)
    accepted_outcomes = [outcome for outcome in outcomes if outcome.executed_action != "HOLD" and outcome.approved_size_usd > 0.0]
    returns = [outcome.realized_return_usd for outcome in outcomes]
    mean_return = statistics.fmean(returns) if returns else 0.0
    standard_deviation = statistics.stdev(returns) if len(returns) >= 2 else 0.0
    sharpe = mean_return / standard_deviation * math.sqrt(config.return_periods_per_year) if len(returns) >= 2 and standard_deviation != 0.0 else None
    downside = math.sqrt(sum(min(value, 0.0) ** 2 for value in returns) / len(returns)) if returns else 0.0
    sortino = mean_return / downside * math.sqrt(config.return_periods_per_year) if returns and downside != 0.0 else None
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in returns:
        cumulative += value
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)
    return PolicyArmMetrics(
        observations=observations,
        eligible_observations=eligible,
        model_decision_coverage=model_decisions / observations if observations else 0.0,
        accepted_action_coverage=len(accepted_outcomes) / observations if observations else 0.0,
        abstention_rate=sum(outcome.executed_action == "HOLD" for outcome in outcomes) / observations if observations else 0.0,
        fallback_count=sum(outcome.fallback for outcome in outcomes),
        gross_return_usd=sum(outcome.realized_return_usd + outcome.decision_cost_usd + outcome.slippage_cost_usd for outcome in accepted_outcomes),
        net_return_usd=sum(outcome.realized_return_usd for outcome in accepted_outcomes),
        slippage_cost_usd=sum(outcome.slippage_cost_usd for outcome in accepted_outcomes),
        decision_cost_usd=sum(outcome.decision_cost_usd for outcome in accepted_outcomes),
        decision_cost_per_million_usd=config.cost_policy.decision_cost_per_million_usd,
        total_modeled_cost_usd=sum(outcome.decision_cost_usd + outcome.slippage_cost_usd for outcome in accepted_outcomes),
        hit_rate=sum(outcome.realized_return_usd > 0.0 for outcome in accepted_outcomes) / len(accepted_outcomes) if accepted_outcomes else None,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown_usd=max_drawdown,
        incorrect_accepted_decisions=sum(outcome.realized_return_usd <= 0.0 for outcome in accepted_outcomes),
        risk_vetoes=sum(outcome.risk_veto for outcome in outcomes),
        outcomes=outcomes,
    )


def load_frozen_evidence_rows() -> list[dict[str, object]]:
    """Load the checked-in synthetic MODELED fixture as fresh row objects."""

    fixture = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "policy" / _FIXTURE_NAME
    try:
        value: object = json.loads(fixture.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PolicyBenchmarkError("FIXTURE_INVALID", f"cannot read registered frozen evidence fixture: {error}", str(fixture)) from error
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise PolicyBenchmarkError("FIXTURE_INVALID", "fixture must contain a list of objects", str(fixture))
    return [dict(item) for item in value]


def run_policy_benchmark(
    frozen_rows: list[Mapping[str, object]],
    arms: tuple[PolicyArmSpec, ...] | list[PolicyArmSpec] = (),
    config: PolicyBenchmarkConfig | None = None,
) -> PolicyBenchmarkResult:
    """Run all four declared arms over one immutable frozen snapshot."""

    selected_arms = _validate_arms(tuple(build_default_policy_arms()) if not arms else arms)
    selected_config = _validate_config(default_policy_benchmark_config() if config is None else config)
    rows, _snapshot_bytes, snapshot_hash = _validate_rows(frozen_rows)
    policy_hash = sha256_digest(canonical_json([arm.mapping() for arm in selected_arms]))
    cost_hash = sha256_digest(
        canonical_json(
            {
                "cost_policy": selected_config.cost_policy.mapping(),
                "slippage_policy": selected_config.slippage_policy.mapping(),
            }
        )
    )
    risk_hash = selected_config.risk_policy.policy_hash
    configuration_hash = sha256_digest(canonical_json(selected_config.mapping()))
    decisions_by_arm: dict[str, list[_PolicyDecision]] = {}
    risk_candidates: list[_RiskCandidate] = []
    for arm in selected_arms:
        decisions = [_decision(row, arm, selected_config) for row in rows]
        decisions_by_arm[arm.kind.value] = decisions
        risk_candidates.extend(
            _RiskCandidate(arm.arm_id, decision)
            for decision in decisions
            if decision.selected_action != "HOLD" and decision.selected_size_usd > 0.0
        )
    risk_results = _run_risk_kernel(selected_config.risk_policy, risk_candidates)
    risk_by_request = {
        f"policy-benchmark-{candidate.arm_id}-{candidate.decision.row_id}": result
        for candidate, result in zip(risk_candidates, risk_results)
    }
    arm_reports: dict[str, PolicyArmReport] = {}
    for arm in selected_arms:
        outcomes = tuple(
            _finalize_outcome(
                decision,
                selected_config,
                risk_by_request.get(f"policy-benchmark-{arm.arm_id}-{decision.row_id}"),
            )
            for decision in decisions_by_arm[arm.kind.value]
        )
        metrics = _metrics(rows, outcomes, selected_config)
        arm_body: dict[str, object] = {
            "arm_id": arm.arm_id,
            "kind": arm.kind.value,
            "observation_basis": "MODELED",
            "input_snapshot_hash": snapshot_hash,
            "policy_hash": policy_hash,
            "cost_hash": cost_hash,
            "risk_hash": risk_hash,
            "feature_fields": list(_FEATURE_FIELDS),
            "metrics": metrics.mapping(),
            "outcomes": [outcome.mapping() for outcome in outcomes],
        }
        arm_reports[arm.kind.value] = PolicyArmReport(
            arm_id=arm.arm_id,
            kind=arm.kind,
            observation_basis="MODELED",
            input_snapshot_hash=snapshot_hash,
            policy_hash=policy_hash,
            cost_hash=cost_hash,
            risk_hash=risk_hash,
            feature_fields=_FEATURE_FIELDS,
            metrics=metrics,
            outcomes=outcomes,
            content_hash=_content_hash(arm_body),
        )
    report_body: dict[str, object] = {
        "schema_version": _BENCHMARK_SCHEMA_VERSION,
        "benchmark_id": _BENCHMARK_ID,
        "seed": selected_config.seed,
        "observation_basis": "MODELED",
        "input_snapshot_hash": snapshot_hash,
        "policy_hash": policy_hash,
        "cost_hash": cost_hash,
        "risk_hash": risk_hash,
        "fallback_action": selected_config.fallback_action,
        "feature_fields": list(_FEATURE_FIELDS),
        "configuration": selected_config.mapping(),
        "configuration_hash": configuration_hash,
        "arm_reports": [report.mapping() for report in arm_reports.values()],
    }
    report_hash = sha256_digest(canonical_json(report_body))
    report = {**report_body, "report_hash": report_hash}
    canonical_bytes = canonical_json(report)
    return PolicyBenchmarkResult(
        schema_version=_BENCHMARK_SCHEMA_VERSION,
        benchmark_id=_BENCHMARK_ID,
        seed=selected_config.seed,
        observation_basis="MODELED",
        input_snapshot_hash=snapshot_hash,
        policy_hash=policy_hash,
        cost_hash=cost_hash,
        risk_hash=risk_hash,
        fallback_action=selected_config.fallback_action,
        feature_fields=_FEATURE_FIELDS,
        configuration=selected_config,
        configuration_hash=configuration_hash,
        arm_reports=MappingProxyType(arm_reports),
        report_hash=report_hash,
        canonical_bytes=canonical_bytes,
    )


def _verify_sealed_section(value: Mapping[str, object], section: str, path: str) -> None:
    body = {key: item for key, item in value.items() if key != "content_hash"}
    expected = _content_hash(body)
    if value.get("content_hash") != expected:
        raise PolicyBenchmarkError("HASH_MISMATCH", f"{section} content hash does not match its canonical body", path)


def _verify_report_result(result: PolicyBenchmarkResult) -> None:
    """Fail closed on any report or nested identity tampering before I/O."""

    if not isinstance(result, PolicyBenchmarkResult):
        raise PolicyBenchmarkError("RESULT_INVALID", "result must be a PolicyBenchmarkResult", "$")
    mapping = result.mapping()
    if canonical_json(mapping) != result.canonical_bytes:
        raise PolicyBenchmarkError("CANONICAL_INVALID", "canonical bytes do not match the result mapping", "$.canonical_bytes")
    report_body = {key: value for key, value in mapping.items() if key != "report_hash"}
    if result.report_hash != _content_hash(report_body):
        raise PolicyBenchmarkError("HASH_MISMATCH", "report hash does not match its canonical body", "$.report_hash")
    expected_cost_hash = _content_hash(
        {
            "cost_policy": result.configuration.cost_policy.mapping(),
            "slippage_policy": result.configuration.slippage_policy.mapping(),
        }
    )
    expected_configuration_hash = _content_hash(result.configuration.mapping())
    if result.cost_hash != expected_cost_hash:
        raise PolicyBenchmarkError("HASH_MISMATCH", "cost hash must bind decision and slippage policy", "$.cost_hash")
    if result.risk_hash != result.configuration.risk_policy.policy_hash:
        raise PolicyBenchmarkError("HASH_MISMATCH", "risk hash must bind the tracked policy version", "$.risk_hash")
    if result.configuration_hash != expected_configuration_hash:
        raise PolicyBenchmarkError("HASH_MISMATCH", "configuration hash does not match its canonical body", "$.configuration_hash")
    for arm_id, report in result.arm_reports.items():
        arm_path = f"$.arm_reports[{arm_id}]"
        arm_mapping = report.mapping()
        _verify_sealed_section(arm_mapping, "arm report", arm_path)
        for field, expected in (
            ("input_snapshot_hash", result.input_snapshot_hash),
            ("policy_hash", result.policy_hash),
            ("cost_hash", result.cost_hash),
            ("risk_hash", result.risk_hash),
        ):
            if getattr(report, field) != expected:
                raise PolicyBenchmarkError("IDENTITY_MISMATCH", f"arm {field} differs from report identity", f"{arm_path}.{field}")


def write_policy_benchmark_report(
    result: PolicyBenchmarkResult,
    destination: Path,
    *,
    data_root: Path | None = None,
) -> tuple[Path, LedgerAppendResult | None]:
    """Write canonical report bytes and optionally append event evidence."""

    _verify_report_result(result)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(result.canonical_bytes + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if data_root is None:
        return destination, None
    event_timestamp = max(
        (outcome.timestamp_utc for report in result.arm_reports.values() for outcome in report.outcomes),
        default=_DEFAULT_EVENT_TIMESTAMP,
    )
    event_arguments = {
        "report_hash": result.report_hash,
        "report_schema_version": result.schema_version,
        "benchmark_id": result.benchmark_id,
    }
    event = EventRecord(
        event_id=f"policy-benchmark-{result.report_hash[7:39]}",
        timestamp_utc=event_timestamp,
        actor=Actor("agent", "gauntlet-policy-benchmark"),
        verb="evidence.project",
        subject="policy-benchmark",
        args_hash=sha256_digest(canonical_json(event_arguments)),
        output_hash=result.report_hash,
        status="OK",
        error_class=None,
        trace={"run_id": f"policy-benchmark:{result.report_hash}", "report_file": destination.name},
    )
    previous_head = regenerate_heads(Path(data_root)).events.head_hash
    append_result = append_event(event, previous_head, data_root=Path(data_root))
    return destination, append_result


__all__ = [
    "DecisionCostPolicy",
    "PolicyArmKind",
    "PolicyArmMetrics",
    "PolicyArmReport",
    "PolicyArmSpec",
    "PolicyBenchmarkConfig",
    "PolicyBenchmarkError",
    "PolicyBenchmarkResult",
    "PolicyDecisionOutcome",
    "SlippagePolicy",
    "build_default_policy_arms",
    "default_policy_benchmark_config",
    "load_frozen_evidence_rows",
    "run_policy_benchmark",
    "write_policy_benchmark_report",
]
