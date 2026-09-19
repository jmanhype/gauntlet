---
id: VK-8ch2
title: "Reduce trades to effective observations"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-18T23:31:25Z
created_by: speed
updated_at: 2026-09-18T23:31:25Z
content_hash: "sha256:87bd0059437cecf08b30243fa69db0b1bf70f3519df00a87ee61cf8058c8fe2e"
blocked_by: [VK-2g0f]
blocks: [VK-aumt, VK-wrce, VK-2e0k, VK-vqvy, VK-rkdr]
---

## Description
## USER INTENT
The owner needs overlapping and clustered observations reported honestly rather than counting repeated exposure as independent trades.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement the effective-evidence panel from row-level trades/labels and a frozen token/regime/cluster policy. Declare label/trade overlap window and reduction algorithm, serial-dependence model or conservative treatment, token identity, correlated-token clustering method/threshold/window and freeze time, regime taxonomy and point-in-time assignment, venue/variant/family/time grouping, and the exact reduction from raw observations to effective observations. Clustering may not reuse post-outcome returns unless method and freeze time are explicit and replayable. Required regime gaps or unresolved overlap can never become PASS.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Dominance contribution math: sibling dominance story.
- Gate thresholds: decision-engine story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 600 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/lab/effective_evidence.py -> compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel

CONSUMES:
- VK-2g0f: src/gauntlet/judge/exact_execution.py -> evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun
  spec: evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun

### Acceptance Criteria (story contract)
1. Panel reports raw resolved trades and effective independent observations separately with full calculation disclosure.
2. Overlap window, serial treatment, clustering keys, regime handling, and reduction formula are versioned and reconstructible.
3. Correlated-token clusters are frozen before outcomes or carry explicit method/freeze-time disclosure.
4. Repeated regimes and time blocks cannot turn missing required coverage into PASS.
5. Effective count is adaptive upward when justified but never removes a required regime gap or unresolved overlap.
6. Point-in-time regime assignment cannot use post-outcome features undeclared in the frozen policy.

## Testing Requirements
- Unit: Property-test overlap reduction, clusters, serial dependence, regimes, and adaptive count behavior.
- Integration tests: MANDATORY (no mocks). Compute effective evidence from real exact-execution rows with overlapping trades and correlated tokens; verify disclosure and conservative treatment against an independent oracle.
- Commands to run: `uv run pytest tests/lab/test_effective_evidence.py`.

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
- [ ] AC #1: Panel reports raw resolved trades and effective independent observations separately with full calculation disclosure.
- [ ] AC #2: Overlap window, serial treatment, clustering keys, regime handling, and reduction formula are versioned and reconstructible.
- [ ] AC #3: Correlated-token clusters are frozen before outcomes or carry explicit method/freeze-time disclosure.
- [ ] AC #4: Repeated regimes and time blocks cannot turn missing required coverage into PASS.
- [ ] AC #5: Effective count is adaptive upward when justified but never removes a required regime gap or unresolved overlap.
- [ ] AC #6: Point-in-time regime assignment cannot use post-outcome features undeclared in the frozen policy.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:25Z dep_added: blocked_by VK-2g0f
- 2026-09-18T23:31:27Z dep_added: blocks VK-aumt
- 2026-09-18T23:31:28Z dep_added: blocks VK-wrce
- 2026-09-18T23:31:29Z dep_added: blocks VK-2e0k
- 2026-09-18T23:31:43Z dep_added: blocks VK-vqvy
- 2026-09-19T01:37:42Z dep_added: blocks VK-rkdr

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-aumt]], [[VK-wrce]], [[VK-2e0k]], [[VK-vqvy]], [[VK-rkdr]]
- Blocked by: [[VK-2g0f]]

## Comments
