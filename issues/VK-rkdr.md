---
id: VK-rkdr
title: "Compute after-cost performance panels"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-19T01:37:42Z
created_by: speed
updated_at: 2026-09-19T01:39:43Z
content_hash: "sha256:90e1e6a2c92db2393de9296da71bcde9f432c82f3e04accb1792c8514e218020"
blocked_by: [VK-2g0f, VK-8ch2]
blocks: [VK-2e0k, VK-1ptl, VK-21gm, VK-vqvy]
was_blocked_by: [VK-jkkn]
---

## Description
## USER INTENT
The owner needs one authoritative performance artifact for after-cost expectancy, benchmark-relative results, and regime coverage rather than projections inventing metrics.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement deterministic lab performance kernels from row-level exact-execution returns. Report after-cost expectancy under base and declared adverse scenarios, benchmark identity/window, after-cost excess performance, explicit benchmark-winning conditions, and performance by frozen regime with required-coverage gaps. Preserve row/input hashes, OBSERVED/MODELED labels, scenario versions, effective-count reference, and a canonical panel artifact hash. Missing dependencies or price-only inputs block rather than synthesizing performance.

Phase 1 boundaries:
- No order placement, real-money exposure, public API, daemon, multi-tenant access, or social claim.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted.

## OUT OF SCOPE
- Choosing promotion thresholds or aggregate precedence: owned by the deterministic policy engine.
- Rendering fields: owned by scoreboard and Evidence Card projections.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 600 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/lab/performance.py -> compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel
- src/gauntlet/lab/performance.py -> compute_regime_performance(rows: RowLevelReturns, regime_policy: RegimePolicy) -> RegimePerformancePanel

CONSUMES:
- VK-2g0f: src/gauntlet/judge/exact_execution.py -> evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun
  spec: evaluate_exact_execution(trades: LockedTrades, reserves: ReserveSeries, policy: ExecutionPolicy) -> ExactExecutionRun
- VK-8ch2: src/gauntlet/lab/effective_evidence.py -> compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel
  spec: compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig

### Acceptance Criteria (story contract)
1. The panel reports after-cost expectancy for the base case and every declared fee, slippage/impact, fill-failure, and latency adverse scenario with numeric inputs and versions.
2. Benchmark output names identity and comparison window, reports after-cost excess performance, and states every condition under which the benchmark wins.
3. Regime output reports performance for each frozen regime, marks required gaps, and never turns missing coverage into PASS.
4. Inputs retain exact row, trade, reserve, benchmark, policy, config, and effective-evidence hashes.
5. OBSERVED and MODELED components are labeled separately; a rule requiring observed outcomes cannot consume a MODELED substitute.
6. Missing reserve, benchmark, regime, lineage, or row-level dependency yields BLOCKED with affected metrics rather than a neutral or fabricated value.

## Testing Requirements
- Unit: Test after-cost arithmetic, benchmark excess, losing conditions, regime gaps, labels, hashes, and blocking paths with small numeric oracles.
- Integration tests: MANDATORY (no mocks). Compute a real panel from exact row-level outputs and a registered benchmark, remove one dependency on a copy, and prove BLOCKED without affecting the original artifact.
- Commands to run: `uv run pytest tests/lab/test_performance.py`.

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
- Epic containment: VK-0auj.

### proof
- [ ] AC #1: The panel reports after-cost expectancy for the base case and every declared fee, slippage/impact, fill-failure, and latency adverse scenario with numeric inputs and versions.
- [ ] AC #2: Benchmark output names identity and comparison window, reports after-cost excess performance, and states every condition under which the benchmark wins.
- [ ] AC #3: Regime output reports performance for each frozen regime, marks required gaps, and never turns missing coverage into PASS.
- [ ] AC #4: Inputs retain exact row, trade, reserve, benchmark, policy, config, and effective-evidence hashes.
- [ ] AC #5: OBSERVED and MODELED components are labeled separately; a rule requiring observed outcomes cannot consume a MODELED substitute.
- [ ] AC #6: Missing reserve, benchmark, regime, lineage, or row-level dependency yields BLOCKED with affected metrics rather than a neutral or fabricated value.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T01:37:42Z dep_added: blocked_by VK-2g0f
- 2026-09-19T01:37:42Z dep_added: blocked_by VK-8ch2
- 2026-09-19T01:37:42Z dep_added: blocked_by VK-jkkn
- 2026-09-19T01:37:43Z dep_added: blocks VK-2e0k
- 2026-09-19T01:37:43Z dep_added: blocks VK-1ptl
- 2026-09-19T01:37:43Z dep_added: blocks VK-21gm
- 2026-09-19T01:37:43Z dep_added: blocks VK-vqvy
- 2026-09-19T04:41:27Z dep_removed: was_blocked_by VK-jkkn

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-2e0k]], [[VK-1ptl]], [[VK-21gm]], [[VK-vqvy]]
- Blocked by: [[VK-2g0f]], [[VK-8ch2]]
- Was blocked by: [[VK-jkkn]]

## Comments

### 2026-09-19T01:39:43Z speed
RECOMMEND hard-tdd: after-cost, benchmark, and regime arithmetic directly feed promotion gates. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
