---
id: VK-wrce
title: "Measure concentration dominance"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-18T23:31:27Z
created_by: speed
updated_at: 2026-09-18T23:31:27Z
content_hash: "sha256:264f37db01d481e10fc4015f772caecc2507ba9b68429e38932a8c26beecd2e7"
blocked_by: [VK-2g0f, VK-8ch2]
blocks: [VK-2e0k, VK-vqvy]
---

## Description
## USER INTENT
The owner needs to know whether one trade, token, regime, venue, variant, or execution artifact creates an illusory edge.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Compute percentage contribution and contribution-after-removal for the largest single trade, token, correlated token cluster, regime, venue, strategy variant, and execution artifact. Rerun the evaluation after removing each top contributor and report the dominance verdict per axis. Use complete row-level returns and lineage; missing lineage blocks. This panel supports the business rule that no single contributor may contribute more than half of positive expectancy or reverse the result when removed.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Applying the 50% threshold or promotion decision: immutable gate policy story.
- Correlation cluster definition: upstream effective-evidence policy.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/lab/dominance.py -> compute_dominance(rows: RowLevelReturns, lineage: TrialLineage) -> DominancePanel

CONSUMES:
- VK-2g0f: src/gauntlet/judge/exact_execution.py -> evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun
  spec: evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun
- VK-8ch2: src/gauntlet/lab/effective_evidence.py -> compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel
  spec: compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel

### Acceptance Criteria (story contract)
1. Panel reports contribution and removal effects for every declared axis.
2. Top-contributor removal is actually rerun and exposes its resulting expectancy.
3. Token uses the frozen correlated-cluster identity, not ad-hoc post-outcome clustering.
4. Venue, variant, execution artifact, regime, and trade verdicts are separate facts.
5. Missing complete lineage or rows yields BLOCKED rather than an empty or optimistic panel.
6. The panel reports exact inputs and is reproducible from immutable artifacts.

## Testing Requirements
- Unit: Test contribution arithmetic, removal reruns, cluster identity, and missing-lineage blocking.
- Integration tests: MANDATORY (no mocks). Build a real concentrated synthetic execution result, remove each top contributor, and verify separate verdicts against an independent recomputation.
- Commands to run: `uv run pytest tests/lab/test_dominance.py`.

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
- [ ] AC #1: Panel reports contribution and removal effects for every declared axis.
- [ ] AC #2: Top-contributor removal is actually rerun and exposes its resulting expectancy.
- [ ] AC #3: Token uses the frozen correlated-cluster identity, not ad-hoc post-outcome clustering.
- [ ] AC #4: Venue, variant, execution artifact, regime, and trade verdicts are separate facts.
- [ ] AC #5: Missing complete lineage or rows yields BLOCKED rather than an empty or optimistic panel.
- [ ] AC #6: The panel reports exact inputs and is reproducible from immutable artifacts.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:28Z dep_added: blocked_by VK-2g0f
- 2026-09-18T23:31:28Z dep_added: blocked_by VK-8ch2
- 2026-09-18T23:31:30Z dep_added: blocks VK-2e0k
- 2026-09-18T23:31:44Z dep_added: blocks VK-vqvy

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-2e0k]], [[VK-vqvy]]
- Blocked by: [[VK-2g0f]], [[VK-8ch2]]

## Comments
