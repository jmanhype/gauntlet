from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.ledger import Actor, verify_chains
from gauntlet.model import (
    ContextObservation,
    FrozenContext,
    ModelProfile,
    ModelRegistryEntry,
    ModelError,
    register_model,
    run_inference,
)


OWNER = Actor("human", "owner")
CHECKPOINT = b"GAUNTLET-TINY-KRONOS-v1 checkpoint bytes"
REGISTERED_AT = "2026-01-02T00:00:00Z"
PREDICTION_AT = "2026-01-01T12:00:00Z"


def entry() -> ModelRegistryEntry:
    architecture = {"name": "tiny-deterministic-kronos", "parameters": 8, "context_length": 8}
    return ModelRegistryEntry("kronos-tiny", 1, architecture, sha256_digest(canonical_json(architecture)), CHECKPOINT, {"start": "2025-01-01", "end": "2025-06-30"}, {"start": "2025-01-01", "end": "2025-12-31", "venue": "solana_dex"}, {"name": "MIT", "uri": "https://opensource.org/licenses/MIT"}, {"source": "local-owner-checkpoint", "lineage": "tiny-real-artifact"}, {"accelerator": "local-cpu", "precision": "float64"}, {"training": 11, "inference": 29}, b"GAUNTLET-TINY-KRONOS-v1 fine-tuned bytes", None, None, REGISTERED_AT, OWNER)


def profile() -> ModelProfile:
    return ModelProfile("kronos-tiny-profile", sha256_digest(b"preprocessing-code"), sha256_digest(b"preprocessing-config"), 4, 29, 12, {"name": "hash-coupled", "temperature": 1.0, "top_k": 8, "deterministic": True})


def context() -> FrozenContext:
    rows = []
    for index in range(8):
        minute = f"{index:02d}"
        rows.append(ContextObservation(f"2026-01-01T11:{minute}:00Z", f"2026-01-01T11:{minute}:00Z", {"value": 100.0 + index}, "OBSERVED"))
    return FrozenContext("solana-test-context", PREDICTION_AT, "2026-01-01T11:00:00Z", "2026-01-01T11:07:00Z", tuple(rows))


@pytest.fixture(autouse=True)
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "gauntlet-data"
    monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root))
    return root


def test_registry_rejects_missing_lineage_before_storage(data_root: Path) -> None:
    invalid = {
        "base_checkpoint_bytes": b"",
        "architecture_config_hash": "not-a-digest",
        "training_window": {},
        "domain_window": {},
        "license": {},
        "provenance": {},
        "hardware": {},
        "seeds": {},
    }
    for field, value in invalid.items():
        with pytest.raises(ModelError) as rejection:
            register_model(replace(entry(), **{field: value}))
        assert rejection.value.code == "REGISTRY_INVALID"
        assert rejection.value.path == f"$.{field}"
    assert not (data_root / "descriptors").exists()
    assert not (data_root / "model").exists()


def test_fingerprint_is_stable_and_duplicate_checkpoint_lineage_is_preserved(data_root: Path) -> None:
    first = register_model(entry())
    second = register_model(replace(entry(), provenance={"source": "second-observation", "lineage": "changed"}))

    assert first.model_fingerprint == register_model(entry()).model_fingerprint
    assert first.model_fingerprint != second.model_fingerprint
    assert first.base_checkpoint_hash == second.base_checkpoint_hash
    assert first.base_checkpoint_path.read_bytes() == second.base_checkpoint_path.read_bytes() == CHECKPOINT
    assert first.descriptor_path != second.descriptor_path
    ledger = [json.loads(line) for line in (data_root / "ledger" / "trials.jsonl").read_bytes().splitlines()]
    model_trials = [record for record in ledger if record["payload"]["parameters"]["descriptor"]["kind"] == "model"]
    assert len(model_trials) == 2
    assert verify_chains(data_root).valid


def test_real_deterministic_inference_is_replayable_and_hash_verified(data_root: Path) -> None:
    model = register_model(entry())
    first = run_inference(context(), model, profile())
    second = run_inference(context(), model, profile())

    assert first.status == "OK" and first.replayable and first.gate_state == "PASS"
    assert first.artifact_hash == second.artifact_hash
    assert first.payload["outputs"] == second.payload["outputs"]
    assert second.replayed and second.artifact_path.read_bytes() == first.canonical_bytes
    assert first.model_fingerprint == model.model_fingerprint
    assert first.context_hash == context().context_hash

    report = json.loads(first.canonical_bytes)
    assert report["normalization"]["uses_future"] is False
    assert report["normalization"]["input_row_ids"] == ["row-04", "row-05", "row-06", "row-07"]
    selected = [104.0, 105.0, 106.0, 107.0]
    mean = sum(selected) / len(selected)
    assert report["normalization"]["statistics"]["mean"] == mean
    assert report["sampling"]["sample_count"] == 12
    assert report["replay"]["checkpoints"]["base"]["bytes_base64"]
    assert report["replay"]["preprocessing_code_hash"] == profile().preprocessing_code_hash
    assert report["replay"]["preprocessing_config_hash"] == profile().preprocessing_config_hash

    outputs = report["outputs"]
    assert len(outputs["paths"]) == 12
    assert all(path["observation_basis"] == "MODELED" for path in outputs["paths"])
    assert outputs["probabilities"]["up"]["observation_basis"] == "MODELED"
    assert outputs["probabilities"]["up"]["calibration"]["status"] == "PENDING"
    assert outputs["path_shares"]["policy"] == "EQUAL_SAMPLE_SHARE"
    assert abs(sum(item["share"] for item in outputs["path_shares"]["values"]) - 1.0) < 5e-12
    assert verify_chains(data_root).valid


@pytest.mark.parametrize("kind", ["future_feature", "late_available_feature", "future_target"])
def test_point_in_time_context_rejects_future_information(kind: str) -> None:
    if kind == "future_feature":
        rows = (*context().observations, ContextObservation("2026-01-01T12:01:00Z", "2026-01-01T12:01:00Z", {"value": 999.0}, "OBSERVED"))
        value = replace(context(), observations=rows)
    elif kind == "late_available_feature":
        rows = (*context().observations, ContextObservation("2026-01-01T11:08:00Z", "2026-01-01T12:01:00Z", {"value": 999.0}, "OBSERVED"))
        value = replace(context(), observations=rows, lookback_end_utc="2026-01-01T11:08:00Z")
    else:
        rows = (*context().observations[:-1], replace(context().observations[-1], target_value=1.0, target_completed_at_utc="2026-01-01T12:30:00Z"))
        value = replace(context(), observations=rows)

    with pytest.raises(ModelError) as rejection:
        run_inference(value, register_model(entry()), profile())
    assert rejection.value.code == "FUTURE_CONTEXT_REJECTED"


def test_missing_checkpoint_bytes_block_replay_without_model_output(data_root: Path) -> None:
    model = register_model(entry())
    model.base_checkpoint_path.unlink()
    blocked = run_inference(context(), model, profile())

    assert blocked.status == "BLOCKED"
    assert blocked.replayable is False
    assert blocked.gate_state == "BLOCKED"
    assert blocked.payload["outputs"]["paths"] == []
    assert blocked.payload["replay"]["status"] == "BLOCKED"
    assert blocked.payload["replay"]["checkpoints"]["base"]["bytes_base64"] is None
    assert blocked.event_record["status"] == "ERROR"
    assert verify_chains(data_root).valid
