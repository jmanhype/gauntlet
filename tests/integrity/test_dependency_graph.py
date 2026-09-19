from __future__ import annotations

import json, pytest
from dataclasses import replace
from datetime import datetime, timezone; from pathlib import Path; from typing import Any

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.data import CHECK_ORDER, QuarantineReason, evaluate_dependencies, quarantine_descriptor, register_descriptor
from gauntlet.data.descriptors import DescriptorError, EvidenceDescriptor, descriptor_digest
from gauntlet.ledger import Actor, verify_chains
from gauntlet.ledger._common import ZERO_DIGEST
OWNER = Actor("human", "integration-owner"); POLICY_HASH = sha256_digest(b'{"criticality_version":1}'); UTC = timezone.utc
def at(minutes: int) -> str: return datetime(2026, 1, 1, 10, minutes, tzinfo=UTC).isoformat().replace("+00:00", "Z")
def when(minutes: int) -> datetime: return datetime(2026, 1, 1, 10, minutes, tzinfo=UTC)
def descriptor(artifact_id: str, effective_minute: int, *, content: bytes, dependencies: tuple[dict[str, str], ...] = (), criticality: str = "GATE_CRITICAL", observation_basis: str = "OBSERVED", quality_state: str = "VALID", downstream_metrics: tuple[str, ...] = ("core.metric",), max_age: str = "P1D", version: int = 1, supersedes: str | None = None) -> EvidenceDescriptor:
    value = EvidenceDescriptor(
        descriptor_schema="gauntlet.evidence.v1", artifact_id=artifact_id, descriptor_id=f"{artifact_id}.descriptor", descriptor_version=version,
        descriptor_hash=ZERO_DIGEST, supersedes_descriptor_hash=supersedes, effective_at_utc=at(effective_minute), superseded_at_utc=None,
        kind="panel", venue_track="solana_dex", content_hash=sha256_digest(content), source={"collector": "integration-test", "uri_or_lineage": f"memory://{artifact_id}"},
        observation_basis=observation_basis, coverage={"start": "2025-12-01", "end_exclusive": "2026-01-01"},
        freshness={"watermark_at": at(effective_minute), "max_age": max_age, "as_of": at(effective_minute)},
        quality={"state": quality_state, "checks": [{"name": "row-count", "status": "PASS"}]}, dependencies=dependencies,
        criticality=criticality, downstream_metrics=downstream_metrics, content_bytes=content, actor=OWNER,
    )
    return replace(value, descriptor_hash=descriptor_digest(value))
def read_descriptor(root: Path, digest: str) -> dict[str, Any]:
    return json.loads((root / "descriptors" / f"{digest}.json").read_bytes())
def use_temporary_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "gauntlet-data"; monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root))
    return root
def test_registration_validates_schema_hashes_dependencies_and_ledgers_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = use_temporary_root(tmp_path, monkeypatch)
    leaf = register_descriptor(descriptor("leaf", 0, content=b"leaf-bytes"))
    assert leaf.descriptor_version == 1 and leaf.descriptor_path.is_file() and leaf.content_path.is_file()
    assert verify_chains(root).valid and leaf.ledger_path.read_bytes().count(b"\n") == 1
    record = json.loads(leaf.ledger_path.read_bytes())
    assert record["trial_id"] == leaf.trial_id
    assert record["payload"]["parameters"]["descriptor"]["descriptor_hash"] == leaf.descriptor_hash
    assert read_descriptor(root, leaf.descriptor_hash)["descriptor_hash"] == leaf.descriptor_hash

    bad_kind = replace(descriptor("bad-kind", 1, content=b"bad"), kind="unknown")
    mismatch = replace(descriptor("bad-hash", 2, content=b"hash"), descriptor_hash=ZERO_DIGEST)
    content_mismatch = replace(descriptor("bad-content", 3, content=b"actual"), content_hash=sha256_digest(b"declared"))
    unknown_dependency = descriptor("bad-dependency", 4, content=b"dependency", dependencies=({"artifact_id": "ghost", "relation": "requires"},))
    for candidate in (bad_kind, mismatch, content_mismatch, unknown_dependency):
        with pytest.raises(DescriptorError) as rejection:
            register_descriptor(candidate)
        assert rejection.value.code in {"SCHEMA_INVALID", "DESCRIPTOR_HASH_MISMATCH", "CONTENT_HASH_MISMATCH", "DEPENDENCY_UNREGISTERED"}
    assert leaf.ledger_path.read_bytes().count(b"\n") == 1
    assert list((root / "descriptors").glob("*.json")) == [leaf.descriptor_path]
def test_real_multilevel_closure_time_travel_and_append_only_quarantine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = use_temporary_root(tmp_path, monkeypatch)
    leaf = register_descriptor(descriptor("leaf", 0, content=b"leaf-v1"))
    middle = register_descriptor(descriptor("middle", 1, content=b"middle", dependencies=({"artifact_id": "leaf", "relation": "requires"},)))
    root_descriptor = register_descriptor(descriptor("root", 2, content=b"root", dependencies=({"artifact_id": "middle", "relation": "requires"},)))
    original_leaf_bytes = leaf.descriptor_path.read_bytes()
    original_leaf_content = leaf.content_path.read_bytes()
    historical = evaluate_dependencies(["root.descriptor"], when(3), POLICY_HASH, {"core.metric"})
    assert historical.status == "OK" and historical.coverage == 1.0
    assert historical.metric_states == {"core.metric": "VALID"}
    assert set(historical.selected_descriptor_hashes) == {leaf.descriptor_hash, middle.descriptor_hash, root_descriptor.descriptor_hash}
    assert historical.graph_hash == evaluate_dependencies(["root.descriptor"], when(3), POLICY_HASH, {"core.metric"}).graph_hash
    assert historical.findings == () and not historical.quarantined

    quarantined = quarantine_descriptor(leaf.descriptor_hash, QuarantineReason("CHECKSUM_FAILURE", "source bytes failed collection checksum", ("leaf",)), OWNER)
    later = datetime.fromisoformat(read_descriptor(root, quarantined.descriptor_hash)["effective_at_utc"].replace("Z", "+00:00"))
    assert quarantined.descriptor_version == 2
    assert quarantined.descriptor_hash != leaf.descriptor_hash
    replacement = read_descriptor(root, quarantined.descriptor_hash)
    assert replacement["supersedes_descriptor_hash"] == leaf.descriptor_hash
    assert replacement["quality"]["state"] == "QUARANTINED"
    assert replacement["quality"]["reason"]["code"] == "CHECKSUM_FAILURE"
    assert leaf.descriptor_path.read_bytes() == original_leaf_bytes
    assert leaf.content_path.read_bytes() == original_leaf_content
    assert verify_chains(root).valid and root_descriptor.ledger_path.read_bytes().count(b"\n") == 4
    before = evaluate_dependencies(["root.descriptor"], when(3), POLICY_HASH, {"core.metric"})
    assert before.status == "OK" and leaf.descriptor_hash in before.selected_descriptor_hashes
    assert quarantined.descriptor_hash not in before.selected_descriptor_hashes
    after = evaluate_dependencies(["root.descriptor"], later, POLICY_HASH, {"core.metric"})
    assert after.status == "BLOCKED" and after.metric_states == {"core.metric": "INVALID"}
    assert after.quarantined and leaf.descriptor_hash not in after.selected_descriptor_hashes
    assert any(finding.code == "QUALITY_QUARANTINED" for finding in after.findings)
    exact = evaluate_dependencies([root_descriptor.descriptor_hash], later, POLICY_HASH, {"core.metric"})
    assert root_descriptor.descriptor_hash in exact.selected_descriptor_hashes
    assert exact.status == "BLOCKED" and quarantined.descriptor_hash in exact.selected_descriptor_hashes
def test_noncritical_gap_degrades_coverage_without_invalidating_unaffected_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = use_temporary_root(tmp_path, monkeypatch)
    optional = register_descriptor(descriptor("optional", 0, content=b"optional", criticality="NON_CRITICAL", quality_state="INCOMPLETE", downstream_metrics=("optional.metric",)))
    parent = register_descriptor(descriptor("parent", 1, content=b"parent", dependencies=({"artifact_id": "optional", "relation": "requires"},), downstream_metrics=("core.metric",)))
    result = evaluate_dependencies(["parent.descriptor"], when(2), POLICY_HASH, {"core.metric", "optional.metric"})
    assert result.status == "DEGRADED" and result.coverage == 0.5
    assert result.metric_states == {"core.metric": "VALID", "optional.metric": "DEGRADED"}
    assert result.affected_metrics == ("optional.metric",)
    assert set(result.selected_descriptor_hashes) == {optional.descriptor_hash, parent.descriptor_hash}
    assert any(finding.code == "QUALITY_INCOMPLETE" and finding.criticality == "NON_CRITICAL" for finding in result.findings)
    assert [CHECK_ORDER.index(finding.check) for finding in result.findings] == sorted(CHECK_ORDER.index(finding.check) for finding in result.findings)
def test_wide_graph_propagates_deep_gate_critical_failure_to_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_temporary_root(tmp_path, monkeypatch)
    deep = register_descriptor(descriptor("deep", 0, content=b"deep", quality_state="INCOMPLETE"))
    fillers = [register_descriptor(descriptor(f"filler-{index}", 1, content=f"filler-{index}".encode(), downstream_metrics=("filler.metric",))) for index in range(4)]
    dependencies = tuple({"artifact_id": item.artifact_id, "relation": "requires"} for item in (deep, *fillers))
    wide = register_descriptor(descriptor("wide", 2, content=b"wide", dependencies=dependencies))
    root = register_descriptor(descriptor("root", 3, content=b"root", dependencies=({"artifact_id": "wide", "relation": "requires"},)))
    result = evaluate_dependencies(["root.descriptor"], when(4), POLICY_HASH, {"core.metric", "filler.metric"})
    propagated = {finding.descriptor_hash for finding in result.findings if finding.code == "QUALITY_INCOMPLETE"}
    assert result.status == "BLOCKED" and result.metric_states == {"core.metric": "INVALID", "filler.metric": "VALID"}
    assert result.affected_metrics == ("core.metric",) and result.coverage == 0.5
    assert {deep.descriptor_hash, wide.descriptor_hash, root.descriptor_hash} <= propagated
    assert len(result.selected_descriptor_hashes) == 7 and result.findings == tuple(sorted(result.findings, key=lambda finding: CHECK_ORDER.index(finding.check)))

@pytest.mark.parametrize(
    ("kwargs", "code", "check"),
    [({"criticality": "UNKNOWN"}, "CRITICALITY_UNKNOWN", CHECK_ORDER[6]), ({"observation_basis": "MODELED"}, "OBSERVATION_BASIS_INVALID", CHECK_ORDER[5]), ({"max_age": "PT1M"}, "FRESHNESS_STALE", CHECK_ORDER[2]), ({"quality_state": "INCOMPLETE"}, "QUALITY_INCOMPLETE", CHECK_ORDER[3])],
)
def test_gate_critical_failures_block_dependent_metric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kwargs: dict[str, Any], code: str, check: str) -> None:
    use_temporary_root(tmp_path, monkeypatch)
    registered = register_descriptor(descriptor("blocked", 0, content=b"blocked", **kwargs))
    result = evaluate_dependencies(["blocked.descriptor"], when(30), POLICY_HASH, {"core.metric"})
    assert result.status == "BLOCKED" and result.coverage == 0.0
    assert result.metric_states == {"core.metric": "INVALID"} and result.affected_metrics == ("core.metric",)
    assert any(finding.code == code and finding.check == check for finding in result.findings)
    assert registered.descriptor_hash in result.selected_descriptor_hashes
def test_missing_gate_critical_input_blocks_all_required_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_temporary_root(tmp_path, monkeypatch)
    result = evaluate_dependencies(["ghost.descriptor"], when(1), POLICY_HASH, {"core.metric", "external.claim"})
    assert result.status == "BLOCKED" and result.coverage == 0.0
    assert result.metric_states == {"core.metric": "INVALID", "external.claim": "INVALID"}
    assert result.selected_descriptor_hashes == () and any(finding.code == "DEPENDENCY_MISSING" for finding in result.findings)
def test_corrupt_or_malformed_registry_fails_closed_without_crashing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = use_temporary_root(tmp_path, monkeypatch)
    registered = register_descriptor(descriptor("corrupt", 0, content=b"immutable"))
    evaluate_dependencies(["corrupt.descriptor"], when(1), POLICY_HASH, {"core.metric"})
    registered.content_path.chmod(0o600)
    registered.content_path.write_bytes(b"tampered")
    corrupt = evaluate_dependencies(["corrupt.descriptor"], when(1), POLICY_HASH, {"core.metric"})
    assert corrupt.status == "BLOCKED" and corrupt.metric_states == {"core.metric": "INVALID"}
    assert any(finding.code == "REPLAY_FAILED" for finding in corrupt.findings)
    monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(tmp_path / "malformed-root"))
    malformed = register_descriptor(descriptor("malformed", 1, content=b"malformed"))
    malformed.descriptor_path.chmod(0o600)
    tampered = json.loads(malformed.descriptor_path.read_bytes())
    tampered["dependencies"] = [{"artifact_id": "cyclic", "relation": "unknown"}]
    malformed.descriptor_path.write_bytes(canonical_json(tampered))
    graph_result = evaluate_dependencies(["malformed.descriptor"], when(2), POLICY_HASH, {"core.metric"})
    assert graph_result.status == "GRAPH_MALFORMED" and graph_result.metric_states == {"core.metric": "INVALID"}
    assert graph_result.findings[0].code == "GRAPH_MALFORMED"
