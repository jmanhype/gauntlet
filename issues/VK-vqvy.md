---
id: VK-vqvy
title: "E2e: review a synthetic candidate through independent evidence"
status: open
priority: 1
type: feature
labels: [phase-1, capstone, e2e]
parent: VK-0auj
created_at: 2026-09-18T23:31:41Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:da8c83cbffa72021ba74f327ddb79d03a3bd07882ca68b1c8e12d7888c8aadb7"
blocked_by: [VK-2g0f, VK-sbdy, VK-8ch2, VK-zvia, VK-aumt, VK-wrce, VK-l747, VK-rkdr]
blocks: [VK-hiuk]
was_blocked_by: [VK-0c4c, VK-ddoh]
---

## Description
## USER INTENT
The owner can run a registered synthetic candidate through judge execution and independently reconstruct every mandatory evidence panel.

Observable outcome: the owner can run the declared E2e command, inspect or display its output, and verify that the full path returns the declared result, stores its immutable artifacts, and emits the corresponding hash-verified events.

## Context (Embedded)
This is the E2e capstone for epic VK-0auj. It must exercise the completed epic from the owner perspective after every sibling story. It verifies real local files, chains, subprocesses, outputs, and exit codes. It does not establish new module semantics.

Phase 1 boundaries:
- No order placement, real-money exposure, public API, daemon, multi-tenant access, or social claim.
- Paper/simulated records are evidence, not executions.
- No database engine dependency; all projections regenerate from immutable files.

## OUT OF SCOPE
- New feature behavior or repaired implementation semantics: a failing capstone creates a bug story rather than broadening this story.
- Live trading, public exposure, or remote access: explicit non-goals.

## DIFF BUDGET
~2 files, under 350 changed LOC.

## Boundary Map
PRODUCES:
- tests/e2e/test_judge_lab_evidence.py -> owner-perspective judge/lab drill

CONSUMES:
- VK-0c4c: src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
  spec: evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
- VK-2g0f: src/gauntlet/judge/exact_execution.py -> evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun
  spec: evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun
- VK-ddoh: src/gauntlet/judge/prospective.py -> append_signal(record: ProspectiveSignal) -> ProspectiveRecord
  spec: append_signal(record: ProspectiveSignal) -> ProspectiveRecord
- VK-sbdy: src/gauntlet/judge/transfer.py -> evaluate_transfer(request: TransferRequest) -> TransferEvaluation
  spec: evaluate_transfer(request: TransferRequest) -> TransferEvaluation
- VK-8ch2: src/gauntlet/lab/effective_evidence.py -> compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel
  spec: compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel
- VK-zvia: src/gauntlet/lab/calibration.py -> compute_calibration(records: list[ConfidenceOutcome], policy: CalibrationPolicy) -> CalibrationPanel
  spec: compute_calibration(records: list[ConfidenceOutcome], policy: CalibrationPolicy) -> CalibrationPanel
- VK-aumt: src/gauntlet/lab/robustness.py -> compute_robustness(trades: LockedTrades, lineage: TrialLineage, policy: StatisticalPolicy) -> RobustnessPanel
  spec: compute_robustness(trades: LockedTrades, lineage: TrialLineage, policy: StatisticalPolicy) -> RobustnessPanel
- VK-wrce: src/gauntlet/lab/dominance.py -> compute_dominance(rows: RowLevelReturns, lineage: TrialLineage) -> DominancePanel
  spec: compute_dominance(rows: RowLevelReturns, lineage: TrialLineage) -> DominancePanel
- VK-l747: src/gauntlet/lab/reconciliation.py -> reconcile_claim(claim: ClaimDecomposition, recomputation: IndependentMetric, policy: ReconciliationPolicy) -> ReconciliationReport
  spec: reconcile_claim(claim: ClaimDecomposition, recomputation: IndependentMetric, policy: ReconciliationPolicy) -> ReconciliationReport

### Acceptance Criteria (story contract)
1. A real synthetic trial with registered Solana data, reserves, prospective signals, Hyperliquid transfer population, model confidence, search lineage, and one external claim flows through every judge and lab artifact without pooled venue counts.
2. The E2e command or test exits nonzero on the first integrity, authorization, dependency, projection, or contract failure and emits machine-readable JSON identifying the failed stage.
3. The run records canonical success or error events with the prior event head and never invents an artifact.
4. 4. Raw and effective counts are separately reported and overlapping/clustered observations do not inflate independent evidence. 5. Removing one reserve makes the affected Solana quote an evidence gap rather than a fill. 6. Concentration, robustness, calibration, reconciliation, and transfer outputs are reconstructible from immutable row-level artifacts. 7. A late signal is historical and cannot satisfy prospective credit.

## Testing Requirements
- E2e tests ONLY. No unit tests, no integration tests. Tests must exercise the full system as a user would. No mocks of any kind.
- Commands to run: `uv run pytest tests/e2e/test_judge_lab_evidence.py`.

## MANDATORY SKILLS
- None identified.

## Delivery Requirements
- Developer must paste unedited E2e output and artifact/event hashes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label.

## nd_contract
status: new

### evidence
- Created 2026-09-18 as the final capstone of epic VK-0auj.
- All sibling dependencies are explicitly recorded in nd.

### proof
- [ ] AC #1: Owner-perspective scenario executes successfully.
- [ ] AC #2: Failure path exits nonzero with machine-readable JSON.
- [ ] AC #3: Event integrity and no-artifact-on-error behavior are verified.
- [ ] AC #4: 4. Raw and effective counts are separately reported and overlapping/clustered observations do not inflate independent evidence. 5. Removing one reserve makes the affected Solana quote an evidence gap rather than a fill. 6. Concentration, robustness, calibration, reconciliation, and transfer outputs are reconstructible from immutable row-level artifacts. 7. A late signal is historical and cannot satisfy prospective credit.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: include performance sibling

GENERAL RULE SWEEP: Every epic capstone is blocked by every sibling.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-rkdr: src/gauntlet/lab/performance.py -> compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel
  spec: compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel

### Acceptance Criteria (repair revision)
1. The judge/lab E2e drill reconstructs the authoritative after-cost, benchmark-relative, and regime performance panel.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The judge/lab E2e drill reconstructs the authoritative after-cost, benchmark-relative, and regime performance panel.


## History
- 2026-09-18T23:31:41Z dep_added: blocked_by VK-0c4c
- 2026-09-18T23:31:42Z dep_added: blocked_by VK-2g0f
- 2026-09-18T23:31:42Z dep_added: blocked_by VK-ddoh
- 2026-09-18T23:31:42Z dep_added: blocked_by VK-sbdy
- 2026-09-18T23:31:43Z dep_added: blocked_by VK-8ch2
- 2026-09-18T23:31:43Z dep_added: blocked_by VK-zvia
- 2026-09-18T23:31:43Z dep_added: blocked_by VK-aumt
- 2026-09-18T23:31:44Z dep_added: blocked_by VK-wrce
- 2026-09-18T23:31:44Z dep_added: blocked_by VK-l747
- 2026-09-18T23:31:48Z dep_added: blocks VK-hiuk
- 2026-09-19T01:37:43Z dep_added: blocked_by VK-rkdr
- 2026-09-19T05:50:41Z dep_removed: was_blocked_by VK-0c4c
- 2026-09-19T16:28:10Z dep_removed: was_blocked_by VK-ddoh

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-hiuk]]
- Blocked by: [[VK-2g0f]], [[VK-sbdy]], [[VK-8ch2]], [[VK-zvia]], [[VK-aumt]], [[VK-wrce]], [[VK-l747]], [[VK-rkdr]]
- Was blocked by: [[VK-0c4c]], [[VK-ddoh]]

## Comments
