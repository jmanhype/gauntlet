from __future__ import annotations

import ast
import base64
import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from gauntlet.contracts.canonical import sha256_digest
from gauntlet.ledger import Actor, verify_chains
from gauntlet.risk import OwnerAuthorizationRef, PaperPortfolio, PaperPosition, QTSSource, RiskError, RiskRequest, evaluate_risk, import_qts

ROOT = Path(__file__).resolve().parents[2]
SOURCE_BYTES = base64.b64decode("ewogICJtYXhfcG9zaXRpb25fc2l6ZSI6IDYyLjUwLAogICJtYXhfZGFpbHlfbG9zc191c2QiOiAxMDAsCiAgIm1heF9kcmF3ZG93bl9wZXJjZW50IjogNS4wLAogICJtYXhfY29uc2VjdXRpdmVfbG9zc2VzIjogMywKICAicGVyX3RyYWRlX3Jpc2tfcGVyY2VudCI6IDIuMCwKICAibWF4X2xldmVyYWdlIjogMy4wLAogICJzeW1ib2xfd2hpdGVsaXN0IjogWyJCVEMvVVNEVCIsICJFVEgvVVNEVCJdLAogICJjb3JyZWxhdGlvbl9zZXR0aW5ncyI6IHsKICAgICJtYXhfY29ycmVsYXRpb24iOiAwLjcsCiAgICAiY29ycmVsYXRpb25fd2luZG93X2RheXMiOiAzMCwKICAgICJtaW5fY29ycmVsYXRpb25fb2JzZXJ2YXRpb25zIjogMjAKICB9LAogICJwb3NpdGlvbl9zaXppbmciOiB7CiAgICAia2VsbHlfZnJhY3Rpb25fc2FmZXR5IjogMC4yNSwKICAgICJ2b2xhdGlsaXR5X2FkanVzdG1lbnQiOiB0cnVlLAogICAgInRhcmdldF92b2xhdGlsaXR5IjogMC4xNSwKICAgICJjb25jZW50cmF0aW9uX2xpbWl0X3BlcmNlbnQiOiAyNS4wLAogICAgImF0cl9tdWx0aXBsaWVyIjogMi4wCiAgfSwKICAiY2lyY3VpdF9icmVha2VycyI6IHsKICAgICJkYWlseV9sb3NzX3VzZCI6IC0xMDAsCiAgICAiZHJhd2Rvd25fcGVyY2VudCI6IDEwLjAsCiAgICAibGF0ZW5jeV9tcyI6IDEwMDAsCiAgICAiZXJyb3JfcmF0ZV9wZXJjZW50IjogNS4wLAogICAgImNvbnNlY3V0aXZlX2Vycm9ycyI6IDMsCiAgICAicmFwaWRfbG9zc192ZWxvY2l0eV9mYWN0b3IiOiAwLjUKICB9LAogICJ0cmFkaW5nX2hvdXJzIjogewogICAgInJlc3RyaWN0ZWRfaG91cnNfdXRjIjogWzMsIDQsIDUsIDZdLAogICAgImxvd19saXF1aWRpdHlfbXVsdGlwbGllciI6IDAuNQogIH0sCiAgImVtZXJnZW5jeV9wcm9jZWR1cmVzIjogewogICAgImF1dG9fbGlxdWlkYXRlX29uX2NyaXRpY2FsIjogZmFsc2UsCiAgICAicG9zaXRpb25fcmVkdWN0aW9uX2ZhY3RvciI6IDAuNSwKICAgICJyZWNvdmVyeV93YWl0X21pbnV0ZXMiOiAxNQogIH0sCiAgInBlcmZvcm1hbmNlX3RhcmdldHMiOiB7CiAgICAibWluX3NoYXJwZV9yYXRpbyI6IDEuMCwKICAgICJtYXhfYWNjZXB0YWJsZV9kcmF3ZG93biI6IDAuMTUsCiAgICAidGFyZ2V0X3dpbl9yYXRlIjogMC41NSwKICAgICJtaW5fcHJvZml0X2ZhY3RvciI6IDEuMgogIH0KfQ==")
OWNER = Actor("human", "owner")
AUTH = OwnerAuthorizationRef(OWNER, "qts-risk-owner-2026-09-18", sha256_digest(b"owner-authorized-qts-risk-2026-09-18"), "2026-09-18T23:00:00Z")


def source(path: Path) -> QTSSource:
    return QTSSource(path, "solana-dex-forecasting/multi-agent-system", "config/risk.json", sha256_digest(path.read_bytes()), "2026-09-18T23:00:00Z")


def request(state: str = "PASS", size: float = 50, correlation: float = 0.2) -> RiskRequest:
    return RiskRequest("risk-001", OWNER, "BTC/USDT", size, 1.0, 10.0, correlation, state)


def portfolio(**overrides: object) -> PaperPortfolio:
    value = PaperPortfolio("2026-09-18T04:00:00Z", 1000.0, 1000.0, 0.0)
    return replace(value, **overrides) if overrides else value


@pytest.fixture(autouse=True)
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "gauntlet-data"; monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root)); return root


@pytest.fixture
def qts_path(tmp_path: Path) -> Path:
    path = tmp_path / "qts-risk.json"; path.write_bytes(SOURCE_BYTES); return path


def test_import_binds_exact_qts_bytes_lineage_authorization_and_trial_input(qts_path: Path) -> None:
    policy = import_qts(source(qts_path), AUTH)
    assert policy.policy_id == "qts.risk" and policy.version == 1 and policy.status == "active"
    assert policy.payload["lineage"]["source"]["content_hash"] == sha256_digest(SOURCE_BYTES)
    assert policy.payload["lineage"]["authorization"]["authorization_hash"] == AUTH.authorization_hash
    units = policy.rules["units"]; scopes = policy.rules["scopes"]; semantics = policy.rules["semantics"]
    assert set(units) == set(scopes) == set(semantics) == set(policy.payload["lineage"]["original_to_gauntlet"])
    trial = policy.trial_history_input
    assert trial["policy_hash"] == policy.policy_hash and trial["requires_new_trial_on_change"] is True
    changed = qts_path.with_suffix(".changed.json"); changed.write_bytes(SOURCE_BYTES.replace(b"62.50", b"62.51"))
    with pytest.raises(RiskError): import_qts(source(changed), AUTH)
    with pytest.raises(RiskError): import_qts(source(qts_path), OwnerAuthorizationRef(OWNER, "wrong", AUTH.authorization_hash, AUTH.authorized_at_utc))


def test_safe_modeled_request_adjusts_restricted_hour_without_curing_evidence_fail(qts_path: Path) -> None:
    result = evaluate_risk(request("FAIL"), portfolio(), import_qts(source(qts_path), AUTH))
    by_id = {check["check_id"]: check for check in result.checks}
    assert result.disposition == "CONTINUE" and result.approved_size_usd == 25
    assert by_id["timing.restricted"]["state"] == "ADJUST" and result.evidence_gate_state == "FAIL"
    assert result.observation_basis == "MODELED" and result.boundary_events == ()


def test_concentration_boundary_reduces_size_to_paper_cap(qts_path: Path) -> None:
    held = (PaperPosition("BTC/USDT", 240.0, 0.2),)
    result = evaluate_risk(request(), portfolio(positions=held), import_qts(source(qts_path), AUTH))
    assert result.disposition == "CONTINUE" and result.approved_size_usd == 10
    concentration = next(check for check in result.checks if check["check_id"] == "concentration.maximum")
    assert concentration["state"] == "ADJUST" and concentration["threshold"] == 250.0


@pytest.mark.parametrize(("field", "value", "disposition"), (("daily_pnl_usd", -120.0, "STOP"), ("latency_ms", 2000, "HOLD"), ("consecutive_losses", 3, "QUARANTINE")))
def test_risk_boundary_appends_event_and_cannot_be_overridden_by_evidence_pass(data_root: Path, qts_path: Path, field: str, value: object, disposition: str) -> None:
    result = evaluate_risk(request("PASS"), portfolio(**{field: value}), import_qts(source(qts_path), AUTH))
    assert result.disposition == disposition and result.approved_size_usd == 0 and result.evidence_gate_state == "PASS"
    assert len(result.boundary_events) == len(result.event_head_hashes) == 1
    event = result.boundary_events[0]; trace = event["trace"]
    assert event["actor"] == {"kind": "human", "identity": "owner"} and event["timestamp_utc"] == "2026-09-18T04:00:00Z"
    assert event["verb"] == "snapshot.write" and trace["boundary_state"] == disposition
    assert trace["duration_minutes"] == 15 and trace["affected_track"] == "paper_portfolio"
    assert verify_chains(data_root).valid


def test_risk_kernel_has_no_order_or_real_money_interface() -> None:
    tree = ast.parse(inspect.getsource(evaluate_risk))
    calls = {node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "") for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not calls & {"submit_order", "place_order", "send_order", "authorize_real_money"}
    assert "real_money_authorized" not in inspect.getsource(evaluate_risk)
