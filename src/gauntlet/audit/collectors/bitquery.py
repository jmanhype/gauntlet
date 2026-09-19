"""Offline, immutable Bitquery Solana snapshot and derivation contracts."""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from gauntlet.contracts.canonical import CanonicalJSONError, canonical_json, sha256_digest
from gauntlet.contracts.manifests import create_exclusive
from gauntlet.data.descriptors import DescriptorRegistration, EvidenceDescriptor, descriptor_digest, descriptor_mapping, load_descriptor_registry, validate_descriptor
from gauntlet.ledger import Actor, EventRecord, append_event, regenerate_heads
from gauntlet.ledger._common import ZERO_DIGEST, data_root_path

COLLECTOR_IDENTITY = "bitquery-solana-v1"
TRANSFORM_IDENTITY = "bitquery-solana-transform-v1"
RESPONSE_SCHEMA = "bitquery.solana-snapshot.v1"
_SECRET_PARTS = ("password", "secret", "credential", "private", "token", "authorization", "bearer", "api_key", "apikey")
_RETRYABLE = frozenset((408, 425, 429, 500, 502, 503, 504))
_NO_PAYLOAD_FAILURES = frozenset(("TRANSPORT_FAILURE", "RETRY_LIMIT_EXCEEDED", "HTTP_FAILURE"))
_ROW_FIELDS = frozenset(("time_utc", "pair", "event_type", "base_amount", "quote_amount", "price", "tx_hash", "log_index"))


class CollectorError(RuntimeError):
    def __init__(self, code: str, message: str, details: Mapping[str, object] | None = None) -> None:
        super().__init__(message); self.code = code; self.message = message; self.details = dict(details or {})


class CollectionIntegrityError(CollectorError):
    """A response or derived row violated immutable collection integrity."""


class TransientTransportError(RuntimeError):
    def __init__(self, status_code: int = 0) -> None:
        super().__init__(f"transport transient failure ({status_code})"); self.status_code = status_code


@dataclass(frozen=True)
class BitqueryPageRequest:
    cursor: str | None; normalized_request: str; page_number: int


@dataclass(frozen=True)
class BitqueryTransportResponse:
    body: bytes; status_code: int = 200; cursor: str | None = None; watermark_utc: str | None = None
    has_more: bool = False; declared_content_hash: str | None = None; cost_units: Decimal | int | str = 1
    retryable: bool = False


@dataclass(frozen=True)
class CollectorRequest:
    query: Mapping[str, object]; start_utc: str; end_utc: str; run_id: str; observed_at_utc: str
    transport: Callable[[BitqueryPageRequest], BitqueryTransportResponse] | None = None; max_pages: int = 10; initial_cursor: str | None = None; per_page_cost_units: Decimal | int | str = 1
    estimated_cost_units: Decimal | int | str = 1; retry_limit: int = 3; backoff_base_seconds: float = 0.0; backoff_cap_seconds: float = 30.0
    max_age: str = "P7D"; sleeper: Callable[[float], None] = time.sleep; data_root: Path | None = None
    actor: Actor = Actor("collector", COLLECTOR_IDENTITY)

    def __post_init__(self) -> None:
        if not isinstance(self.query, Mapping): raise CollectorError("REQUEST_INVALID", "query must be an object")
        _reject_secrets(self.query, "$.query")
        if not isinstance(self.run_id, str): raise CollectorError("REQUEST_INVALID", "run_id must be a string")
        if not self.run_id.strip(): raise CollectorError("REQUEST_INVALID", "run_id must be non-empty")
        for name in ("start_utc", "end_utc", "observed_at_utc"): _timestamp(getattr(self, name), f"$.{name}")
        if _parse_time(self.end_utc) <= _parse_time(self.start_utc): raise CollectorError("REQUEST_INVALID", "end_utc must follow start_utc")
        if isinstance(self.max_pages, bool) or not isinstance(self.max_pages, int) or self.max_pages < 1: raise CollectorError("REQUEST_INVALID", "max_pages must be a positive integer")
        if isinstance(self.retry_limit, bool) or not isinstance(self.retry_limit, int) or self.retry_limit < 0: raise CollectorError("REQUEST_INVALID", "retry_limit must be a non-negative integer")
        _number(self.per_page_cost_units, "$.per_page_cost_units"); _number(self.estimated_cost_units, "$.estimated_cost_units")
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0 for value in (self.backoff_base_seconds, self.backoff_cap_seconds)): raise CollectorError("REQUEST_INVALID", "backoff bounds must be non-negative numbers")
        if self.backoff_cap_seconds < self.backoff_base_seconds: raise CollectorError("REQUEST_INVALID", "backoff_cap_seconds cannot precede backoff_base_seconds")
        if self.data_root is not None and self.data_root.resolve() != data_root_path(None).resolve(): raise CollectorError("REQUEST_INVALID", "explicit data_root must match the configured registry root")
        actor_mapping_safe(self.actor)
        frozen = _freeze(self.query)
        try: encoded = canonical_json(frozen)
        except (CanonicalJSONError, TypeError, ValueError) as error: raise CollectorError("REQUEST_INVALID", "query must be canonical JSON data") from error
        object.__setattr__(self, "query", frozen)
        object.__setattr__(self, "_normalized", sha256_digest(encoded))

    @property
    def normalized_request_hash(self) -> str:
        return str(self._normalized)  # type: ignore[attr-defined]


@dataclass(frozen=True)
class BudgetEvent:
    phase: str; status: str; timestamp_utc: str; run_id: str; family_spent_units: str; api_spent_units: str
    family_limit_units: str; api_limit_units: str; snapshot_hash: str = ZERO_DIGEST
    def mapping(self) -> dict[str, object]:
        value = {name: getattr(self, name) for name in self.__dataclass_fields__}
        _reject_secrets(value, "$.budget_event"); return value


def actor_mapping_safe(actor: Actor) -> None:
    value = {"kind": actor.kind, "identity": actor.identity}
    _reject_secrets(value, "$.actor")
    if actor.kind not in {"human", "agent", "collector"} or not actor.identity.strip(): raise CollectorError("ACTOR_INVALID", "actor is not registered")


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value): raise CollectorError("REQUEST_INVALID", "query object keys must be strings")
        return {key: _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class LedgerBudgetRecorder:
    data_root: Path | None = None; actor: Actor = Actor("collector", COLLECTOR_IDENTITY)
    def __call__(self, event: BudgetEvent) -> str:
        safe = event.mapping(); actor_mapping_safe(self.actor); chain = regenerate_heads(data_root_path(self.data_root)); previous = chain.events.head_hash
        failure = event.status == "ERROR"
        record = EventRecord(
            f"bitquery-budget-{event.phase}-{chain.events.entry_count}-{event.run_id}", event.timestamp_utc, self.actor, "snapshot.write", f"bitquery:{event.run_id}",
            sha256_digest(canonical_json(safe)), ZERO_DIGEST if failure else event.snapshot_hash, "ERROR" if failure else "OK",
            "BUDGET_REJECTED" if failure else None, {"run_id": event.run_id, "capture_phase": event.phase, "budget_scope": ["family", "api"]},
        )
        return append_event(record, previous, data_root=self.data_root).head_hash


@dataclass(frozen=True)
class BudgetContext:
    family_limit_units: Decimal | int | str; api_limit_units: Decimal | int | str; family_spent_units: Decimal | int | str = 0
    api_spent_units: Decimal | int | str = 0; authorized: bool = True; event_recorder: Callable[[BudgetEvent], object] | None = None

    def __post_init__(self) -> None:
        if self.event_recorder is None: raise CollectorError("BUDGET_EVENT_RECORDER_REQUIRED", "pre/post capture budget events are mandatory")

    def units(self, value: Decimal | int | str, path: str) -> Decimal:
        return _number(value, path)

    def authorize(self, units: Decimal, request: CollectorRequest) -> None:
        limits = (self.units(self.family_limit_units, "$.family_limit_units") - self.units(self.family_spent_units, "$.family_spent_units"),
                  self.units(self.api_limit_units, "$.api_limit_units") - self.units(self.api_spent_units, "$.api_spent_units"))
        event = lambda status: BudgetEvent("pre_capture", status, request.observed_at_utc, request.run_id, str(self.family_spent_units), str(self.api_spent_units), str(self.family_limit_units), str(self.api_limit_units))
        if not self.authorized or units > limits[0] or units > limits[1]:
            self.event_recorder(event("ERROR")); raise CollectorError("BUDGET_UNAUTHORIZED" if not self.authorized else "BUDGET_EXHAUSTED", "capture is not authorized within the family/API budget", {"requested_units": str(units)})


@dataclass(frozen=True)
class CapturedPage:
    page_number: int; request_cursor: str | None; response_cursor: str | None; watermark_utc: str; content_hash: str
    duplicate_key: str; body_path: str; terminal_condition: str; attempts: int; transient_retries: int
    backoff_milliseconds: tuple[float, ...]; quality_state: str = "VALID"; failure_code: str | None = None


@dataclass(frozen=True)
class CaptureFailure:
    code: str; message: str; path: str; page_number: int | None


@dataclass(frozen=True)
class SnapshotDescriptor:
    registration: DescriptorRegistration; manifest: Mapping[str, object]


@dataclass(frozen=True)
class CaptureResult:
    status: str; run_id: str; normalized_request_hash: str; watermark_utc: str; terminal_condition: str
    pages: tuple[CapturedPage, ...]; snapshot: SnapshotDescriptor | None = None; failure: CaptureFailure | None = None
    actual_cost_units: str = "0"; budget_event_hashes: tuple[object, ...] = ()


@dataclass(frozen=True)
class DerivedVenueData:
    bars: DescriptorRegistration; events: DescriptorRegistration; bars_partition: Path; events_partition: Path
    provenance: Mapping[str, object]; complete_state_path: Path


def _number(value: Decimal | int | str, path: str) -> Decimal:
    try:
        result = Decimal(value) if not isinstance(value, Decimal) else value
    except (InvalidOperation, ValueError, TypeError) as error: raise CollectorError("BUDGET_INVALID", f"{path} must be a finite decimal", path) from error
    if not result.is_finite() or result < 0: raise CollectorError("BUDGET_INVALID", f"{path} must be a non-negative finite decimal", path)
    return result


def _reject_secrets(value: object, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}" if isinstance(key, str) else path
            normalized = str(key).casefold().replace("-", "_").replace(" ", "_")
            if any(part in normalized for part in _SECRET_PARTS): raise CollectorError("SECRET_MATERIAL_REJECTED", "credential material is never accepted", {"path": child})
            _reject_secrets(item, child)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value): _reject_secrets(item, f"{path}[{index}]")
    elif isinstance(value, str) and ((value.casefold().startswith("bearer ") and len(value) > 7) or (value.startswith("sk-") and len(value) >= 20)):
        raise CollectorError("SECRET_MATERIAL_REJECTED", "credential material is never accepted", {"path": path})


def _timestamp(value: object, path: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"): raise CollectorError("TIMESTAMP_INVALID", "UTC timestamp must end with Z", path)
    try: return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error: raise CollectorError("TIMESTAMP_INVALID", "timestamp is not ISO-8601", path) from error


def _parse_time(value: str) -> datetime: return _timestamp(value, "$")


def _root(request: CollectorRequest) -> Path: return data_root_path(request.data_root)


def _relative(root: Path, path: Path) -> str: return path.resolve().relative_to(root.resolve()).as_posix()


def _exclusive(root: Path, relative: str, data: bytes) -> Path:
    destination = root / Path(*relative.split("/")); destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink(): raise CollectorError("STORAGE_PATH_INVALID", "immutable output may not be a symlink", relative)
    return create_exclusive(destination, data)


def _decode(body: bytes, declared: str | None) -> tuple[dict[str, object], list[Mapping[str, object]]]:
    actual = sha256_digest(body)
    if declared is not None and declared != actual: raise CollectionIntegrityError("CHECKSUM_FAILURE", "transport checksum does not match response bytes", {"declared": declared, "actual": actual})
    try: value = json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error: raise CollectionIntegrityError("TRUNCATED_RESPONSE", "response is not complete UTF-8 JSON", {"content_hash": actual}) from error
    if not isinstance(value, dict): raise CollectionIntegrityError("MALFORMED_RESPONSE", "response must be an object", {"content_hash": actual})
    if value.get("schema_version") != RESPONSE_SCHEMA: raise CollectionIntegrityError("MALFORMED_RESPONSE", "response schema is not registered", {"content_hash": actual})
    rows = value.get("rows"); count = value.get("row_count")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows) or count != len(rows): raise CollectionIntegrityError("MALFORMED_RESPONSE", "row_count does not match rows", {"content_hash": actual})
    checked: list[dict[str, object]] = []
    for row in rows:
        if set(row) != _ROW_FIELDS: raise CollectionIntegrityError("MALFORMED_RESPONSE", "row fields are unknown or incomplete", {"content_hash": actual})
        if any(not isinstance(row[key], str) or not row[key].strip() for key in ("time_utc", "pair", "event_type", "tx_hash")):
            raise CollectionIntegrityError("MALFORMED_RESPONSE", "row string fields must be non-empty", {"content_hash": actual})
        numeric = (row["base_amount"], row["quote_amount"], row["price"])
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item) or item < 0 for item in numeric):
            raise CollectionIntegrityError("MALFORMED_RESPONSE", "row numeric fields must be finite and non-negative", {"content_hash": actual})
        if isinstance(row["log_index"], bool) or not isinstance(row["log_index"], int) or row["log_index"] < 0:
            raise CollectionIntegrityError("MALFORMED_RESPONSE", "log_index must be a non-negative integer", {"content_hash": actual})
        _timestamp(row["time_utc"], "$.rows.time_utc"); checked.append(dict(row))
    return value, checked


def _transport(request: CollectorRequest, page: BitqueryPageRequest) -> tuple[BitqueryTransportResponse, int, tuple[float, ...]]:
    attempts = 0; delays: list[float] = []
    while True:
        attempts += 1
        try: response = request.transport(page) if request.transport is not None else None
        except TransientTransportError as error:
            response = BitqueryTransportResponse(b"", status_code=error.status_code, retryable=True)
        except Exception as error: raise CollectionIntegrityError("TRANSPORT_FAILURE", f"transport rejected request: {error}", {"page_number": page.page_number}) from error
        if response is None: raise CollectorError("LIVE_ENDPOINT_BLOCKED", "owner-approved real-endpoint capture is explicitly blocked in this offline implementation", {"page_number": page.page_number})
        transient = response.retryable or response.status_code in _RETRYABLE
        if not transient and not 200 <= response.status_code < 300: raise CollectionIntegrityError("HTTP_FAILURE", "transport returned a non-2xx response", {"status_code": response.status_code})
        if not transient: return response, attempts, tuple(delays)
        if attempts > request.retry_limit: raise CollectionIntegrityError("RETRY_LIMIT_EXCEEDED", "bounded exponential backoff exhausted", {"attempts": attempts, "status_code": response.status_code})
        delay = min(request.backoff_base_seconds * (2 ** (attempts - 1)), request.backoff_cap_seconds); delays.append(delay * 1000)
        if delay: request.sleeper(delay)


def _existing_keys(directory: Path) -> set[str]:
    result: set[str] = set()
    if not directory.exists(): return result
    for path in directory.rglob("page.json"):
        try: value = json.loads(path.read_bytes())
        except (OSError, UnicodeError, json.JSONDecodeError): raise CollectorError("DUPLICATE_INDEX_INVALID", "stored duplicate observation is malformed", str(path))
        if isinstance(value, dict) and isinstance(value.get("duplicate_key"), str): result.add(str(value["duplicate_key"]))
    return result


def _store_page(request: CollectorRequest, response: BitqueryTransportResponse, page_number: int, request_cursor: str | None, retry: tuple[int, tuple[float, ...]], failure: CaptureFailure | None, cursor: str | None) -> tuple[CapturedPage, bool]:
    root = _root(request); content_hash = sha256_digest(response.body); watermark = response.watermark_utc or request.observed_at_utc
    _timestamp(watermark, "$.watermark_utc")
    key_document = {"collector_identity": COLLECTOR_IDENTITY, "normalized_request_hash": request.normalized_request_hash, "cursor": cursor, "source_watermark": watermark, "payload_hash": content_hash}
    duplicate_key = sha256_digest(canonical_json(key_document)); base = root / "raw" / "solana_dex" / request.normalized_request_hash[7:] / "observations" / duplicate_key[7:]
    known = _existing_keys(base.parent); duplicate = duplicate_key in known; sequence = len(list(base.iterdir())) if base.exists() else 0
    relative_body = f"raw/solana_dex/{request.normalized_request_hash[7:]}/observations/{duplicate_key[7:]}/{sequence:08d}/response.bin"
    _exclusive(root, relative_body, response.body)
    page = CapturedPage(page_number, request_cursor, cursor, watermark, content_hash, duplicate_key, relative_body,
                        "FAILURE" if failure else ("CURSOR_CONTINUE" if response.has_more else "CURSOR_COMPLETE"), retry[0], retry[0] - 1, retry[1],
                        "QUARANTINED" if failure else "VALID", failure.code if failure else None)
    _reject_secrets(page.__dict__, "$.page")
    _exclusive(root, f"raw/solana_dex/{request.normalized_request_hash[7:]}/observations/{duplicate_key[7:]}/{sequence:08d}/page.json", canonical_json(page.__dict__))
    return page, duplicate


def _raw_descriptor(request: CollectorRequest, manifest: dict[str, object], quality: dict[str, object], content: bytes) -> DescriptorRegistration:
    effective = request.observed_at_utc; capture_hash = sha256_digest(content); artifact = f"bitquery.raw.{request.normalized_request_hash[7:19]}.{request.run_id}"
    value = EvidenceDescriptor("gauntlet.evidence.v1", artifact, f"bitquery.raw.{capture_hash[7:]}.descriptor", 1, ZERO_DIGEST, None, effective, None, "panel", "solana_dex", capture_hash,
                               {"collector": COLLECTOR_IDENTITY, "uri_or_lineage": f"gauntlet://bitquery/{request.normalized_request_hash}", "run_id": request.run_id}, "OBSERVED",
                               {"start_utc": request.start_utc, "end_utc": request.end_utc, "terminal_condition": manifest["terminal_condition"]},
                               {"watermark_at": manifest["watermark_utc"], "max_age": request.max_age}, quality, (), "GATE_CRITICAL", ("solana.discovery",), content, request.actor)
    sealed = replace(value, descriptor_hash=descriptor_digest(value)); _reject_secrets(dict(sealed.source), "$.source")
    from gauntlet.data.descriptors import register_descriptor
    return register_descriptor(sealed)


def collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult:
    """Capture immutable pages through an injected transport; never call the live endpoint implicitly."""

    _reject_secrets(request.__dict__, "$.request")
    if request.transport is None: raise CollectorError("LIVE_ENDPOINT_BLOCKED", "owner-approved real-endpoint capture is explicitly blocked in this offline implementation")
    budget.authorize(budget.units(request.estimated_cost_units, "$.estimated_cost_units"), request)
    spent = Decimal(0)
    family_remaining = budget.units(budget.family_limit_units, "$.family_limit_units") - budget.units(budget.family_spent_units, "$.family_spent_units")
    api_remaining = budget.units(budget.api_limit_units, "$.api_limit_units") - budget.units(budget.api_spent_units, "$.api_spent_units")
    pre = BudgetEvent("pre_capture", "OK", request.observed_at_utc, request.run_id, str(budget.family_spent_units), str(budget.api_spent_units), str(budget.family_limit_units), str(budget.api_limit_units))
    events = [budget.event_recorder(pre)]
    pages: list[CapturedPage] = []; duplicates: list[bool] = []; cursor = request.initial_cursor; watermark = request.start_utc; failure: CaptureFailure | None = None; terminal = "NOT_STARTED"
    seen_cursors = {request.initial_cursor} if request.initial_cursor is not None else set()
    for page_number in range(1, request.max_pages + 1):
        response = BitqueryTransportResponse(b"")
        cost = budget.units(request.per_page_cost_units, "$.per_page_cost_units")
        if cost > family_remaining or cost > api_remaining:
            failure = CaptureFailure("BUDGET_EXHAUSTED", "additional page would exceed the declared budget", "$.budget", page_number); terminal = failure.code; break
        try:
            response, attempts, delays = _transport(request, BitqueryPageRequest(cursor, request.normalized_request_hash, page_number))
            _decode(response.body, response.declared_content_hash)
            if response.has_more and (not isinstance(response.cursor, str) or not response.cursor): raise CollectionIntegrityError("CURSOR_INVALID", "continuation response has no cursor")
            observed_watermark = response.watermark_utc or request.observed_at_utc; _timestamp(observed_watermark, "$.watermark_utc")
            if _parse_time(observed_watermark) < _parse_time(watermark): raise CollectionIntegrityError("CURSOR_REGRESSION", "source watermark moved backwards")
            if _parse_time(observed_watermark) > _parse_time(request.observed_at_utc): raise CollectionIntegrityError("FRESHNESS_INVALID", "source watermark is after observation time")
            if response.cursor in seen_cursors: raise CollectionIntegrityError("CURSOR_REGRESSION", "page cursor repeats an earlier cursor")
            if response.has_more: seen_cursors.add(response.cursor)
            page_failure = None
        except CollectionIntegrityError as error:
            if error.code in _NO_PAYLOAD_FAILURES:
                failure = CaptureFailure(error.code, error.message, "$.transport", page_number); terminal = error.code; break
            attempts = locals().get("attempts", 1); delays = locals().get("delays", ())
            page_failure = CaptureFailure(error.code, error.message, "$.response", page_number); failure = page_failure; terminal = error.code
        page, duplicate = _store_page(request, response, page_number, cursor, (attempts, delays), page_failure, response.cursor)
        pages.append(page); duplicates.append(duplicate)
        if failure is not None: break
        cursor = response.cursor if response.has_more else None; watermark = page.watermark_utc
        actual = budget.units(response.cost_units, "$.response.cost_units"); family_remaining -= actual; api_remaining -= actual; spent += actual
        if response.has_more and page_number == request.max_pages:
            failure = CaptureFailure("PARTIAL_CAPTURE", "page limit reached before a terminal page", "$.max_pages", page_number); terminal = failure.code
        elif not response.has_more: terminal = "CURSOR_COMPLETE"; break
    manifest = {"schema_version": "bitquery.raw-manifest.v1", "collector_identity": COLLECTOR_IDENTITY, "run_id": request.run_id, "normalized_request_hash": request.normalized_request_hash,
                "normalized_request": dict(request.query), "start_utc": request.start_utc, "end_utc": request.end_utc, "observed_at_utc": request.observed_at_utc,
                "watermark_utc": watermark, "terminal_condition": terminal, "status": "QUARANTINED" if failure else "COMPLETE", "pages": [page.__dict__ for page in pages],
                "duplicate_observations": sum(duplicates), "actual_cost_units": str(spent)}
    _reject_secrets(manifest, "$.manifest"); content = canonical_json(manifest)
    checks = [{"name": f"page-{page.page_number}-checksum", "status": "PASS" if page.quality_state == "VALID" else "FAIL"} for page in pages] or [{"name": "no-accepted-payload", "status": "FAIL"}]
    quality = {"state": "QUARANTINED" if failure else "VALID", "checks": checks}
    if failure is not None: quality |= {"reason": failure.__dict__}
    snapshot_registration = _raw_descriptor(request, manifest, quality, content) if pages else None
    snapshot_hash = sha256_digest(content)
    post = BudgetEvent("post_capture", "ERROR" if failure else "OK", request.observed_at_utc, request.run_id, str(budget.units(budget.family_spent_units, "$") + spent),
                       str(budget.units(budget.api_spent_units, "$") + spent), str(budget.family_limit_units), str(budget.api_limit_units), snapshot_hash)
    events.append(budget.event_recorder(post))
    return CaptureResult("FAILED" if failure is not None and not pages else "QUARANTINED" if failure else "COMPLETE", request.run_id, request.normalized_request_hash, watermark, terminal, tuple(pages),
                         SnapshotDescriptor(snapshot_registration, manifest) if snapshot_registration else None, failure, str(spent), tuple(events))


def _derived_descriptor(kind: str, artifact: str, request_run: str, content: bytes, manifest: Mapping[str, object], raw: DescriptorRegistration, rows: int) -> EvidenceDescriptor:
    source = {"collector": TRANSFORM_IDENTITY, "uri_or_lineage": f"gauntlet://derived/{artifact}", "raw_descriptor_hash": raw.descriptor_hash, "transformation": manifest}
    value = EvidenceDescriptor("gauntlet.evidence.v1", artifact, f"{artifact}.{request_run}.descriptor", 1, ZERO_DIGEST, None, str(manifest["observed_at_utc"]), None, kind, "solana_dex", sha256_digest(content),
                               source, "OBSERVED", {"start_utc": manifest["start_utc"], "end_utc": manifest["end_utc"]}, {"watermark_at": manifest["watermark_utc"], "max_age": "P7D"},
                               {"state": "VALID", "checks": [{"name": "partition-checksum", "status": "PASS"}, {"name": "row-count", "status": "PASS"}]},
                               ({"artifact_id": raw.artifact_id, "relation": "requires", "descriptor_hash": raw.descriptor_hash, "descriptor_id": raw.descriptor_id},), "GATE_CRITICAL",
                               ("solana.bars",) if kind == "bars" else ("solana.events",), content)
    return replace(value, descriptor_hash=descriptor_digest(value))


def derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData:
    """Register bars/events only after every immutable input and both descriptors validate."""

    from gauntlet.data.descriptors import register_descriptor
    manifest = dict(raw_snapshot.manifest); root = data_root_path(None)
    if raw_snapshot.registration.descriptor_hash not in load_descriptor_registry(root): raise CollectionIntegrityError("RAW_SNAPSHOT_UNREGISTERED", "raw snapshot is absent from the verified registry")
    if raw_snapshot.registration.content_path.read_bytes() != canonical_json(manifest): raise CollectionIntegrityError("RAW_SNAPSHOT_MISMATCH", "descriptor bytes do not match snapshot manifest")
    if manifest.get("status") != "COMPLETE": raise CollectionIntegrityError("SNAPSHOT_QUARANTINED", "derived tables require a complete snapshot")
    rows: list[dict[str, object]] = []
    for page in manifest["pages"]:  # type: ignore[index]
        body = (root / str(page["body_path"])).read_bytes()  # type: ignore[index]
        if sha256_digest(body) != page["content_hash"]: raise CollectionIntegrityError("CHECKSUM_FAILURE", "raw page no longer matches its sealed hash")
        _, decoded = _decode(body, str(page["content_hash"])); rows.extend(dict(row) for row in decoded)
    _reject_secrets(rows, "$.rows")
    allowed = {"time_utc", "pair", "event_type", "base_amount", "quote_amount", "price", "tx_hash", "log_index"}
    if any(set(row) - allowed or "time_utc" not in row or "pair" not in row for row in rows): raise CollectionIntegrityError("MALFORMED_RESPONSE", "derived row fields are not registered")
    bars: dict[tuple[str, str], dict[str, object]] = {}
    for row in sorted(rows, key=lambda item: (str(item["pair"]), str(item["time_utc"]), int(item.get("log_index", 0)))):
        timestamp = _parse_time(str(row["time_utc"])); bucket = timestamp.replace(second=timestamp.second // 60 * 60, microsecond=0).isoformat().replace("+00:00", "Z"); pair = str(row["pair"])
        price = float(row["price"]); amount = float(row["base_amount"]); bar = bars.setdefault((pair, bucket), {"pair": pair, "bucket_start_utc": bucket, "open": price, "high": price, "low": price, "close": price, "base_volume": 0.0, "trade_count": 0})
        bar["high"] = max(float(bar["high"]), price); bar["low"] = min(float(bar["low"]), price); bar["close"] = price; bar["base_volume"] = float(bar["base_volume"]) + amount; bar["trade_count"] = int(bar["trade_count"]) + 1
    bar_rows = [dict(value) for _, value in sorted(bars.items())]; event_rows = [{key: row.get(key) for key in allowed} for row in rows]
    bars_schema = {"pair": "string", "bucket_start_utc": "string", "open": "double", "high": "double", "low": "double", "close": "double", "base_volume": "double", "trade_count": "int64"}
    events_schema = {"time_utc": "string", "pair": "string", "event_type": "string", "base_amount": "double", "quote_amount": "double", "price": "double", "tx_hash": "string", "log_index": "int64"}
    from .parquet import write_parquet
    if not bar_rows or not event_rows: raise CollectionIntegrityError("DERIVATION_EMPTY", "snapshot produced no Solana rows")
    bar_bytes = write_parquet(bar_rows, bars_schema); event_bytes = write_parquet(event_rows, events_schema); request_run = str(manifest["run_id"])
    base = f"evidence/solana_dex/{request_run}"; bar_path = _exclusive(root, f"{base}/solana.bars/part-00000.parquet", bar_bytes); event_path = _exclusive(root, f"{base}/solana.events/part-00000.parquet", event_bytes)
    provenance = {"schema_version": "gauntlet.solana-derivation.v1", "transform_identity": TRANSFORM_IDENTITY, "raw_descriptor_hash": raw_snapshot.registration.descriptor_hash,
                  "input_page_hashes": [page["content_hash"] for page in manifest["pages"]],  # type: ignore[index]
                  "partitions": {"solana.bars": {"path": _relative(root, bar_path), "hash": sha256_digest(bar_bytes), "rows": len(bar_rows), "format": "parquet"},
                                 "solana.events": {"path": _relative(root, event_path), "hash": sha256_digest(event_bytes), "rows": len(event_rows), "format": "parquet"}}}
    bars_bytes = canonical_json({**provenance, "artifact_id": "solana.bars", "kind": "bars"})
    events_bytes = canonical_json({**provenance, "artifact_id": "solana.events", "kind": "events"})
    bars_descriptor = _derived_descriptor("bars", "solana.bars", request_run, bars_bytes, manifest, raw_snapshot.registration, len(bar_rows))
    events_descriptor = _derived_descriptor("events", "solana.events", request_run, events_bytes, manifest, raw_snapshot.registration, len(event_rows))
    validate_descriptor(descriptor_mapping(bars_descriptor), bars_bytes); validate_descriptor(descriptor_mapping(events_descriptor), events_bytes)
    registered_bars = register_descriptor(bars_descriptor); registered_events = register_descriptor(events_descriptor)
    complete = {"schema_version": "gauntlet.derived-complete.v1", "status": "COMPLETE", "bars_descriptor_hash": registered_bars.descriptor_hash, "events_descriptor_hash": registered_events.descriptor_hash, "provenance_hash": sha256_digest(canonical_json(provenance))}
    state_path = _exclusive(root, f"{base}/complete.json", canonical_json(complete))
    return DerivedVenueData(registered_bars, registered_events, bar_path, event_path, provenance, state_path)


__all__ = ["BudgetContext", "BudgetEvent", "CaptureResult", "CollectorRequest", "DerivedVenueData", "LedgerBudgetRecorder", "SnapshotDescriptor", "collect_bitquery", "derive_solana_tables"]
