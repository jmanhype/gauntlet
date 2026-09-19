from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from gauntlet.audit.collectors.bitquery import (
    BudgetContext,
    BudgetEvent,
    CollectorError,
    CollectorRequest,
    LedgerBudgetRecorder,
    collect_bitquery,
    derive_solana_tables,
)
from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.data.descriptors import load_descriptor_registry
from gauntlet.ledger import Actor, verify_chains

FIXTURE = Path(__file__).parent / "fixtures" / "bitquery_solana_pages.json"
OWNER = Actor("human", "integration-owner")


def use_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "gauntlet-data"; monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root)); return root


def bodies() -> list[bytes]:
    value = json.loads(FIXTURE.read_bytes()); return [canonical_json(item) for item in value["pages"]]


def recorder() -> tuple[list[BudgetEvent], dict[str, object]]:
    events: list[BudgetEvent] = []; calls: dict[str, object] = {"transports": 0, "retried": False}
    return events, calls


def transport(pages: list[bytes], calls: dict[str, object], *, retry_once: bool = False):
    def send(page) -> object:
        index = int(page.page_number) - 1; calls["transports"] = int(calls["transports"]) + 1
        if retry_once and index == 0 and not calls["retried"]:
            calls["retried"] = True
            from gauntlet.audit.collectors.bitquery import BitqueryTransportResponse
            return BitqueryTransportResponse(b"", status_code=429, retryable=True)
        from gauntlet.audit.collectors.bitquery import BitqueryTransportResponse
        body = pages[index]; terminal = index == len(pages) - 1
        return BitqueryTransportResponse(body, 200, None if terminal else f"cursor-{index + 2}", f"2026-01-01T00:0{index}:30Z", not terminal, sha256_digest(body))
    return send


def request(pages: list[bytes], calls: dict[str, object], run_id: str = "run-1", **overrides) -> CollectorRequest:
    retry_once = bool(overrides.pop("retry_once", False))
    values = {"query": {"network": "solana", "venue": "dex"}, "start_utc": "2026-01-01T00:00:00Z", "end_utc": "2026-01-01T00:02:00Z",
              "run_id": run_id, "observed_at_utc": "2026-01-01T00:02:00Z", "transport": overrides.pop("transport", transport(pages, calls, retry_once=retry_once)), "max_pages": 4, "backoff_base_seconds": 0.0}
    return CollectorRequest(**{**values, **overrides})  # type: ignore[arg-type]


def budget(events: list[BudgetEvent], **overrides) -> BudgetContext:
    values = {"family_limit_units": 10, "api_limit_units": 10, "event_recorder": events.append}
    return BudgetContext(**{**values, **overrides})  # type: ignore[arg-type]


def test_pagination_duplicates_budget_sanitization_and_atomic_derivation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = use_root(tmp_path, monkeypatch); events, calls = recorder(); pages = bodies()
    first = collect_bitquery(request(pages, calls), budget(events))
    assert first.status == "COMPLETE" and first.terminal_condition == "CURSOR_COMPLETE"
    assert [page.response_cursor for page in first.pages] == ["cursor-2", None]
    assert [page.watermark_utc for page in first.pages] == ["2026-01-01T00:00:30Z", "2026-01-01T00:01:30Z"]
    assert [page.terminal_condition for page in first.pages] == ["CURSOR_CONTINUE", "CURSOR_COMPLETE"]
    assert [event.phase for event in events] == ["pre_capture", "post_capture"] and all(event.status == "OK" for event in events)
    assert all("Bearer" not in canonical_json(event.mapping()).decode() for event in events)

    derived = derive_solana_tables(first.snapshot)
    assert derived.bars.artifact_id == "solana.bars" and derived.events.artifact_id == "solana.events"
    assert derived.bars_partition.name == "part-00000.parquet" and derived.bars_partition.read_bytes().startswith(b"PAR1")
    assert derived.events_partition.read_bytes().startswith(b"PAR1") and derived.complete_state_path.is_file()
    provenance = json.loads(canonical_json(derived.provenance).decode())
    assert provenance["partitions"]["solana.bars"]["hash"] == sha256_digest(derived.bars_partition.read_bytes())
    registry = load_descriptor_registry(root)
    assert {derived.bars.descriptor_hash, derived.events.descriptor_hash, first.snapshot.registration.descriptor_hash} <= set(registry)
    assert registry[derived.bars.descriptor_hash].value["dependencies"][0]["descriptor_hash"] == first.snapshot.registration.descriptor_hash
    assert verify_chains(root).valid

    second_events, second_calls = recorder(); redownload = collect_bitquery(request(pages, second_calls, run_id="run-2"), budget(second_events))
    assert redownload.status == "COMPLETE" and [page.duplicate_key for page in redownload.pages] == [page.duplicate_key for page in first.pages]
    assert second_calls["transports"] == 2
    observations = list((root / "raw" / "solana_dex").rglob("response.bin"))
    assert len(observations) == 4 and all(path.stat().st_size > 0 for path in observations)
    manifests = [json.loads(path.read_bytes()) for path in (root / "raw" / "solana_dex").rglob("page.json")]
    assert len({item["duplicate_key"] for item in manifests}) == 2 and len(manifests) == 4


def test_retry_and_live_endpoint_budget_and_secret_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_root(tmp_path, monkeypatch); events, calls = recorder(); result = collect_bitquery(request(bodies(), calls, retry_once=True), budget(events))
    assert result.pages[0].attempts == 2 and result.pages[0].transient_retries == 1 and result.pages[0].backoff_milliseconds == (0.0,)
    with pytest.raises(CollectorError) as blocked: collect_bitquery(request(bodies(), calls, transport=None), budget(events))  # type: ignore[arg-type]
    assert blocked.value.code == "LIVE_ENDPOINT_BLOCKED"
    exhausted, no_call = recorder(); values = {"family_limit_units": 1, "api_limit_units": 1, "event_recorder": exhausted.append}
    exhausted_result = collect_bitquery(request(bodies(), no_call, run_id="budget-run"), BudgetContext(**values))  # type: ignore[arg-type]
    assert exhausted_result.status == "QUARANTINED" and exhausted_result.failure is not None and exhausted_result.failure.code == "BUDGET_EXHAUSTED"
    assert no_call["transports"] == 1 and exhausted[-1].status == "ERROR"
    failed_events, failed_calls = recorder()
    def http_failure(page): return transport(bodies(), failed_calls)(page).__class__(b"", 400)
    raw_count = len(list((tmp_path / "gauntlet-data" / "raw").rglob("response.bin")))
    failed = collect_bitquery(request(bodies(), failed_calls, run_id="http-failed", transport=http_failure), budget(failed_events))
    assert failed.status == "FAILED" and failed.pages == () and failed.snapshot is None and failed.failure.code == "HTTP_FAILURE"
    assert failed_events[-1].status == "ERROR" and len(list((tmp_path / "gauntlet-data" / "raw").rglob("response.bin"))) == raw_count
    secret_query = {"network": "solana", "api_key": "not-allowed"}
    with pytest.raises(CollectorError) as secret: CollectorRequest(secret_query, "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z", "bad", "2026-01-01T00:01:00Z")
    assert secret.value.code == "SECRET_MATERIAL_REJECTED"


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda body: body.replace(b'"row_count":2', b'"row_count":3'), "MALFORMED_RESPONSE"),
        (lambda body: body[:3], "TRUNCATED_RESPONSE"),
        (lambda body: body, "CHECKSUM_FAILURE"),
        (lambda body: body, "CURSOR_REGRESSION"),
        (lambda body: body, "PARTIAL_CAPTURE"),
    ],
)
def test_integrity_failures_quarantine_without_overwriting_raw_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutate, code: str) -> None:
    root = use_root(tmp_path, monkeypatch); events, calls = recorder(); original = bodies(); pages = [mutate(item) for item in original]
    send = transport(pages, calls)
    if code == "CHECKSUM_FAILURE":
        def send(page): return transport(pages, calls)(page).__class__(pages[page.page_number - 1], 200, "cursor-2", "2026-01-01T00:00:30Z", False, sha256_digest(b"wrong"))
    elif code == "CURSOR_REGRESSION":
        def send(page): return transport(pages, calls)(page).__class__(pages[page.page_number - 1], 200, "cursor-2", "2026-01-01T00:00:30Z", True, sha256_digest(pages[page.page_number - 1]))
    kwargs = {"max_pages": 1} if code == "PARTIAL_CAPTURE" else {}
    if code in {"CHECKSUM_FAILURE", "CURSOR_REGRESSION"}: kwargs["transport"] = send
    result = collect_bitquery(request(pages, calls, **kwargs), budget(events))  # type: ignore[arg-type]
    assert result.status == "QUARANTINED" and result.failure is not None and result.failure.code == code
    assert result.snapshot is not None and result.snapshot.registration.content_path.is_file()
    descriptor = json.loads(result.snapshot.registration.descriptor_path.read_bytes())
    assert descriptor["quality"]["state"] == "QUARANTINED" and descriptor["quality"]["reason"]["code"] == code
    stored = next((root / "raw" / "solana_dex").rglob("response.bin")); assert stored.read_bytes() == pages[0]
    with pytest.raises(CollectorError) as derived_error: derive_solana_tables(result.snapshot)
    assert derived_error.value.code == "SNAPSHOT_QUARANTINED"


def test_ledger_budget_events_are_hash_chained_and_sanitized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = use_root(tmp_path, monkeypatch); event = BudgetEvent("pre_capture", "OK", "2026-01-01T00:00:00Z", "ledger-run", "1", "1", "10", "10", sha256_digest(b"snapshot"))
    LedgerBudgetRecorder(root, OWNER)(event)
    ledger = root / "ledger" / "events.jsonl"; value = json.loads(ledger.read_bytes())
    assert value["verb"] == "snapshot.write" and value["trace"]["budget_scope"] == ["family", "api"]
    assert b"Bearer" not in ledger.read_bytes() and verify_chains(root).valid
