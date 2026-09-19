from __future__ import annotations
import json
import shutil
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import pytest
from gauntlet.contracts.canonical import canonical_json
from gauntlet.ledger import Actor, EventRecord, TrialPayload, append_event, append_trial, regenerate_heads, verify_chains
from gauntlet.ledger._common import LedgerError, ZERO_DIGEST
OWNER = Actor("human", "owner")
COLLECTOR = Actor("collector", "integration-test")
TRIAL_KEYS = {"schema_version", "entry_type", "trial_id", "family_id", "venue_track", "recorded_at_utc", "actor", "payload_hash", "previous_head_hash", "entry_hash", "payload"}
EVENT_KEYS = {"event_id", "schema_version", "timestamp_utc", "actor", "verb", "subject", "args_hash", "output_hash", "payload_hash", "previous_head_hash", "event_hash", "status", "error_class", "trace"}
_TRIAL_VALUES: dict[str, object] = {
    "family_id": "family-1", "venue_track": "solana_dex", "recorded_at_utc": "2026-01-01T00:00:00Z",
    "hypothesis": "Momentum survives realistic execution costs", "success_interpretation": "Out-of-sample profit after adverse scenarios",
    "failure_interpretation": "Evidence does not meet the registered threshold", "strategy_family": "cross_venue_momentum", "parent_trial_ids": (),
    "transfer_hypothesis": None, "data_window": {"start": "2025-01-01", "end": "2025-12-31"}, "split_manifest_hash": ZERO_DIGEST,
    "source_descriptor_hashes": (ZERO_DIGEST,), "frozen": True, "feature_manifest_hash": ZERO_DIGEST, "preprocessing_hash": ZERO_DIGEST,
    "parameters": {"lookback": 16}, "search_space": {"lookback": [8, 16, 32]}, "execution_assumptions": {"next_bar_entry": True},
    "adverse_scenarios": ({"name": "latency", "multiplier": 2.0},), "benchmark_identity": "solana-dex-buy-and-hold", "benchmark_role": "reference",
    "budgets": {"trials": 10, "compute": 100, "data": 1000}, "stop_condition": {"condition": "budget_or_evidence_failure"},
    "axis_control": {"mode": "one-axis", "declaration": "lookback", "attribution_plan": "per-axis isolation"},
    "policy_versions": {"policy": "1", "risk": "1", "evaluation": "1"}, "resolved_config_hash": ZERO_DIGEST,
    "dependencies": ({"descriptor": ZERO_DIGEST, "criticality": "GATE_CRITICAL"},), "criticality": "GATE_CRITICAL",
}
def trial_payload(trial_id: str = "trial-1") -> TrialPayload:
    return TrialPayload(trial_id=trial_id, **_TRIAL_VALUES)  # type: ignore[arg-type]
def event_record(event_id: str, status: str = "OK") -> EventRecord:
    output = ZERO_DIGEST if status == "ERROR" else "sha256:" + "a" * 64
    error = "SOURCE_DESCRIPTOR_MISSING" if status == "ERROR" else None
    return EventRecord(event_id, "2026-01-01T00:01:00Z", COLLECTOR, "trial.register", "trial-1", ZERO_DIGEST, output, status, error, {"run_id": "run-1", "span_id": "span-1"})
def child_append_trial(root: str, trial_id: str, previous_head: str | None) -> str:
    result = append_trial(trial_payload(trial_id), OWNER, previous_head, data_root=Path(root))
    return result.head_hash
def child_read_and_append(root: str, trial_id: str) -> str:
    state = regenerate_heads(Path(root))
    return child_append_trial(root, trial_id, state.trials.head_hash)
def test_complete_trial_appends_once_with_exact_envelope_and_head_range(tmp_path: Path) -> None:
    result = append_trial(trial_payload(), OWNER, None, data_root=tmp_path)
    assert set(result.record) == TRIAL_KEYS
    assert result.record["entry_type"] == "trial.registered"
    assert result.record["previous_head_hash"] == ZERO_DIGEST
    assert result.byte_start == 0 and result.byte_end == result.ledger_path.stat().st_size
    assert result.head_path == tmp_path / "ledger" / "trial-head.json"
    assert result.ledger_path.read_bytes().endswith(b"\n")
    assert canonical_json(dict(result.record)) + b"\n" == result.ledger_path.read_bytes()
    head = json.loads(result.head_path.read_bytes())
    assert head == {"schema_version": "1", "chain": "trials", "head_hash": result.head_hash, "entry_count": 1, "byte_start": 0, "byte_end": result.byte_end}
    verification = verify_chains(tmp_path)
    assert verification.valid and verification.trials.head_hash == result.head_hash
    trial_bytes, trial_head_bytes = result.ledger_path.read_bytes(), result.head_path.read_bytes()
    success = append_event(event_record("event-success"), None, data_root=tmp_path)
    failure = append_event(event_record("event-failure", "ERROR"), success.head_hash, data_root=tmp_path)
    assert set(success.record) == EVENT_KEYS and success.record["status"] == "OK" and success.record["error_class"] is None
    assert failure.record["status"] == "ERROR" and failure.record["error_class"] == "SOURCE_DESCRIPTOR_MISSING"
    assert failure.record["output_hash"] == ZERO_DIGEST and failure.record["previous_head_hash"] == success.head_hash
    assert result.ledger_path.read_bytes() == trial_bytes and result.head_path.read_bytes() == trial_head_bytes
    heads = {result.head_path: result.head_path.read_bytes(), failure.head_path: failure.head_path.read_bytes()}
    for path in heads:
        path.unlink()
    regenerated = regenerate_heads(tmp_path)
    assert regenerated.trials.head_hash == result.head_hash and regenerated.events.head_hash == failure.head_hash
    assert all(path.read_bytes() == original_bytes for path, original_bytes in heads.items()) and verify_chains(tmp_path).valid
def test_append_sequence_extends_after_a_new_process_reads_prior_head(tmp_path: Path) -> None:
    first = append_trial(trial_payload("trial-1"), OWNER, None, data_root=tmp_path)
    with ProcessPoolExecutor(max_workers=1) as executor:
        second_head = executor.submit(child_read_and_append, str(tmp_path), "trial-2").result()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(child_append_trial, str(tmp_path), trial_id, second_head) for trial_id in ("trial-a", "trial-b")]
        outcomes = [future.result() if future.exception() is None else future.exception() for future in futures]
    assert sum(isinstance(value, str) for value in outcomes) == 1
    failures = [value for value in outcomes if isinstance(value, LedgerError)]
    assert len(failures) == 1 and failures[0].code == "LEDGER_CONFLICT"
    verification = verify_chains(tmp_path)
    assert verification.valid and verification.trials.entry_count == 3 and verification.trials.head_hash != first.head_hash
def test_malformed_inputs_and_secret_material_fail_before_writes(tmp_path: Path) -> None:
    incomplete = replace(trial_payload(), hypothesis="")
    with pytest.raises(LedgerError) as payload_error:
        append_trial(incomplete, OWNER, None, data_root=tmp_path)
    assert payload_error.value.code == "TRIAL_PAYLOAD_INVALID"
    secret_payload = replace(trial_payload(), parameters={"lookback": 16, "api_key": "not-in-ledger"})
    with pytest.raises(LedgerError) as trial_secret_error:
        append_trial(secret_payload, OWNER, None, data_root=tmp_path)
    assert trial_secret_error.value.code == "SECRET_MATERIAL_REJECTED"
    secret_event = EventRecord("bad-event", "2026-01-01T00:00:00Z", OWNER, "trial.register", "trial-1", ZERO_DIGEST, ZERO_DIGEST, "ERROR", "TEST", {"run_id": "run-1", "authorization": "Bearer not-in-ledger"})
    with pytest.raises(LedgerError) as event_secret_error:
        append_event(secret_event, None, data_root=tmp_path)
    assert event_secret_error.value.code == "SECRET_MATERIAL_REJECTED"
    for field, value, code in (
        ("status", "INVALID", "STATUS_INVALID"),
        ("output_hash", "sha256:" + "a" * 64, "EVENT_ERROR_INVALID"),
        ("trace", {"span_id": "span-1"}, "TRACE_INVALID"),
    ):
        with pytest.raises(LedgerError) as shape_error:
            append_event(replace(event_record("invalid-shape", "ERROR"), **{field: value}), None)
        assert shape_error.value.code == code
    assert not (tmp_path / "ledger").exists()
def test_stale_or_malformed_previous_head_refuses_append_without_mutation(tmp_path: Path) -> None:
    first = append_trial(trial_payload("trial-1"), OWNER, None, data_root=tmp_path)
    before = first.ledger_path.read_bytes()
    with pytest.raises(LedgerError) as stale_error:
        append_trial(trial_payload("trial-stale"), OWNER, None, data_root=tmp_path)
    assert stale_error.value.code == "LEDGER_CONFLICT" and first.ledger_path.read_bytes() == before
    with pytest.raises(LedgerError) as conflict_error:
        append_trial(trial_payload("trial-conflict"), OWNER, ZERO_DIGEST, data_root=tmp_path)
    assert conflict_error.value.code == "LEDGER_CONFLICT"
    with pytest.raises(LedgerError) as digest_error:
        append_trial(trial_payload("trial-bad-prev"), OWNER, "not-a-digest", data_root=tmp_path)
    assert digest_error.value.code == "DIGEST_INVALID"
    assert first.ledger_path.read_bytes() == before
def test_byte_edit_delete_and_reorder_fail_for_both_chains_while_original_stays_valid(tmp_path: Path) -> None:
    original = tmp_path / "original"
    original.mkdir()
    append_trial(trial_payload("trial-1"), OWNER, None, data_root=original)
    append_trial(trial_payload("trial-2"), OWNER, regenerate_heads(original).trials.head_hash, data_root=original)
    append_event(event_record("event-1"), None, data_root=original)
    append_event(event_record("event-2"), regenerate_heads(original).events.head_hash, data_root=original)
    assert verify_chains(original).valid
    for chain, ledger_name in (("trials", "trials.jsonl"), ("events", "events.jsonl")):
        for mode in ("byte-edit", "delete", "reorder"):
            copy = tmp_path / f"{chain}-{mode}"
            shutil.copytree(original, copy)
            target = copy / "ledger" / ledger_name
            copied = target.read_bytes().splitlines(keepends=True)
            if mode == "byte-edit":
                copied[0] = bytes(bytearray(copied[0][:-2]) + bytes([copied[0][-2] ^ 1]) + copied[0][-1:])
            elif mode == "delete":
                copied.pop(0)
            else:
                copied[0], copied[1] = copied[1], copied[0]
            target.write_bytes(b"".join(copied))
            tampered = verify_chains(copy)
            assert not tampered.valid and tampered.failure is not None
            assert tampered.failure.code in {"JSON_INVALID", "CANONICAL_INVALID", "PAYLOAD_HASH_MISMATCH", "PREVIOUS_HEAD_MISMATCH"}
            assert verify_chains(original).valid
