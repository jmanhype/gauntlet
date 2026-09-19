---
id: VK-jvku
title: "Report collector health without substitution"
status: open
priority: 2
type: feature
labels: [integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:18Z
created_by: speed
updated_at: 2026-09-18T23:31:18Z
content_hash: "sha256:002b179de48c629b3d41b66a7cbbc2a30b4e629dae8604aac5480ca645c4935e"
blocked_by: [VK-pg9j, VK-pol1, VK-bbmn]
blocks: [VK-1ptl, VK-ldg1]
---

## Description
## USER INTENT
The owner needs collection failures and budget consumption visible as first-class evidence rather than silent data gaps.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Create a collection-health projection across Bitquery, Hyperliquid, and Scarlett captures. It reports duplicates/deduplication, partial-capture state, API-cost and family budget state, retries/rate limits, failure and quarantine events, watermark lag, and affected descriptors and downstream metrics. It never imputes, estimates, forward-fills, or substitutes gate evidence. It distinguishes noncritical reduced coverage from gate-critical blocking.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Repairing a collector defect: lands in a future bug story created from the health evidence.
- Alert delivery in Phase 2: out of Phase 1.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~5 files, under 400 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/audit/health.py -> summarize_collection_health(scope: CollectionScope, as_of: datetime) -> CollectionHealth

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
- VK-pol1: src/gauntlet/audit/collectors/hyperliquid.py -> derive_transfer_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: derive_transfer_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
- VK-bbmn: src/gauntlet/audit/collectors/scarlett.py -> snapshot_scarlett(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
  spec: snapshot_scarlett(request: CollectorRequest, budget: BudgetContext) -> CaptureResult

### Acceptance Criteria (story contract)
1. Health output reports per-collector success, failure, retry/rate-limit, duplicate, partial-capture, quarantine, watermark, and budget state.
2. Every gate-critical defect maps to affected artifact descriptors, metrics, and downstream trials.
3. Noncritical missingness visibly reduces coverage without invalidating unaffected metrics.
4. Budget summaries distinguish estimated and actual cost and prevent spend after exhaustion.
5. The projection is deterministic for a ledger/event head and regenerates without mutation.

## Testing Requirements
- Unit: Test aggregation, budget arithmetic, affected-metric mapping, and deterministic projection.
- Integration tests: MANDATORY (no mocks). Use real ledger events from the three collector stories, introduce one quarantined capture and one noncritical duplicate, and verify health from immutable inputs.
- Commands to run: `uv run pytest tests/audit/test_collection_health.py`.

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
- [ ] AC #1: Health output reports per-collector success, failure, retry/rate-limit, duplicate, partial-capture, quarantine, watermark, and budget state.
- [ ] AC #2: Every gate-critical defect maps to affected artifact descriptors, metrics, and downstream trials.
- [ ] AC #3: Noncritical missingness visibly reduces coverage without invalidating unaffected metrics.
- [ ] AC #4: Budget summaries distinguish estimated and actual cost and prevent spend after exhaustion.
- [ ] AC #5: The projection is deterministic for a ledger/event head and regenerates without mutation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:18Z dep_added: blocked_by VK-pg9j
- 2026-09-18T23:31:18Z dep_added: blocked_by VK-pol1
- 2026-09-18T23:31:19Z dep_added: blocked_by VK-bbmn
- 2026-09-18T23:31:33Z dep_added: blocks VK-1ptl
- 2026-09-18T23:31:39Z dep_added: blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-1ptl]], [[VK-ldg1]]
- Blocked by: [[VK-pg9j]], [[VK-pol1]], [[VK-bbmn]]

## Comments
