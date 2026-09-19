---
id: VK-2g0f
title: "Price Solana fills from reserve state"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-18T23:31:23Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:2cfc41423965675cd834dd761e60f385c5fa49459ae1d176cd5bfa3453f0fa49"
blocked_by: [VK-4qfy]
blocks: [VK-8ch2, VK-wrce, VK-l747, VK-vqvy, VK-rkdr]
was_blocked_by: [VK-0c4c]
---

## Description
## USER INTENT
The owner needs Solana paper fills priced against contemporaneous pool reserves so a price-only illusion cannot support promotion.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement exact Solana execution for locked walk-forward trades. Record trade-level entry/exit reserve hashes, exact constant-product quotes, fee/impact/latency/fill-failure scenarios, and invalid-quote counts. Use event-level AMM reserve state at or before the simulated order and a documented alignment rule. Missing or invalid reserve state is a failed quote/evidence gap, never a fill. Price-only Solana results are exploratory. Overlap policy is disclosed when positions overlap.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Hyperliquid mechanics: sibling transfer story.
- Effective-observation reduction: lab effective-evidence story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~7 files, under 650 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/judge/exact_execution.py -> evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun

CONSUMES:
- VK-0c4c: src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
  spec: evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun

### Acceptance Criteria (story contract)
1. Each entry and exit records exact reserve-state hashes and timestamps satisfying the declared at-or-before alignment rule.
2. Constant-product output matches an independent small-vector oracle.
3. Fee, impact, latency, and fill-failure scenarios use predeclared versioned inputs and report PASS/FAIL with numeric assumptions.
4. Missing, stale, malformed, or unusable reserve state yields a failed quote and evidence gap, never a fill or silent substitution.
5. Invalid-quote counts and execution failures appear in every downstream row-level artifact.
6. When overlap is allowed, its policy and effect on raw count are disclosed to effective evidence.
7. Result exposes enough row detail for calibration, dominance, robustness, and reconciliation to be independently recomputed.

## Testing Requirements
- Unit: Test quote math against an oracle, reserve alignment, adverse scenarios, invalid quotes, and row completeness.
- Integration tests: MANDATORY (no mocks). Execute a real synthetic locked-trade stream against immutable event-level reserves, remove one reserve on a copy, and prove the affected trade blocks/fails rather than filling.
- Commands to run: `uv run pytest tests/judge/test_exact_execution.py`.

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
- [ ] AC #1: Each entry and exit records exact reserve-state hashes and timestamps satisfying the declared at-or-before alignment rule.
- [ ] AC #2: Constant-product output matches an independent small-vector oracle.
- [ ] AC #3: Fee, impact, latency, and fill-failure scenarios use predeclared versioned inputs and report PASS/FAIL with numeric assumptions.
- [ ] AC #4: Missing, stale, malformed, or unusable reserve state yields a failed quote and evidence gap, never a fill or silent substitution.
- [ ] AC #5: Invalid-quote counts and execution failures appear in every downstream row-level artifact.
- [ ] AC #6: When overlap is allowed, its policy and effect on raw count are disclosed to effective evidence.
- [ ] AC #7: Result exposes enough row detail for calibration, dominance, robustness, and reconciliation to be independently recomputed.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: bind exact execution to reserve producer

GENERAL RULE SWEEP: Every typed input consumed by a story must have an explicit upstream producer and dependency.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-4qfy: src/gauntlet/audit/collectors/solana_reserves.py -> derive_reserve_events(raw_snapshot: SnapshotDescriptor, events: VenueEvents) -> ReserveSeries
  spec: derive_reserve_events(raw_snapshot: SnapshotDescriptor, events: VenueEvents) -> ReserveSeries

### Acceptance Criteria (repair revision)
1. Exact execution consumes the event-level ReserveSeries produced by the reserve story and records entry/exit reserve hashes from that artifact.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: Exact execution consumes the event-level ReserveSeries produced by the reserve story and records entry/exit reserve hashes from that artifact.


## History
- 2026-09-18T23:31:23Z dep_added: blocked_by VK-0c4c
- 2026-09-18T23:31:25Z dep_added: blocks VK-8ch2
- 2026-09-18T23:31:28Z dep_added: blocks VK-wrce
- 2026-09-18T23:31:29Z dep_added: blocks VK-l747
- 2026-09-18T23:31:42Z dep_added: blocks VK-vqvy
- 2026-09-19T01:37:42Z dep_added: blocks VK-rkdr
- 2026-09-19T01:37:43Z dep_added: blocked_by VK-4qfy
- 2026-09-19T05:50:41Z dep_removed: was_blocked_by VK-0c4c

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-8ch2]], [[VK-wrce]], [[VK-l747]], [[VK-vqvy]], [[VK-rkdr]]
- Blocked by: [[VK-4qfy]]
- Was blocked by: [[VK-0c4c]]

## Comments
