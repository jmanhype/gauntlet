"""Deterministic paper-risk boundaries, separate from evidence-gate arithmetic."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.ledger import Actor, EventRecord, append_event, regenerate_heads
from gauntlet.ledger._common import LedgerError, actor_mapping, data_root_path, validate_timestamp
from .import_qts import RiskError, RiskPolicyVersion

RISK_STATEMENTS = ("PASS", "ADJUST", "HOLD", "QUARANTINE", "STOP")
RISK_DISPOSITIONS = frozenset(("CONTINUE", "HOLD", "QUARANTINE", "STOP"))


@dataclass(frozen=True, slots=True)
class PaperPosition:
    symbol: str; notional_usd: float; correlation: float


@dataclass(frozen=True, slots=True)
class PaperPortfolio:
    as_of_utc: str; equity_usd: float; peak_equity_usd: float; daily_pnl_usd: float
    positions: tuple[PaperPosition, ...] = (); consecutive_losses: int = 0; latency_ms: int = 0
    error_rate_percent: float = 0.0; consecutive_errors: int = 0; loss_velocity_factor: float = 0.0


@dataclass(frozen=True, slots=True)
class RiskRequest:
    request_id: str; actor: Actor; symbol: str; requested_size_usd: float
    requested_leverage: float; risk_amount_usd: float; correlation: float; evidence_gate_state: str


@dataclass(frozen=True, slots=True)
class RiskCheckResult:
    disposition: str; requested_size_usd: float; approved_size_usd: float; checks: tuple[Mapping[str, object], ...]
    warnings: tuple[str, ...]; policy_id: str; policy_version: int; policy_hash: str
    venue_applicability: Mapping[str, object]; evidence_gate_state: str; observation_basis: str
    boundary_events: tuple[Mapping[str, object], ...]; event_head_hashes: tuple[str, ...]
    trial_history_input: Mapping[str, object]


def _invalid(message: str, path: str = "$", code: str = "RISK_INVALID") -> RiskError:
    return RiskError(code, message, path)


def _number(value: object, path: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise _invalid(f"{path} must be finite", path)
    result = float(value)
    if minimum is not None and result < minimum:
        raise _invalid(f"{path} must be at least {minimum}", path)
    return result


def _time(value: object) -> datetime:
    try: validate_timestamp(value, "$.as_of_utc")
    except LedgerError as error: raise _invalid(error.message, "$.as_of_utc") from error
    assert isinstance(value, str)
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _check(check_id: str, state: str, observed: object, threshold: object, unit: str, reason: str) -> dict[str, object]:
    if state not in RISK_STATEMENTS: raise _invalid("unknown risk state", check_id)
    return {"check_id": check_id, "state": state, "observed": observed, "threshold": threshold, "unit": unit, "reason": reason}


def _event(root: Path, request: RiskRequest, policy: RiskPolicyVersion, check: Mapping[str, object], timestamp: str) -> tuple[str, dict[str, object]]:
    event_id = f"risk-boundary-{request.request_id}-{check['check_id']}"
    ledger = root / "ledger" / "events.jsonl"
    if ledger.is_file():
        for line in ledger.read_bytes().splitlines():
            value: object = json.loads(line)
            if isinstance(value, dict) and value.get("event_id") == event_id: return str(value["event_hash"]), value
    trace = {"run_id": request.request_id, "phase": "risk-boundary", "boundary_state": check["state"], "duration_minutes": policy.rules["source"]["emergency_procedures"]["recovery_wait_minutes"],
             "reason": check["reason"], "affected_track": "paper_portfolio", "check_id": check["check_id"], "limit": check["threshold"]}
    material = {"request": {"correlation": request.correlation, "evidence_gate_state": request.evidence_gate_state, "risk_amount_usd": request.risk_amount_usd,
              "requested_leverage": request.requested_leverage, "requested_size_usd": request.requested_size_usd, "symbol": request.symbol},
              "policy_hash": policy.policy_hash, "check": dict(check)}
    event = EventRecord(event_id, timestamp,
                        request.actor, "snapshot.write", f"risk:{request.request_id}", sha256_digest(canonical_json(material)),
                        sha256_digest(canonical_json(trace)), "OK", None, trace)
    appended = append_event(event, regenerate_heads(root).events.head_hash, data_root=root)
    return appended.head_hash, dict(appended.record)


def _validate(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> tuple[dict[str, object], datetime]:
    if not isinstance(request, RiskRequest) or not isinstance(portfolio, PaperPortfolio) or not isinstance(policy, RiskPolicyVersion):
        raise _invalid("request, portfolio, and policy must use their typed contracts")
    if not request.request_id.strip() or not request.symbol.strip(): raise _invalid("request_id and symbol are required", "$.request")
    actor_mapping(request.actor); _time(portfolio.as_of_utc)
    for field in ("requested_size_usd", "requested_leverage", "risk_amount_usd", "correlation"): _number(getattr(request, field), f"$.request.{field}", minimum=0)
    for field in ("equity_usd", "peak_equity_usd"): _number(getattr(portfolio, field), f"$.portfolio.{field}", minimum=0)
    for field in ("daily_pnl_usd", "error_rate_percent", "loss_velocity_factor"): _number(getattr(portfolio, field), f"$.portfolio.{field}")
    for position in portfolio.positions: _number(position.notional_usd, "$.positions.notional_usd", minimum=0); _number(position.correlation, "$.positions.correlation", minimum=0); _invalid("position symbol must be non-empty", "$.positions.symbol") if not isinstance(position.symbol, str) or not position.symbol.strip() else None
    for field in ("consecutive_losses", "latency_ms", "consecutive_errors"):
        value = getattr(portfolio, field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0: raise _invalid(f"{field} must be a non-negative integer", f"$.portfolio.{field}")
    rules = policy.rules.get("source"); assert isinstance(rules, dict)
    return rules, _time(portfolio.as_of_utc)


def evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult:
    """Evaluate modeled paper boundaries without changing evidence-gate arithmetic."""
    rules, as_of = _validate(request, portfolio, policy)
    sizing = rules["position_sizing"]; correlation = rules["correlation_settings"]; breakers = rules["circuit_breakers"]; hours = rules["trading_hours"]
    assert isinstance(sizing, dict) and isinstance(correlation, dict) and isinstance(breakers, dict) and isinstance(hours, dict)
    drawdown = 0.0 if portfolio.peak_equity_usd == 0 else max(0.0, (portfolio.peak_equity_usd - portfolio.equity_usd) / portfolio.peak_equity_usd * 100)
    gross = sum(position.notional_usd for position in portfolio.positions) + request.requested_size_usd
    portfolio_leverage = gross / portfolio.equity_usd if portfolio.equity_usd else math.inf
    symbol_gross = sum(position.notional_usd for position in portfolio.positions if position.symbol == request.symbol) + request.requested_size_usd
    concentration_cap = portfolio.equity_usd * float(sizing["concentration_limit_percent"]) / 100
    checks = [
        _check("symbol.whitelist", "PASS" if request.symbol in rules["symbol_whitelist"] else "STOP", request.symbol, rules["symbol_whitelist"], "symbol", "symbol must be explicitly applicable"),
        _check("position.maximum", "PASS" if request.requested_size_usd <= float(rules["max_position_size"]) else "STOP", request.requested_size_usd, rules["max_position_size"], "USD", "hard paper-notional cap"),
        _check("leverage.request", "PASS" if request.requested_leverage <= float(rules["max_leverage"]) else "STOP", request.requested_leverage, rules["max_leverage"], "ratio", "hard request leverage cap"),
        _check("leverage.portfolio", "PASS" if portfolio_leverage <= float(rules["max_leverage"]) else "STOP", round(portfolio_leverage, 6), rules["max_leverage"], "ratio", "gross paper exposure divided by modeled equity"),
        _check("risk.per_trade", "PASS" if request.risk_amount_usd <= portfolio.equity_usd * float(rules["per_trade_risk_percent"]) / 100 else "STOP", request.risk_amount_usd, rules["per_trade_risk_percent"], "percent of equity", "single-request modeled loss cap"),
        _check("correlation.maximum", "PASS" if request.correlation <= float(correlation["max_correlation"]) else "HOLD", request.correlation, correlation["max_correlation"], "correlation", "highly correlated paper position is held"),
        _check("concentration.maximum", "PASS" if symbol_gross <= concentration_cap else "ADJUST", round(symbol_gross, 6), round(concentration_cap, 6), "USD", "one-symbol paper concentration cap"),
        _check("loss.daily_breaker", "PASS" if portfolio.daily_pnl_usd > float(breakers["daily_loss_usd"]) else "STOP", portfolio.daily_pnl_usd, breakers["daily_loss_usd"], "USD", "daily-loss circuit breaker"),
        _check("drawdown.breaker", "PASS" if drawdown <= float(rules["max_drawdown_percent"]) else ("QUARANTINE" if drawdown <= float(breakers["drawdown_percent"]) else "STOP"), round(drawdown, 6), breakers["drawdown_percent"], "percent", "drawdown operating boundary"),
        _check("losses.consecutive", "PASS" if portfolio.consecutive_losses < int(rules["max_consecutive_losses"]) else "QUARANTINE", portfolio.consecutive_losses, rules["max_consecutive_losses"], "count", "candidate-family loss streak boundary"),
        _check("latency.operating", "PASS" if portfolio.latency_ms <= int(breakers["latency_ms"]) else "HOLD", portfolio.latency_ms, breakers["latency_ms"], "ms", "stale-operation boundary"),
        _check("errors.rate", "PASS" if portfolio.error_rate_percent <= float(breakers["error_rate_percent"]) else "HOLD", portfolio.error_rate_percent, breakers["error_rate_percent"], "percent", "error-rate boundary"),
        _check("errors.consecutive", "PASS" if portfolio.consecutive_errors < int(breakers["consecutive_errors"]) else "STOP", portfolio.consecutive_errors, breakers["consecutive_errors"], "count", "repeated-error circuit breaker"),
        _check("loss.velocity", "PASS" if portfolio.loss_velocity_factor <= float(breakers["rapid_loss_velocity_factor"]) else "QUARANTINE", portfolio.loss_velocity_factor, breakers["rapid_loss_velocity_factor"], "ratio", "rapid-loss quarantine boundary"),
        _check("timing.restricted", "ADJUST" if as_of.hour in hours["restricted_hours_utc"] else "PASS", as_of.hour, hours["restricted_hours_utc"], "UTC hour", "restricted-hour liquidity adjustment"),
    ]
    approved = request.requested_size_usd
    if as_of.hour in hours["restricted_hours_utc"]: approved *= float(hours["low_liquidity_multiplier"])
    if symbol_gross > concentration_cap: approved = min(approved, max(0.0, concentration_cap - (symbol_gross - request.requested_size_usd)))
    states = {str(check["state"]) for check in checks}
    disposition = "STOP" if "STOP" in states else "QUARANTINE" if "QUARANTINE" in states else "HOLD" if "HOLD" in states else "CONTINUE"
    if disposition != "CONTINUE": approved = 0.0
    boundary = tuple(check for check in checks if check["state"] in ("HOLD", "QUARANTINE", "STOP"))
    root = data_root_path(None); heads: list[str] = []; events: list[dict[str, object]] = []
    for check in boundary:
        try: head, record = _event(root, request, policy, check, portfolio.as_of_utc)
        except LedgerError as error: raise _invalid(error.message, error.path or "$.event", "EVENT_APPEND_FAILED") from error
        heads.append(head); events.append(record)
    warnings = tuple(f"{check['check_id']}: {check['reason']}" for check in checks if check["state"] != "PASS")
    venue = policy.rules.get("venue_applicability"); assert isinstance(venue, dict)
    return RiskCheckResult(disposition, request.requested_size_usd, round(approved, 6), tuple(checks), warnings, policy.policy_id, policy.version, policy.policy_hash,
                           MappingProxyType(venue), request.evidence_gate_state, "MODELED", tuple(MappingProxyType(item) for item in events), tuple(heads), MappingProxyType(policy.trial_history_input))


__all__ = ["PaperPortfolio", "PaperPosition", "RISK_DISPOSITIONS", "RiskCheckResult", "RiskRequest", "evaluate_risk"]
