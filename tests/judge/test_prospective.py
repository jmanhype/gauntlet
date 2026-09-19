from __future__ import annotations

import json, shutil
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import pytest

from gauntlet.config.resolver import ArtifactVersions, ResolvedConfig, resolve_config
from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.data.descriptors import EvidenceDescriptor, descriptor_digest, register_descriptor
from gauntlet.judge import ProspectiveDependency, ProspectiveDependencySnapshot, ProspectiveError, ProspectiveOutcome, ProspectiveSignal, append_signal, resolve_outcome, verify_prospective
from gauntlet.ledger import Actor, verify_chains
from gauntlet.ledger._common import ZERO_DIGEST

OWNER = Actor("human", "prospective-owner"); START = datetime(2026, 1, 2, 10, tzinfo=timezone.utc); UTC = timezone.utc


def z(minutes: float = 0) -> str:
    return datetime.fromtimestamp(START.timestamp() + minutes * 60, UTC).isoformat().replace("+00:00", "Z")


def resolved_config(tmp_path: Path) -> ResolvedConfig:
    profile = tmp_path / "prospective-profile.toml"
    profile.write_text('schema_version = "1"\nprofile_id = "prospective"\nprofile_version = 1\n[values]\nvenue_track = "solana_dex"\ndata_start = "2026-01-01"\ndata_end = "2026-01-03"\nseed = 11\nlookback = 2\nhorizon = 2\nthreshold = 0.5\nfee_bps = 10\n', encoding="utf-8")
    return resolve_config(profile, {}, ArtifactVersions(*(["1"] * 6), sha256_digest(b"schemas"), sha256_digest(b"environment")))


def dependency(artifact_id: str, basis: str, content: bytes) -> EvidenceDescriptor:
    value = EvidenceDescriptor("gauntlet.evidence.v1", artifact_id, f"{artifact_id}.descriptor", 1, ZERO_DIGEST, None, z(-30), None, "panel", "solana_dex", sha256_digest(content), {"collector": "integration-test", "uri_or_lineage": f"gauntlet://test/{artifact_id}"}, basis, {"start_utc": z(-30), "end_exclusive_utc": z(30)}, {"watermark_at": z(-1), "max_age": "P1D"}, {"state": "VALID", "checks": [{"name": "present", "status": "PASS"}]}, (), "GATE_CRITICAL", ("judge.prospective",), content, OWNER)
    return replace(value, descriptor_hash=descriptor_digest(value))


def snapshot(root: Path) -> ProspectiveDependencySnapshot:
    registered = [register_descriptor(dependency("observed-state", "OBSERVED", b"observed-bytes")), register_descriptor(dependency("modeled-feature", "MODELED", b"modeled-bytes"))]
    assert root.joinpath("descriptors").is_dir()
    return ProspectiveDependencySnapshot("DEGRADED", (ProspectiveDependency(registered[0].descriptor_hash, "observed-state", "OBSERVED", "VALID", z(-1)), ProspectiveDependency(registered[1].descriptor_hash, "modeled-feature", "MODELED", "VALID", z(-1))))


def signal(config: ResolvedConfig, dependencies: ProspectiveDependencySnapshot, *, recorded: str = "2026-01-02T10:00:01Z", signal_id: str = "signal-1") -> ProspectiveSignal:
    return ProspectiveSignal(signal_id, z(), recorded, z(5), "solana_dex", "SOL", sha256_digest(b"candidate"), sha256_digest(b"model"), config, sha256_digest(b"policy"), {"features": {"momentum": 0.2, "available_at_utc": z()}}, "BUY", 100.0, 5, 300, {"fee_bps": 10, "entry": "next_bar"}, 0.72, 0.18, "P_POSITIVE_RETURN_AFTER_COST_V1", dependencies, OWNER, "awaiting completed outcome")


def outcome(record_id: str, status: str = "RESOLVED", minutes: float = 6, reason: str = "venue state completed the horizon") -> ProspectiveOutcome:
    state: Mapping[str, object] = {"venue": "solana_dex", "pool": "pool-1", "mark_price": 101, "state_available_at_utc": z(minutes)} if status == "RESOLVED" else {}
    return ProspectiveOutcome(record_id, status, OWNER, reason, z(minutes), state, sha256_digest(canonical_json(state)), 0.01 if status == "RESOLVED" else None, "OBSERVED" if status == "RESOLVED" else "MODELED", ())


@pytest.fixture
def scene(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "gauntlet-data"; monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root)); config = resolved_config(tmp_path); return root, config, snapshot(root)


def test_real_signal_and_later_outcome_are_hash_chained_without_mutation(scene) -> None:
    root, config, dependencies = scene
    result = append_signal(signal(config, dependencies))
    signal_bytes = result.signal_path.read_bytes(); signal_envelope = json.loads(signal_bytes)
    assert result.record_id == "signal-1" and result.status == "OPEN" and result.classification == "PROSPECTIVE" and result.eligible_for_prospective_gate_credit
    assert result.signal_hash == signal_envelope["signal_hash"] and result.signal_hash != ZERO_DIGEST
    assert result.mapping()["fingerprints"] == {"candidate": sha256_digest(b"candidate"), "model": sha256_digest(b"model"), "config": config.config_hash, "policy": sha256_digest(b"policy")}
    assert result.mapping()["action"] == {"intended": "BUY", "notional": 100.0, "horizon_bars": 5, "horizon_seconds": 300, "execution_assumptions": {"fee_bps": 10, "entry": "next_bar"}}
    assert result.mapping()["confidence"] == {"value": 0.72, "path_share": 0.18, "semantics": "P_POSITIVE_RETURN_AFTER_COST_V1"}
    assert result.mapping()["dependency_snapshot"]["values"][0]["observation_basis"] == "OBSERVED" and result.mapping()["dependency_snapshot"]["values"][1]["observation_basis"] == "MODELED"
    assert result.status_history == ({"from": None, "to": "OPEN", "actor": {"kind": "human", "identity": "prospective-owner"}, "reason": "awaiting completed outcome", "timestamp_utc": "2026-01-02T10:00:01Z"},)
    resolved = resolve_outcome("signal-1", outcome("signal-1"))
    assert resolved.status == "RESOLVED" and [item["to"] for item in resolved.status_history] == ["OPEN", "RESOLVED"] and resolved.outcome_path.read_bytes().count(b"\n") == 1
    assert all(all(key in item for key in ("actor", "reason", "timestamp_utc")) for item in resolved.status_history)
    assert resolved.signal_path.read_bytes() == signal_bytes and verify_prospective(root).valid and verify_chains(root).valid and (root / "ledger" / "events.jsonl").read_bytes().count(b"\n") == 2
    with pytest.raises(ProspectiveError) as rejection: resolve_outcome("signal-1", outcome("signal-1"))
    assert rejection.value.code == "TRANSITION_EXISTS" and resolved.signal_path.read_bytes() == signal_bytes


def test_late_and_nonresolved_transitions_are_classified_and_terminal(scene) -> None:
    root, config, dependencies = scene; late = append_signal(signal(config, dependencies, recorded=z(6), signal_id="late"))
    assert late.classification == "HISTORICAL" and not late.eligible_for_prospective_gate_credit and json.loads(late.signal_path.read_bytes())["classification"] == "HISTORICAL"
    late_resolved = resolve_outcome("late", outcome("late")); assert not late_resolved.eligible_for_prospective_gate_credit
    for index, status in enumerate(("SKIPPED", "EXECUTION_FAILED"), 2):
        record = append_signal(signal(config, dependencies, recorded=f"2026-01-02T10:00:0{index}Z", signal_id=f"signal-{index}")); moved = resolve_outcome(record.record_id, outcome(record.record_id, status, index, f"owner skipped {index}" if status == "SKIPPED" else "quote unavailable"))
        assert moved.status == status and len(moved.status_history) == 2 and moved.status_history[-1]["reason"] == ("owner skipped 2" if status == "SKIPPED" else "quote unavailable")
        with pytest.raises(ProspectiveError) as rejection: resolve_outcome(record.record_id, outcome(record.record_id, "RESOLVED", 7))
        assert rejection.value.code == "TRANSITION_TERMINAL"
    assert verify_prospective(root).valid and (root / "prospective" / "signals.jsonl").read_bytes().count(b"\n") == 3


def test_unknown_dependencies_and_schema_fail_closed_before_writes(scene) -> None:
    root, config, dependencies = scene; ghost = replace(dependencies.entries[0], descriptor_hash=sha256_digest(b"ghost"))
    with pytest.raises(ProspectiveError) as rejection: append_signal(signal(config, replace(dependencies, entries=(ghost, dependencies.entries[1]))))
    assert rejection.value.code == "DEPENDENCY_UNREGISTERED" and not (root / "prospective").exists()
    bad = replace(signal(config, dependencies), model_fingerprint="not-a-digest")
    with pytest.raises(ProspectiveError) as fingerprint_error: append_signal(bad)
    assert fingerprint_error.value.code == "FINGERPRINT_INVALID" and not (root / "prospective").exists()
    bad_outcome = replace(outcome("signal-1", "RESOLVED"), venue_state_hash=sha256_digest(b"different"))
    with pytest.raises(ProspectiveError) as outcome_error: resolve_outcome("signal-1", bad_outcome)
    assert outcome_error.value.code == "OUTCOME_NOT_FOUND" and not (root / "prospective").exists()


def test_byte_tampering_in_either_append_only_history_is_detected(scene) -> None:
    root, config, dependencies = scene; append_signal(signal(config, dependencies)); resolve_outcome("signal-1", outcome("signal-1")); assert verify_prospective(root).valid
    for name, field in (("signals", "signal_hash"), ("outcomes", "outcome_hash")):
        copy = root.parent / f"tampered-{name}"; shutil.copytree(root, copy); target = copy / "prospective" / f"{name}.jsonl"; target.chmod(0o600); lines = target.read_bytes().splitlines(keepends=True); value = json.loads(lines[0]); value[field] = ZERO_DIGEST; lines[0] = canonical_json(value) + b"\n"; target.write_bytes(b"".join(lines))
        verification = verify_prospective(copy)
        assert not verification.valid and verification.failure is not None and verification.failure.code in {"ENTRY_HASH_MISMATCH", "PREVIOUS_HEAD_MISMATCH"}
