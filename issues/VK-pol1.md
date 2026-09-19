---
id: VK-pol1
title: "Capture Hyperliquid transfer snapshots"
status: open
priority: 2
type: feature
labels: [external-integration, integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:17Z
created_by: speed
updated_at: 2026-09-18T23:31:17Z
content_hash: "sha256:a82c6912ef6551f2f039938281252c685f8456516ba8419c546a30f4b10b2276"
blocked_by: [VK-pg9j]
blocks: [VK-jvku, VK-sbdy, VK-ldg1]
---

## Description
## USER INTENT
The owner needs Hyperliquid transfer evidence kept separate so it can test transfer without contaminating Solana discovery statistics.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement the Hyperliquid collector for immutable paginated market/order snapshots and venue-derived tables. Produce `hyperliquid.bars`, `hyperliquid.order_book`, and declared transfer descriptors with venue_track `hyperliquid`, transformation provenance, mechanics, fees, latency, failure modes, and benchmark identity. Track pagination, watermark, retries, cost, duplicates, partial capture, and quarantine exactly as the shared collector rules require. Hyperliquid is never pooled into a Solana candidate gate.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Declaring and evaluating a cross-venue transfer hypothesis: lands in judge transfer work.
- Solana collection: sibling Bitquery story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/audit/collectors/hyperliquid.py -> collect_hyperliquid(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
- src/gauntlet/audit/collectors/hyperliquid.py -> derive_transfer_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult; derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult; derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData

### Acceptance Criteria (story contract)
1. Real-endpoint verification (non-automatable): capture one minimum-scope Hyperliquid market/order page and retain immutable response plus descriptor/event hashes.
2. Market and order-book descriptors carry venue_track `hyperliquid`, source watermark, coverage, freshness, quality, dependencies, criticality, and downstream metrics.
3. Venue mechanics, fee, latency, failure, and benchmark assumptions are explicit in the transfer population metadata.
4. Pagination, rate limit, cost, duplicate, partial-capture, and quarantine behavior fail closed without overwriting immutable observations.
5. A Hyperliquid descriptor cannot satisfy a single-venue Solana discovery gate.
6. Sanitized collection events expose no credential or private value.

## Testing Requirements
- Unit: Test venue descriptor identity, pagination, table transformation, duplicate retention, and failure paths with golden pages.
- Integration tests: MANDATORY (no mocks). Run the real endpoint, derive tables, register descriptors, and prove a Solana-only gate sees the Hyperliquid artifact as ineligible.
- Commands to run: `uv run pytest tests/collectors/test_hyperliquid.py` plus recorded real-endpoint evidence.

## MANDATORY SKILLS
None identified.

## Delivery Requirements
- Developer must paste test or CI output snippets into story notes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label; PM acceptance remains separate.

## nd_contract
status: new

### evidence
- Created 2026-09-18 by sr_pm from the owner-confirmed Phase 1 contracts at repository commit d77b4032e7ab1c90b435908a1a6d104007feff9e.
- Epic containment: VK-u40v.

### proof
- [ ] AC #1: Real-endpoint verification (non-automatable): capture one minimum-scope Hyperliquid market/order page and retain immutable response plus descriptor/event hashes.
- [ ] AC #2: Market and order-book descriptors carry venue_track `hyperliquid`, source watermark, coverage, freshness, quality, dependencies, criticality, and downstream metrics.
- [ ] AC #3: Venue mechanics, fee, latency, failure, and benchmark assumptions are explicit in the transfer population metadata.
- [ ] AC #4: Pagination, rate limit, cost, duplicate, partial-capture, and quarantine behavior fail closed without overwriting immutable observations.
- [ ] AC #5: A Hyperliquid descriptor cannot satisfy a single-venue Solana discovery gate.
- [ ] AC #6: Sanitized collection events expose no credential or private value.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:18Z dep_added: blocked_by VK-pg9j
- 2026-09-18T23:31:18Z dep_added: blocks VK-jvku
- 2026-09-18T23:31:25Z dep_added: blocks VK-sbdy
- 2026-09-18T23:31:39Z dep_added: blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-jvku]], [[VK-sbdy]], [[VK-ldg1]]
- Blocked by: [[VK-pg9j]]

## Comments
