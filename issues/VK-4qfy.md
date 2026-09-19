---
id: VK-4qfy
title: "Derive event-level Solana reserve state"
status: open
priority: 2
type: feature
labels: [integration, phase-1]
parent: VK-u40v
created_at: 2026-09-19T01:37:42Z
created_by: speed
updated_at: 2026-09-19T01:39:43Z
content_hash: "sha256:d3ee1681999b9e17919f39471200b27fbdad2fe9799da216ba5fc5b1f88fec7f"
blocked_by: [VK-pg9j]
blocks: [VK-2g0f, VK-ldg1]
was_blocked_by: [VK-kmbs]
---

## Description
## USER INTENT
The owner needs contemporaneous pool reserve state so exact Solana execution can quote fills instead of trusting price-only results.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement a local-only derivation from an already captured Bitquery raw/event snapshot. Produce an event-level ReserveSeries containing pool/token identities, UTC event time, reserve amounts, transaction/event identifiers, source watermark, content hash, and provenance. Register a descriptor with kind `reserves`, venue_track `solana_dex`, quality/freshness/coverage, dependencies, GATE_CRITICAL criticality, and downstream execution metrics. Reserve corrections create superseding descriptor versions; original bytes remain unchanged.

Phase 1 boundaries:
- No order placement, real-money exposure, public API, daemon, multi-tenant access, or social claim.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted.

## OUT OF SCOPE
- Fetching Bitquery pages or handling credentials: owned by the Bitquery collector story.
- Constant-product quote math and trade alignment: owned by exact Solana execution.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/audit/collectors/solana_reserves.py -> derive_reserve_events(raw_snapshot: SnapshotDescriptor, events: VenueEvents) -> ReserveSeries
- src/gauntlet/audit/collectors/solana_reserves.py -> register_reserve_descriptor(reserves: ReserveSeries, source_hash: str) -> DescriptorRegistration
- data/evidence/solana_dex/reserves.parquet -> immutable event-level reserve artifact

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
- VK-kmbs: src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
  spec: register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration

### Acceptance Criteria (story contract)
1. Each output row binds pool/token identity, UTC event time, reserve amounts, transaction/event identifier, source watermark, and raw content hash.
2. The registered descriptor uses kind `reserves`, venue_track `solana_dex`, GATE_CRITICAL criticality, explicit coverage/freshness/quality, dependencies, and downstream execution metrics.
3. The derivation performs no network call and accepts only a verified local Bitquery snapshot descriptor.
4. Missing, malformed, duplicate, stale, truncated, or cursor-regressed reserve evidence creates a superseding QUARANTINED descriptor version and never overwrites original bytes.
5. A correction supersedes the exact prior descriptor hash while historical `as_of` selection continues to resolve the original population.
6. The artifact supports at-or-before simulated-order alignment and exposes reserve hashes suitable for entry and exit verification.

## Testing Requirements
- Unit: Test schema validation, event alignment fields, provenance, descriptor identity, correction lineage, and quarantine paths.
- Integration tests: MANDATORY (no mocks). Derive reserves from a real immutable local Bitquery capture fixture, verify descriptor and Parquet hashes, then corrupt a copy and prove quarantine blocks without mutating the original.
- Commands to run: `uv run pytest tests/collectors/test_solana_reserves.py`.

## MANDATORY SKILLS
None identified.

## Delivery Requirements
- Developer must paste test or CI output snippets into story notes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label; PM acceptance remains separate.

## nd_contract
status: new

### evidence
- Created 2026-09-18 to repair the documented Anchor rejection in the live Phase 1 backlog.
- Epic containment: VK-u40v.

### proof
- [ ] AC #1: Each output row binds pool/token identity, UTC event time, reserve amounts, transaction/event identifier, source watermark, and raw content hash.
- [ ] AC #2: The registered descriptor uses kind `reserves`, venue_track `solana_dex`, GATE_CRITICAL criticality, explicit coverage/freshness/quality, dependencies, and downstream execution metrics.
- [ ] AC #3: The derivation performs no network call and accepts only a verified local Bitquery snapshot descriptor.
- [ ] AC #4: Missing, malformed, duplicate, stale, truncated, or cursor-regressed reserve evidence creates a superseding QUARANTINED descriptor version and never overwrites original bytes.
- [ ] AC #5: A correction supersedes the exact prior descriptor hash while historical `as_of` selection continues to resolve the original population.
- [ ] AC #6: The artifact supports at-or-before simulated-order alignment and exposes reserve hashes suitable for entry and exit verification.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T01:37:42Z dep_added: blocked_by VK-pg9j
- 2026-09-19T01:37:42Z dep_added: blocked_by VK-kmbs
- 2026-09-19T01:37:43Z dep_added: blocks VK-2g0f
- 2026-09-19T01:37:44Z dep_added: blocks VK-ldg1
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-2g0f]], [[VK-ldg1]]
- Blocked by: [[VK-pg9j]]
- Was blocked by: [[VK-kmbs]]

## Comments

### 2026-09-19T01:39:43Z speed
RECOMMEND hard-tdd: event-level reserve provenance is required for executable Solana evidence. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
