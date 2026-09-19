---
id: VK-21gm
title: "Render complete Evidence Cards"
status: open
priority: 2
type: feature
labels: [integration, phase-1]
parent: VK-rakf
created_at: 2026-09-18T23:31:34Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:224def70a8f2f771dfcbe8df7322a1e47636f1c240f277b62de3be3495c18450"
blocked_by: [VK-bns7, VK-2e0k, VK-rkdr]
blocks: [VK-6khc, VK-ealt, VK-hiuk]
---

## Description
## USER INTENT
The owner needs every mandatory decision input visible and distinguishable from computed gate state, advisory opinion, and the owner decision.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Render an Evidence Card projection with each DESIGN field or a labeled one-action drill-down. Separate evidence, inspectable gate calculation, gate state, policy disposition/version, optional advisory recommendation, and owner decision slot. Include evidence quantity and full effective-evidence disclosure, reconciliation, performance assumptions and four adverse classes, benchmark, concentration, robustness, calibration, dual temporal status, integrity/quarantine, lineage/budgets, next action/current distance, and delta. Missing mandatory evidence renders BLOCKED and is never omitted. Recommendation remains visually and structurally distinct.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Writing a new decision or recommendation: separate decision/auth work.
- Alert delivery: Phase 2.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~7 files, under 650 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/scoreboard/evidence_card.py -> project_evidence_card(snapshot_hash: str, policy: ProjectionPolicy, format: OutputFormat) -> EvidenceCardProjection

CONSUMES:
- VK-bns7: src/gauntlet/decisions/reconstructor.py -> reconstruct_snapshot(snapshot_hash: str, data_root: Path) -> SnapshotReconstruction
  spec: reconstruct_snapshot(snapshot_hash: str, data_root: Path) -> SnapshotReconstruction
- VK-2e0k: src/gauntlet/policy/engine.py -> evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
  spec: evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult

### Acceptance Criteria (story contract)
1. Card includes every normative field group or a labeled one-action drill-down to it.
2. Evidence, gate arithmetic, computed state, policy disposition, advisory recommendation, and owner decision slot are separate facts.
3. Gate arithmetic retains rule IDs, formulas, inputs, thresholds, per-rule states, and selected precedence branch.
4. All four adverse scenario classes and both dual-temporal statuses are visible with PASS/FAIL/PENDING labels.
5. Missing or stale mandatory evidence projects BLOCKED with the dependency reason; no synthetic metric hides a gap.
6. Output supports JSON, Markdown, no-color, ASCII fallback, and textual state labels independent of color.
7. Recommendation identity/version/visibility is distinct and never presented as deterministic gate consequence.

## Testing Requirements
- Unit: Test mandatory-field coverage, blocked rendering, machine-readable states, and projection determinism.
- Integration tests: MANDATORY (no mocks). Project real valid, incomplete, quarantined, and recommendation-visible snapshots; verify every field resolves to value or labeled BLOCKED and hashes regenerate.
- Commands to run: `uv run pytest tests/scoreboard/test_evidence_card.py`.

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
- Epic containment: VK-rakf.

### proof
- [ ] AC #1: Card includes every normative field group or a labeled one-action drill-down to it.
- [ ] AC #2: Evidence, gate arithmetic, computed state, policy disposition, advisory recommendation, and owner decision slot are separate facts.
- [ ] AC #3: Gate arithmetic retains rule IDs, formulas, inputs, thresholds, per-rule states, and selected precedence branch.
- [ ] AC #4: All four adverse scenario classes and both dual-temporal statuses are visible with PASS/FAIL/PENDING labels.
- [ ] AC #5: Missing or stale mandatory evidence projects BLOCKED with the dependency reason; no synthetic metric hides a gap.
- [ ] AC #6: Output supports JSON, Markdown, no-color, ASCII fallback, and textual state labels independent of color.
- [ ] AC #7: Recommendation identity/version/visibility is distinct and never presented as deterministic gate consequence.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: consume authoritative performance panel

GENERAL RULE SWEEP: Every Evidence Card field is a projection of persisted computed evidence, never an invented value.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-rkdr: src/gauntlet/lab/performance.py -> compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel
  spec: compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel
- VK-rkdr: src/gauntlet/lab/performance.py -> compute_regime_performance(rows: RowLevelReturns, regime_policy: RegimePolicy) -> RegimePerformancePanel
  spec: compute_regime_performance(rows: RowLevelReturns, regime_policy: RegimePolicy) -> RegimePerformancePanel

### Acceptance Criteria (repair revision)
1. Performance, benchmark, adverse-scenario, and regime fields render from PerformancePanel/RegimePerformancePanel or explicit BLOCKED/missing labels.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: Performance, benchmark, adverse-scenario, and regime fields render from PerformancePanel/RegimePerformancePanel or explicit BLOCKED/missing labels.


## History
- 2026-09-18T23:31:34Z dep_added: blocked_by VK-bns7
- 2026-09-18T23:31:34Z dep_added: blocked_by VK-2e0k
- 2026-09-18T23:31:34Z dep_added: blocks VK-6khc
- 2026-09-18T23:31:35Z dep_added: blocks VK-ealt
- 2026-09-18T23:31:46Z dep_added: blocks VK-hiuk
- 2026-09-19T01:37:43Z dep_added: blocked_by VK-rkdr

## Links
- Parent: [[VK-rakf]]
- Blocks: [[VK-6khc]], [[VK-ealt]], [[VK-hiuk]]
- Blocked by: [[VK-bns7]], [[VK-2e0k]], [[VK-rkdr]]

## Comments
