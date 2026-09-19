from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from gauntlet.contracts.canonical import CanonicalJSONError, canonical_json, sha256_digest
from gauntlet.contracts.manifests import ExclusiveCreationError, create_exclusive, verify_manifest
from gauntlet.contracts.schemas import validate

ZERO = "sha256:" + "0" * 64

def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()

def merkle_root(entries: list[dict[str, str]]) -> str:
    level = [hashlib.sha256(canonical_json(entry)).digest() for entry in entries]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return "sha256:" + level[0].hex()

def envelopes() -> dict[str, dict[str, Any]]:
    return {
        "gauntlet.evidence.v1": {"descriptor_schema": "gauntlet.evidence.v1", "artifact_id": "artifact-1", "descriptor_id": "descriptor-1", "descriptor_version": 1, "descriptor_hash": ZERO, "effective_at_utc": "2026-01-01T00:00:00Z", "kind": "bars", "venue_track": "solana_dex", "content_hash": ZERO, "source": {"collector": "test"}, "observation_basis": "OBSERVED", "coverage": {"start": "2026-01-01"}, "freshness": {"as_of": "2026-01-02"}, "quality": {"state": "VALID"}, "dependencies": [], "criticality": "GATE_CRITICAL", "downstream_metrics": []},
        "gauntlet.trial.v1": {"schema_version": "1", "entry_type": "trial.registered", "trial_id": "trial-1", "family_id": "family-1", "venue_track": "solana_dex", "recorded_at_utc": "2026-01-01T00:00:00Z", "actor": {"kind": "human", "identity": "owner"}, "payload_hash": ZERO, "previous_head_hash": ZERO, "entry_hash": ZERO, "payload": {}},
        "gauntlet.event.v1": {"event_id": "event-1", "schema_version": "1", "timestamp_utc": "2026-01-01T00:00:00Z", "actor": {"kind": "collector", "identity": "test"}, "verb": "dependency.evaluate", "subject": "artifact-1", "args_hash": ZERO, "output_hash": ZERO, "payload_hash": ZERO, "previous_head_hash": ZERO, "event_hash": ZERO, "status": "OK", "trace": {"run_id": "run-1"}},
        "gauntlet.policy.v1": {"schema_version": "1", "manifest_type": "policy", "policy_type": "evidence-policy", "policy_id": "policy-1", "version": 1, "creator": "owner", "created_at_utc": "2026-01-01T00:00:00Z", "changelog": ["initial"], "status": "active", "rules": {}, "content_hash": ZERO},
    }

def write_tree(root: Path) -> tuple[Path, bytes, bytes]:
    embedded = root / "evidence" / "payload.json"
    external = root / "external" / "reference.json"
    embedded.parent.mkdir(parents=True); external.parent.mkdir(parents=True)
    embedded.write_bytes(b'{"stable":true}'); external.write_bytes(b"reference")
    entries = [
        {"path": "evidence/payload.json", "hash": digest(embedded.read_bytes())},
        {"artifact_id": "external-1", "path": "external/reference.json", "hash": digest(external.read_bytes())},
    ]
    manifest = {
        "schema_version": "1", "manifest_type": "artifact-manifest", "artifact_id": "artifact-1",
        "created_at_utc": "2026-01-01T00:00:00Z", "files": entries[:1], "external_artifacts": entries[1:],
        "merkle_root": merkle_root(entries),
    }
    manifest_path = root / "manifest.json"; manifest_path.write_bytes(canonical_json(manifest))
    return manifest_path, embedded.read_bytes(), manifest_path.read_bytes()


def test_canonical_json_is_deterministic_and_fail_closed() -> None:
    first = {"z": [1, {"a": None}], "a": "é"}
    second = {"a": "é", "z": [1, {"a": None}]}
    expected = '{"a":"é","z":[1,{"a":null}]}'.encode("utf-8")
    assert canonical_json(first) == canonical_json(second) == expected
    with pytest.raises(CanonicalJSONError) as nan_error:
        canonical_json({"value": float("nan")})
    with pytest.raises(CanonicalJSONError) as key_error:
        canonical_json({1: "value"})
    assert nan_error.value.code == "NON_FINITE_NUMBER"
    assert key_error.value.code == "NON_STRING_OBJECT_KEY"


def test_digest_is_lowercase_and_exact_byte_bound() -> None:
    data = b"exact bytes"
    result = sha256_digest(data)
    assert result == digest(data) and len(result) == 71 and result.islower()
    assert result != sha256_digest(data + b"s")

def test_registered_envelopes_and_discriminators() -> None:
    valid = envelopes()
    assert all(validate(instance, schema_id).valid for schema_id, instance in valid.items())
    assert not validate(valid["gauntlet.evidence.v1"], "gauntlet.unknown.v1").valid
    invalid = [
        ("gauntlet.evidence.v1", valid["gauntlet.evidence.v1"] | {"kind": "unregistered"}),
        ("gauntlet.trial.v1", valid["gauntlet.trial.v1"] | {"entry_type": "trial.unknown"}),
        ("gauntlet.event.v1", valid["gauntlet.event.v1"] | {"verb": "unknown.evaluate"}),
        ("gauntlet.policy.v1", valid["gauntlet.policy.v1"] | {"policy_type": "unknown-policy"}),
        ("gauntlet.manifest.v1", {"schema_version": "1", "manifest_type": "unknown", "artifact_id": "x", "created_at_utc": "x", "files": [], "external_artifacts": [], "merkle_root": ZERO}),
    ]
    assert all(
        any(error.code == "UNKNOWN_DISCRIMINATOR" for error in validate(instance, schema_id).errors)
        for schema_id, instance in invalid
    )


def test_real_manifest_success_tamper_and_original_stability(tmp_path: Path) -> None:
    original = tmp_path / "original"; original.mkdir()
    manifest_path, embedded_bytes, manifest_bytes = write_tree(original)
    verified = verify_manifest(manifest_path, original)
    assert verified.valid and (verified.file_count, verified.external_count) == (1, 1)

    copy = tmp_path / "copy"; shutil.copytree(original, copy)
    payload = copy / "evidence" / "payload.json"
    changed = payload.read_bytes()
    payload.write_bytes(changed[:-1] + bytes([changed[-1] ^ 1]))
    tampered = verify_manifest(copy / "manifest.json", copy)
    assert not tampered.valid and tampered.failure is not None
    assert tampered.failure.code == "ARTIFACT_HASH_MISMATCH"
    assert verify_manifest(manifest_path, original).valid
    assert manifest_path.read_bytes() == manifest_bytes
    assert (original / "evidence" / "payload.json").read_bytes() == embedded_bytes


def test_manifest_integrity_failures_are_read_only_and_machine_readable(tmp_path: Path) -> None:
    root = tmp_path / "root"; root.mkdir()
    manifest_path, _, _ = write_tree(root); instance = json.loads(manifest_path.read_bytes())
    instance["files"][0]["hash"] = ZERO
    manifest_path.write_bytes(canonical_json(instance))
    before = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    mismatch = verify_manifest(manifest_path, root)
    assert not mismatch.valid and mismatch.failure is not None
    assert mismatch.failure.code == "ARTIFACT_HASH_MISMATCH"
    assert {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before

    (root / "evidence" / "payload.json").unlink()
    missing = verify_manifest(manifest_path, root)
    assert not missing.valid and missing.failure is not None and missing.failure.code == "ARTIFACT_MISSING"
    instance["files"][0]["path"] = "../escape.json"
    manifest_path.write_bytes(canonical_json(instance))
    escaping = verify_manifest(manifest_path, root)
    assert not escaping.valid and escaping.failure is not None
    assert escaping.failure.code == "SCHEMA_INVALID" and escaping.failure.path == "$.files[0].path"


def test_exclusive_create_refuses_nonempty_directory_and_existing_file(tmp_path: Path) -> None:
    directory = tmp_path / "output"; directory.mkdir()
    prior = directory / "prior.json"; prior.write_bytes(b"prior")
    with pytest.raises(ExclusiveCreationError) as directory_error:
        create_exclusive(directory, b"new")
    assert directory_error.value.code == "DESTINATION_NOT_EMPTY" and prior.read_bytes() == b"prior"
    immutable = tmp_path / "immutable.json"; immutable.write_bytes(b"immutable")
    with pytest.raises(ExclusiveCreationError) as file_error:
        create_exclusive(immutable, b"replacement")
    assert file_error.value.code == "ARTIFACT_EXISTS" and immutable.read_bytes() == b"immutable"
