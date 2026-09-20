---
id: VK-2e0k
title: "Evaluate deterministic gate precedence"
status: open
priority: 0
type: feature
labels: [integration, phase-1]
parent: VK-1rbc
created_at: 2026-09-18T23:31:29Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:f5162368884540abf756b7ccb5ad971cbcaf29f5aac3d5ab7dd119ea86f526cd"
blocked_by: [VK-8ch2, VK-zvia, VK-aumt, VK-wrce, VK-l747, VK-rkdr]
blocks: [VK-bns7, VK-21gm, VK-dblr, VK-uyca]
was_blocked_by: [VK-kmbs, VK-aej2, VK-0pfo]
---

## Description
## USER INTENT
The owner needs a deterministic gate that cannot be persuaded by an agent or a profitable but fragile claim.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement the pure gate/policy engine as a function of `(evidence_bundle, ruleset_manifest, policy_manifest, dependency_state, as_of)`. Rules return PASS, FAIL, BLOCKED, or PENDING/INSUFFICIENT_EVIDENCE. Aggregate precedence is fixed: any BLOCKED, else any FAIL, else any PENDING or INSUFFICIENT_EVIDENCE, else PASS. Version immutable manifests for evidence-policy, gate-rules, disposition-policy, transitions, effective-evidence, alert-policy, and risk-policy. The engine never reads wall-clock/current data, calls an LLM, fetches, or infers thresholds. Unknown outputs become BLOCKED. Each rule records IDs, versions, material inputs/hashes, observed value, comparator, threshold, observation labels, state, reason, and disposition derivation.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Rendering gate arithmetic: Evidence Card story.
- Owner override semantics: authorization story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 700 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/policy/engine.py -> evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
- src/gauntlet/policy/manifests.py -> load_policy_manifest(path: Path) -> PolicyManifest

CONSUMES:
- VK-kmbs: src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
  spec: evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
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
- VK-0pfo: src/gauntlet/risk/kernel.py -> evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult
  spec: evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult

### Acceptance Criteria (story contract)
1. All four rule states are supported and exhaustive combinations prove BLOCKED > FAIL > INSUFFICIENT_EVIDENCE > PASS.
2. Engine output is deterministic for identical immutable inputs and `as_of`; it performs no I/O beyond provided hashed artifacts.
3. Every rule result exposes formula/rule IDs, policy/ruleset versions, input hashes, values, comparators, thresholds, labels, states, and reasons.
4. Unknown rule output, malformed panel contract, hash mismatch, or stale dependency evaluation becomes BLOCKED.
5. Risk disposition remains separate from gate arithmetic and evidence PASS cannot override a risk boundary.
6. An old snapshot continues evaluating under its recorded manifest hashes after a new policy version exists.
7. Missing effective observations with otherwise valid lineage yields INSUFFICIENT_EVIDENCE rather than FAIL.

## Testing Requirements
- Unit: Exhaustively test precedence, rule schemas, manifest compatibility, unknown outputs, and historical policy selection.
- Integration tests: MANDATORY (no mocks). Evaluate a real synthetic bundle across PASS, FAIL, BLOCKED, and pending windows using registered panels, then upgrade policy and prove historical interpretation is unchanged.
- Commands to run: `uv run pytest tests/policy/test_gate_engine.py`.

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
- Epic containment: VK-1rbc.

### proof
- [ ] AC #1: All four rule states are supported and exhaustive combinations prove BLOCKED > FAIL > INSUFFICIENT_EVIDENCE > PASS.
- [ ] AC #2: Engine output is deterministic for identical immutable inputs and `as_of`; it performs no I/O beyond provided hashed artifacts.
- [ ] AC #3: Every rule result exposes formula/rule IDs, policy/ruleset versions, input hashes, values, comparators, thresholds, labels, states, and reasons.
- [ ] AC #4: Unknown rule output, malformed panel contract, hash mismatch, or stale dependency evaluation becomes BLOCKED.
- [ ] AC #5: Risk disposition remains separate from gate arithmetic and evidence PASS cannot override a risk boundary.
- [ ] AC #6: An old snapshot continues evaluating under its recorded manifest hashes after a new policy version exists.
- [ ] AC #7: Missing effective observations with otherwise valid lineage yields INSUFFICIENT_EVIDENCE rather than FAIL.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: consume authoritative performance panel

GENERAL RULE SWEEP: Every displayed or gated performance fact must originate from a lab computation artifact, not a projection.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-rkdr: src/gauntlet/lab/performance.py -> compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel
  spec: compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel
- VK-rkdr: src/gauntlet/lab/performance.py -> compute_regime_performance(rows: RowLevelReturns, regime_policy: RegimePolicy) -> RegimePerformancePanel
  spec: compute_regime_performance(rows: RowLevelReturns, regime_policy: RegimePolicy) -> RegimePerformancePanel

### Acceptance Criteria (repair revision)
1. The gate consumes the authoritative after-cost, benchmark-relative, and regime performance panel hashes.
2. Scoreboard and Evidence Card render only values reconstructible from that panel or explicit BLOCKED labels.
ANCHOR REPAIR: follow P0 synthetic precedence skeleton

GENERAL RULE SWEEP: The deterministic P0 pattern must be established with synthetic inputs before full producer integration.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:
- No additional PRODUCES; the original declarations remain applicable except where explicitly superseded below.

CONSUMES:
- VK-aej2: src/gauntlet/policy/precedence.py -> evaluate_precedence(rule_results: list[RuleResult]) -> GateState
  spec: evaluate_precedence(rule_results: list[RuleResult]) -> GateState
- VK-aej2: src/gauntlet/policy/synthetic.py -> build_synthetic_panel_bundle(seed: int) -> SyntheticEvidenceBundle
  spec: build_synthetic_panel_bundle(seed: int) -> SyntheticEvidenceBundle

### Acceptance Criteria (repair revision)
1. The full gate integration consumes the P0 precedence kernel and synthetic contract shape established by the new skeleton story.
2. This story ceases to carry the walking-skeleton label; it is the real-evidence integration slice.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The full gate integration consumes the P0 precedence kernel and synthetic contract shape established by the new skeleton story.
- [ ] Repair AC #2: This story ceases to carry the walking-skeleton label; it is the real-evidence integration slice.


## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The gate consumes the authoritative after-cost, benchmark-relative, and regime performance panel hashes.
- [ ] Repair AC #2: Scoreboard and Evidence Card render only values reconstructible from that panel or explicit BLOCKED labels.


## History
- 2026-09-18T23:31:29Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:29Z dep_added: blocked_by VK-8ch2
- 2026-09-18T23:31:30Z dep_added: blocked_by VK-zvia
- 2026-09-18T23:31:30Z dep_added: blocked_by VK-aumt
- 2026-09-18T23:31:30Z dep_added: blocked_by VK-wrce
- 2026-09-18T23:31:30Z dep_added: blocked_by VK-l747
- 2026-09-18T23:31:31Z dep_added: blocked_by VK-0pfo
- 2026-09-18T23:31:31Z dep_added: blocks VK-bns7
- 2026-09-18T23:31:34Z dep_added: blocks VK-21gm
- 2026-09-18T23:31:36Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:45Z dep_added: blocks VK-uyca
- 2026-09-19T01:37:43Z dep_added: blocked_by VK-rkdr
- 2026-09-19T01:37:43Z dep_added: blocked_by VK-aej2
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs
- 2026-09-19T05:02:19Z dep_removed: was_blocked_by VK-aej2
- 2026-09-20T14:53:40Z dep_removed: was_blocked_by VK-0pfo

## Links
- Parent: [[VK-1rbc]]
- Blocks: [[VK-bns7]], [[VK-21gm]], [[VK-dblr]], [[VK-uyca]]
- Blocked by: [[VK-8ch2]], [[VK-zvia]], [[VK-aumt]], [[VK-wrce]], [[VK-l747]], [[VK-rkdr]]
- Was blocked by: [[VK-kmbs]], [[VK-aej2]], [[VK-0pfo]]

## Comments

### 2026-09-18T23:33:03Z speed
RECOMMEND hard-tdd: exhaustive precedence and historical policy interpretation are the core QC gate. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: exhaustive precedence and historical policy interpretation are the core QC gate. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
