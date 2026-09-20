from __future__ import annotations

import json; from dataclasses import FrozenInstanceError, replace; from pathlib import Path
import pytest
from gauntlet.config import ArtifactVersions, ConfigError, diff_config, resolve_config
from gauntlet.contracts.canonical import sha256_digest
from gauntlet.data import EvidenceDescriptor, register_descriptor
from gauntlet.data.descriptors import descriptor_digest
from gauntlet.ledger import Actor, verify_chains


PROFILE = 'schema_version = "1"\nprofile_id = "sol-momentum-v3"\nprofile_version = 1\n\n[values]\nvenue_track = "solana_dex"\ndata_start = "2025-01-01"\ndata_end = "2025-12-31"\nseed = 42\nlookback = 16\nhorizon = 12\nthreshold = 0.55\nfee_bps = 20\n'
OWNER = Actor("human", "owner"); SECRET = "sk-" + "x" * 24


def versions(policy: str = "policy@v1") -> ArtifactVersions:
    return ArtifactVersions("config-schema@v1", policy, "evidence@v1", "data@v1", "model@v7", "code@abc123", sha256_digest(b"dependency-lock"), sha256_digest(b"environment"))


def write_profile(root: Path, text: str = PROFILE) -> Path:
    path = root / "profile.toml"
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")
    return path


def config_descriptor(resolved: object, profile: Path) -> EvidenceDescriptor:
    effective = "2026-01-01T00:00:00Z"
    artifact_id = "resolved-config-vk-jkkn"
    value = EvidenceDescriptor("gauntlet.evidence.v1", artifact_id, f"{artifact_id}.descriptor", 1, "sha256:" + "0" * 64, None, effective, None, "config", "solana_dex", sha256_digest(resolved.canonical_bytes), {"collector": "config-resolver", "uri_or_lineage": profile.name}, "OBSERVED", {"resolved_config_hash": resolved.config_hash}, {"watermark_at": effective, "max_age": "P1D"}, {"state": "VALID", "checks": [{"name": "canonical-json", "status": "PASS"}]}, (), "GATE_CRITICAL", ("research.configuration",), resolved.canonical_bytes, OWNER)  # type: ignore[arg-type]
    return replace(value, descriptor_hash=descriptor_digest(value))


def test_real_profile_overrides_and_complete_canonical_hash(tmp_path: Path) -> None:
    profile = write_profile(tmp_path)
    first = resolve_config(profile, {"fee_bps": 25, "horizon": 8}, versions())
    second = resolve_config(profile, {"fee_bps": 25, "horizon": 8}, versions())

    assert first.config_hash == second.config_hash == sha256_digest(first.canonical_bytes) and first.canonical_bytes == second.canonical_bytes
    artifact = json.loads(first.canonical_bytes)
    assert artifact["values"]["fee_bps"] == 25 and artifact["values"]["horizon"] == 8
    assert artifact["overrides"] == {"fee_bps": 25, "horizon": 8}
    assert artifact["defaults"]["values"]["runtime.mode"] == "local-single-owner"
    assert artifact["provenance"]["fee_bps"]["source"] == "override"
    assert artifact["profile"]["content_hash"] == sha256_digest(profile.read_bytes())
    assert artifact["artifact_versions"] == versions().mapping()
    assert resolve_config(profile, {"fee_bps": 26}, versions()).config_hash != first.config_hash
    assert resolve_config(profile, {"fee_bps": 25, "horizon": 8}, versions("policy@v2")).config_hash != first.config_hash


def test_versioned_redaction_and_secret_refusal_are_fail_closed(tmp_path: Path) -> None:
    profile = write_profile(tmp_path, PROFILE + 'runtime_secret_name = "SOLANA_RPC_TOKEN"\n')
    resolved = resolve_config(profile, {}, versions())
    marker = resolved.artifact["values"]["runtime.secret_name"]
    assert marker == {"redacted": True, "rule_version": "gauntlet.redaction@v1", "kind": "secret_name"}
    assert resolved.artifact["redaction_rule"]["redacted_fields"] == ("runtime.data_root", "runtime.secret_name")
    assert b"SOLANA_RPC_TOKEN" not in resolved.canonical_bytes

    secret = write_profile(tmp_path / "secret.toml", PROFILE + 'api_key = "not-allowed"\n')
    with pytest.raises(ConfigError) as rejection: resolve_config(secret, {}, versions())
    assert rejection.value.code == "CONFIG_INVALID" and rejection.value.path == "$.values.api_key"
    with pytest.raises(ConfigError) as unknown: resolve_config(profile, {"unknown_threshold": 1}, versions())
    assert unknown.value.code == "CONFIG_INVALID" and unknown.value.path == "$.overrides.unknown_threshold"


@pytest.mark.parametrize("field", tuple(ArtifactVersions.__dataclass_fields__))
def test_secret_shaped_artifact_versions_are_rejected_before_emission(tmp_path: Path, field: str) -> None:
    with pytest.raises(ConfigError) as rejection: resolve_config(write_profile(tmp_path), {}, replace(versions(), **{field: SECRET}))
    assert rejection.value.code == "CONFIG_INVALID" and rejection.value.path == f"$.artifact_versions.{field}"


def test_secret_shaped_profile_metadata_and_override_are_rejected_before_emission(tmp_path: Path) -> None:
    profile = write_profile(tmp_path, PROFILE.replace('profile_id = "sol-momentum-v3"', f'profile_id = "{SECRET}"'))
    with pytest.raises(ConfigError) as rejection: resolve_config(profile, {}, versions())
    assert rejection.value.code == "CONFIG_INVALID" and rejection.value.path == "$.profile_id"
    with pytest.raises(ConfigError) as override: resolve_config(write_profile(tmp_path / "clean"), {"threshold": SECRET}, versions())
    assert override.value.code == "CONFIG_INVALID" and override.value.path == "$.overrides.threshold"


def test_missing_incomplete_and_malformed_inputs_reject_before_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "gauntlet-data"
    monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root))
    incomplete = write_profile(tmp_path / "incomplete.toml", PROFILE.replace('threshold = 0.55\n', ""))
    malformed = tmp_path / "malformed.toml"; malformed.write_bytes(b"\xff\xfe not-toml")
    bad_versions = replace(versions(), policy_version="")
    cases = ((incomplete, {}, versions()), (malformed, {}, versions()), (write_profile(tmp_path / "valid.toml"), {}, bad_versions))
    for candidate_profile, overrides, candidate_versions in cases:
        with pytest.raises(ConfigError) as rejection: resolve_config(candidate_profile, overrides, candidate_versions)
        assert rejection.value.code == "CONFIG_INVALID"
    assert not root.exists()


def test_diff_preserves_provenance_and_classifies_material_changes(tmp_path: Path) -> None:
    left_profile = write_profile(tmp_path / "left.toml")
    left = resolve_config(left_profile, {"threshold": 0.6, "horizon": 8}, versions())
    right = resolve_config(write_profile(tmp_path / "right.toml", PROFILE + 'runtime_secret_name = "TOKEN"\n'), {"threshold": 0.65}, versions("policy@v2"))
    diff = diff_config(left, right)

    by_key = {item.key: item for item in diff.changed}
    assert diff.left_hash == left.config_hash and diff.right_hash == right.config_hash
    threshold = by_key["values.threshold"]
    assert threshold.left.value == 0.6 and threshold.right.value == 0.65 and threshold.left.provenance.source == "override"
    assert threshold.threshold_bearing and not threshold.redacted
    assert by_key["artifact_versions.policy_version"].right.value == "policy@v2"
    assert [item.key for item in diff.removed] == ["overrides.horizon"]
    assert {item.key for item in diff.added} == {"values.runtime.secret_name"}
    assert {item.key for item in diff.redacted} == {"values.runtime.secret_name"}


def test_contract_registration_freezes_bytes_against_later_profile_edits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "gauntlet-data"
    monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root))
    profile = write_profile(tmp_path)
    resolved = resolve_config(profile, {"fee_bps": 25}, versions())
    original_bytes = resolved.canonical_bytes
    registration = register_descriptor(config_descriptor(resolved, profile))

    with pytest.raises(FrozenInstanceError): resolved.config_hash = "changed"  # type: ignore[misc]
    profile.write_text(PROFILE.replace("threshold = 0.55", "threshold = 0.75"), encoding="utf-8")
    later = resolve_config(profile, {"fee_bps": 25}, versions())
    assert later.config_hash != resolved.config_hash and resolved.canonical_bytes == original_bytes
    assert registration.content_path.read_bytes() == original_bytes
    assert registration.descriptor_path.is_file() and verify_chains(root).valid
