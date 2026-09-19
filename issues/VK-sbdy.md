---
id: VK-sbdy
title: "Test Hyperliquid transfer populations"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-18T23:31:24Z
created_by: speed
updated_at: 2026-09-18T23:31:24Z
content_hash: "sha256:dd335d9c7474a2c7cc3c250840372fe3269cfea459d026ae97049ed8f825d0fc"
blocked_by: [VK-0c4c, VK-pol1]
blocks: [VK-vqvy]
---

## Description
## USER INTENT
The owner needs transfer treated as a separate falsifiable hypothesis rather than pooling two execution environments.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement a separate Hyperliquid evaluation for a frozen Solana candidate fingerprint. Record exact fingerprint, transfer plausibility, frozen Hyperliquid window, permitted adaptation (none, recalibration, or retraining), benchmark, execution model, assumptions, and lineage. Produce Hyperliquid-specific artifacts and execution assumptions under venue_track `cross_venue_transfer` when declared; discovery remains Solana-only. Any Hyperliquid adaptation is a new trial linked to the source. Success strengthens only the declared transfer hypothesis and does not retroactively strengthen Solana discovery.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Pooling venue counts into one gate: prohibited.
- Hyperliquid collection mechanics: upstream collector story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/judge/transfer.py -> evaluate_transfer(request: TransferRequest) -> TransferEvaluation

CONSUMES:
- VK-0c4c: src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
  spec: evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
- VK-pol1: src/gauntlet/audit/collectors/hyperliquid.py -> derive_transfer_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: derive_transfer_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData

### Acceptance Criteria (story contract)
1. Transfer trial records exact source fingerprint and all declared transfer settings before interpretation.
2. Venue identity is `cross_venue_transfer`; Solana and Hyperliquid counts and assumptions remain side-by-side and separate.
3. Permitted adaptation is enforced and any adaptation creates a linked new trial.
4. Hyperliquid mechanics, fees, latency, failure modes, and benchmark use venue-specific assumptions.
5. Transfer success cannot increase a Solana discovery-gate observation count or alter its verdict.
6. Descriptor and provenance checks reject an undeclared cross-venue artifact in a single-venue gate.

## Testing Requirements
- Unit: Test identity separation, adaptation branching, lineage linkage, and gate eligibility.
- Integration tests: MANDATORY (no mocks). Evaluate the same synthetic candidate fingerprint against real registered Solana and Hyperliquid populations, then prove venue-specific artifacts remain separate through dependency evaluation.
- Commands to run: `uv run pytest tests/judge/test_transfer.py`.

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
- Epic containment: VK-0auj.

### proof
- [ ] AC #1: Transfer trial records exact source fingerprint and all declared transfer settings before interpretation.
- [ ] AC #2: Venue identity is `cross_venue_transfer`; Solana and Hyperliquid counts and assumptions remain side-by-side and separate.
- [ ] AC #3: Permitted adaptation is enforced and any adaptation creates a linked new trial.
- [ ] AC #4: Hyperliquid mechanics, fees, latency, failure modes, and benchmark use venue-specific assumptions.
- [ ] AC #5: Transfer success cannot increase a Solana discovery-gate observation count or alter its verdict.
- [ ] AC #6: Descriptor and provenance checks reject an undeclared cross-venue artifact in a single-venue gate.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:25Z dep_added: blocked_by VK-0c4c
- 2026-09-18T23:31:25Z dep_added: blocked_by VK-pol1
- 2026-09-18T23:31:42Z dep_added: blocks VK-vqvy

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-vqvy]]
- Blocked by: [[VK-0c4c]], [[VK-pol1]]

## Comments
