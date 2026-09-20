from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.data import EvidenceDescriptor, register_descriptor
from gauntlet.data.descriptors import descriptor_digest
from gauntlet.ledger import Actor, verify_chains
from gauntlet.model import ModelRegistryEntry, register_model
from gauntlet.model.adaptation import AdaptationFold, AdaptationManifest, AdaptationPolicy, AdaptationReplay, AdaptationSample, AdaptationWindow, ModelError, run_adaptation

OWNER = Actor("human", "owner")
CHECKPOINT = b"GAUNTLET-TINY-KRONOS-v1 checkpoint bytes"
REGISTERED_AT = "2026-01-02T00:00:00Z"
REQUESTED_AT = "2026-01-01T01:00:00Z"
POLICY = AdaptationPolicy(60, 4, 4, 2, 1, 1, True, "validation_only")


def at(minute: int) -> str: return datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
def samples(last_value: float = 360.0) -> tuple[AdaptationSample, ...]:
    rows = []
    for index in range(36):
        value = 100.0 + index + (12.5 if index == 35 else 0.0)
        target = None if index >= 30 else 0.02 if index % 3 == 0 else -0.01
        rows.append(AdaptationSample(f"bar-{index:02d}", at(index), at(index), {"value": value if index < 35 else last_value}, target, at(index + 2) if index < 30 else None))
    return tuple(rows)
def folds() -> tuple[AdaptationFold, ...]:
    first = AdaptationFold("fold-0001", 1, AdaptationWindow(at(0), at(11)), AdaptationWindow(at(13), at(16)), AdaptationWindow(at(17), at(20)), AdaptationWindow(at(30), at(35)), tuple(f"bar-{index:02d}" for index in range(10)), ("bar-13", "bar-14"), ("bar-17", "bar-18"), ("bar-30", "bar-31"))
    second = AdaptationFold("fold-0002", 2, AdaptationWindow(at(0), at(18)), AdaptationWindow(at(20), at(23)), AdaptationWindow(at(24), at(27)), AdaptationWindow(at(30), at(35)), tuple(f"bar-{index:02d}" for index in range(14)), ("bar-20", "bar-21"), ("bar-24", "bar-25"), ("bar-32", "bar-33"))
    return first, second


def model() -> object:
    architecture = {"name": "tiny-deterministic-kronos", "parameters": 8, "context_length": 8}
    entry = ModelRegistryEntry("kronos-tiny", 1, architecture, sha256_digest(canonical_json(architecture)), CHECKPOINT, {"start": "2025-01-01", "end": "2025-06-30"}, {"start": "2025-01-01", "end": "2025-12-31", "venue": "solana_dex"}, {"name": "MIT", "uri": "https://opensource.org/licenses/MIT"}, {"source": "local-owner-checkpoint", "lineage": "tiny-real-artifact"}, {"accelerator": "local-cpu", "precision": "float64"}, {"training": 11, "inference": 29}, b"GAUNTLET-TINY-KRONOS-v1 fine-tuned bytes", None, None, REGISTERED_AT, OWNER)
    return register_model(entry)
def dataset_descriptor(rows: tuple[AdaptationSample, ...], *, version: int = 1, supersedes: str | None = None) -> EvidenceDescriptor:
    content = canonical_json({"population": [row.mapping() for row in rows]})
    effective = "2026-01-01T00:00:00Z" if version == 1 else "2026-01-01T00:01:00Z"
    value = EvidenceDescriptor("gauntlet.evidence.v1", "kronos-adaptation-population", "kronos-adaptation-population.descriptor", version, "sha256:" + "0" * 64, supersedes, effective, None, "panel", "solana_dex", sha256_digest(content), {"collector": "adaptation-test", "uri_or_lineage": "local://synthetic-bars"}, "OBSERVED", {"start": at(0), "end_exclusive": at(36)}, {"watermark_at": effective, "max_age": "P36500D"}, {"state": "VALID", "checks": [{"name": "frozen-temporal-population", "status": "PASS"}]}, (), "GATE_CRITICAL", ("model.adaptation",), content, OWNER)
    return replace(value, descriptor_hash=descriptor_digest(value))
def manifest(descriptor_hash: str, content_hash: str, rows: tuple[AdaptationSample, ...] = samples(), policy: AdaptationPolicy = POLICY) -> AdaptationManifest:
    replay = AdaptationReplay("gauntlet@dfd217a", sha256_digest(b"dependency-lock"), sha256_digest(b"environment"), "gauntlet.model-normalization@v1", {"training": 71, "sampling": 29}, {"name": "hash-coupled", "temperature": 1.0, "top_k": 8, "deterministic": True})
    return AdaptationManifest("kronos-sol-adaptation", "solana_dex", REQUESTED_AT, rows, folds(), policy, replay, sha256_digest(canonical_json({"features": ["value"]})), sha256_digest(b"evidence-policy"), sha256_digest(b"resolved-config"), (descriptor_hash,), (content_hash,), {"learning_rates": [0.1, 0.01]}, OWNER)


@pytest.fixture(autouse=True)
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "gauntlet-data"
    monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root))
    return root


def adaptation_trials(root: Path) -> list[dict[str, object]]:
    ledger = root / "ledger" / "trials.jsonl"
    if not ledger.is_file():
        return []
    records = [json.loads(line) for line in ledger.read_bytes().splitlines()]
    return [record for record in records if record["payload"]["parameters"].get("adaptation")]


def test_real_frozen_adaptation_registers_first_and_replays_exactly(data_root: Path) -> None:
    registration = model()
    source = register_descriptor(dataset_descriptor(samples()))
    request = manifest(source.descriptor_hash, sha256_digest(source.content_path.read_bytes()))
    first = run_adaptation(request, registration)
    second = run_adaptation(request, registration)

    assert first.status == "OK" and first.gate_state == "PASS" and first.replayable
    assert first.run_hash == second.run_hash and second.replayed
    assert len(adaptation_trials(data_root)) == 1
    trial = adaptation_trials(data_root)[0]
    assert trial["trial_id"] == first.trial_id
    assert trial["recorded_at_utc"] == REQUESTED_AT
    assert trial["actor"] == {"kind": "human", "identity": "owner"}
    assert trial["payload"]["parameters"]["adaptation"]["manifest_hash"] == request.manifest_hash
    assert trial["payload"]["parameters"]["adaptation"]["model_fingerprint"] == registration.model_fingerprint

    report = json.loads(first.canonical_bytes)
    fingerprints = report["fingerprints"]
    assert fingerprints["manifest"] == request.manifest_hash
    assert fingerprints["population"] == request.population_hash
    assert fingerprints["split"] == report["fold_manifest"]["membership_hash"]
    assert fingerprints["model"] == registration.model_fingerprint
    assert fingerprints["feature"] == request.feature_manifest_hash
    assert fingerprints["policy"] == request.policy.policy_hash
    assert fingerprints["config"] == request.resolved_config_hash
    assert report["source_descriptor_hashes"] == [source.descriptor_hash]
    assert report["replay"]["code_version"] == "gauntlet@dfd217a"
    assert report["replay"]["dependency_lock_hash"] == sha256_digest(b"dependency-lock")
    assert report["replay"]["checkpoint"]["hash"] == sha256_digest(first.checkpoint_path.read_bytes())
    assert report["replay"]["seeds"] == {"training": 71, "sampling": 29}
    assert report["replay"]["sampler"]["deterministic"] is True
    assert report["replay"]["normalization_version"] == "gauntlet.model-normalization@v1"

    assert report["fold_manifest"]["fold_order"] == [1, 2]
    for fold, output in zip(request.folds, report["folds"], strict=True):
        locked = output["selection_lock"]
        assert locked["state"] == "LOCKED"
        assert locked["locked_at_boundary"] == fold.validation_window.end_utc
        assert locked["selection_input"] == "validation_only"
        assert locked["test_membership_digest_before_selection"] == sha256_digest(canonical_json(list(fold.test_membership)))
        assert output["normalization"]["uses_future"] is False
        assert output["normalization"]["bounds"]["end_utc"] <= fold.validation_window.start_utc
    assert report["checkpoint_selection"]["selection_input"] == "validation_only"
    assert report["checkpoint_selection"]["test_targets_read"] is False
    assert report["checkpoint_selection"]["prospective_targets_read"] is False
    assert all(log["actor"] == {"kind": "human", "identity": "owner"} for log in report["logs"])
    assert all(log["timestamp_utc"] and log["metric_inputs"] and log["reason"] for log in report["logs"])
    assert sha256_digest(first.checkpoint_path.read_bytes()) == first.checkpoint_hash
    assert verify_chains(data_root).valid


@pytest.mark.parametrize(
    ("kind", "code"),
    [
        ("target_crosses_train_boundary", "FOLD_BOUNDARY_LEAK"),
        ("feature_available_after_train_boundary", "FOLD_BOUNDARY_LEAK"),
        ("insufficient_embargo_purge_gap", "EMBARGO_PURGE_INVALID"),
        ("test_scoped_selection", "SELECTION_SCOPE_INVALID"),
    ],
)
def test_boundary_and_gap_leakage_fail_closed_before_trial(
    data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    code: str,
) -> None:
    registration = model()
    rows = samples()
    if kind == "target_crosses_train_boundary":
        rows = (*rows[:9], replace(rows[9], target_completed_at_utc=at(12)), *rows[10:])
    elif kind == "feature_available_after_train_boundary":
        rows = (*rows[:9], replace(rows[9], available_at_utc=at(16)), *rows[10:])
    policy = POLICY
    if kind == "insufficient_embargo_purge_gap":
        policy = AdaptationPolicy(60, 4, 4, 2, 3, 3, True, "validation_only")
    elif kind == "test_scoped_selection":
        policy = AdaptationPolicy(60, 4, 4, 2, 1, 1, True, "test")
    source = register_descriptor(dataset_descriptor(rows))
    request = manifest(source.descriptor_hash, sha256_digest(source.content_path.read_bytes()), rows, policy)
    source.content_path.chmod(0o600)

    with pytest.raises(ModelError) as rejection:
        run_adaptation(request, registration)
    assert rejection.value.code == code
    assert adaptation_trials(data_root) == []
    assert not (data_root / "model" / "adaptations").exists()
    assert verify_chains(data_root).valid


def test_replay_metadata_gap_rejects_without_artifact_or_trial(data_root: Path) -> None:
    registration = model()
    source = register_descriptor(dataset_descriptor(samples()))
    complete = manifest(source.descriptor_hash, sha256_digest(source.content_path.read_bytes()))
    for field, value in (
        ("code_version", ""),
        ("dependency_lock_hash", "not-a-digest"),
        ("environment_hash", None),
        ("normalization_version", ""),
        ("seeds", {}),
        ("sampler", {}),
    ):
        candidate = replace(complete, replay=replace(complete.replay, **{field: value}))
        with pytest.raises(ModelError) as rejection:
            run_adaptation(candidate, registration)
        assert rejection.value.code == "ADAPTATION_REPLAY_INCOMPLETE"
    assert adaptation_trials(data_root) == []
    assert not (data_root / "model" / "adaptations").exists()


def test_mutating_frozen_evaluation_population_creates_a_new_trial(data_root: Path) -> None:
    registration = model()
    first_source = register_descriptor(dataset_descriptor(samples()))
    first = run_adaptation(manifest(first_source.descriptor_hash, sha256_digest(first_source.content_path.read_bytes())), registration)
    original_descriptor = first_source.descriptor_path.read_bytes()
    original_content = first_source.content_path.read_bytes()
    original_run = first.artifact_path.read_bytes()

    changed_rows = samples(last_value=480.0)
    second_source = register_descriptor(
        dataset_descriptor(changed_rows, version=2, supersedes=first_source.descriptor_hash)
    )
    corrected = run_adaptation(manifest(second_source.descriptor_hash, sha256_digest(second_source.content_path.read_bytes()), changed_rows), registration)

    assert corrected.run_hash != first.run_hash
    assert corrected.trial_id != first.trial_id
    assert corrected.population_hash != first.population_hash
    trials = adaptation_trials(data_root)
    assert len(trials) == 2
    assert trials[1]["payload"]["parent_trial_ids"] == [first.trial_id]
    assert trials[1]["payload"]["parameters"]["adaptation"]["prior_population_hash"] == first.population_hash
    assert first_source.descriptor_path.read_bytes() == original_descriptor
    assert first_source.content_path.read_bytes() == original_content
    assert first.artifact_path.read_bytes() == original_run
    assert verify_chains(data_root).valid
