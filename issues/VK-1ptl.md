---
id: VK-1ptl
title: "Project the owner scoreboard"
status: open
priority: 2
type: feature
labels: [integration, phase-1, walking-skeleton]
parent: VK-rakf
created_at: 2026-09-18T23:31:33Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:902257cdbd7d6d1fb0fdf3ff890e6f8dcafd00a4dce18dc56d1dc82bb7c4a0e6"
blocked_by: [VK-bns7, VK-jvku, VK-rkdr]
blocks: [VK-ealt, VK-hiuk]
was_blocked_by: [VK-0pfo]
---

## Description
## USER INTENT
The owner needs a current decision triage view that prioritizes integrity and action rather than P&L or model confidence.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Create the non-authoritative Scoreboard projection from latest valid Decision Snapshots, policy enumerations, dependency state, collection health, budgets, and risk boundaries. Views are Action Required, Blocked/Quarantined, Killed, Archived, and Recently Changed. In-stage sort is owner-action-required, then integrity/blocking condition, then recent material transition, then age/staleness. Show candidate stage, effective evidence, after-cost performance, benchmark comparison, execution assumptions, calibration, trial-budget consumption, and next explicit kill/downgrade/renewal/promotion condition. Never default-sort by P&L, Sharpe, confidence, or recommendation strength.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Phase 3 app, web server, or Telegram: out of Phase 1.
- Recomputing policy with a new manifest while presenting it as historical: prohibited.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/scoreboard/scoreboard.py -> project_scoreboard(snapshot_refs: list[SnapshotRef], as_of: datetime) -> ScoreboardProjection

CONSUMES:
- VK-bns7: src/gauntlet/decisions/reconstructor.py -> reconstruct_snapshot(snapshot_hash: str, data_root: Path) -> SnapshotReconstruction
  spec: reconstruct_snapshot(snapshot_hash: str, data_root: Path) -> SnapshotReconstruction
- VK-jvku: src/gauntlet/audit/health.py -> summarize_collection_health(scope: CollectionScope, as_of: datetime) -> CollectionHealth
  spec: summarize_collection_health(scope: CollectionScope, as_of: datetime) -> CollectionHealth
- VK-0pfo: src/gauntlet/risk/kernel.py -> evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult
  spec: evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult

### Acceptance Criteria (story contract)
1. All five first-class views are present with accessible textual machine-readable states.
2. Sort priority exactly follows owner action, integrity/blocking condition, material transition, then age/staleness.
3. Every track/family shows current status, effective evidence, after-cost performance, benchmark, assumptions, calibration, budget consumption, and next explicit action condition.
4. A snapshot verification failure or missing mandatory field is visible and BLOCKED, never omitted or synthesized.
5. Projection is deterministic for snapshot IDs plus policy/event heads and contains no P&L default ranking.
6. Deleting and regenerating the projection does not alter decisions.

## Testing Requirements
- Unit: Test view classification, sorting, budget fields, accessibility states, determinism, and missing-snapshot behavior.
- Integration tests: MANDATORY (no mocks). Build real projections from multiple synthetic snapshots including quarantined, blocked, killed, and action-required cases; delete outputs and regenerate identical hashes.
- Commands to run: `uv run pytest tests/scoreboard/test_scoreboard.py`.

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
- [ ] AC #1: All five first-class views are present with accessible textual machine-readable states.
- [ ] AC #2: Sort priority exactly follows owner action, integrity/blocking condition, material transition, then age/staleness.
- [ ] AC #3: Every track/family shows current status, effective evidence, after-cost performance, benchmark, assumptions, calibration, budget consumption, and next explicit action condition.
- [ ] AC #4: A snapshot verification failure or missing mandatory field is visible and BLOCKED, never omitted or synthesized.
- [ ] AC #5: Projection is deterministic for snapshot IDs plus policy/event heads and contains no P&L default ranking.
- [ ] AC #6: Deleting and regenerating the projection does not alter decisions.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: consume authoritative performance panel

GENERAL RULE SWEEP: Every displayed metric must have an authoritative computation producer.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-rkdr: src/gauntlet/lab/performance.py -> compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel
  spec: compute_performance(rows: RowLevelReturns, benchmark: BenchmarkSeries, policy: PerformancePolicy) -> PerformancePanel

### Acceptance Criteria (repair revision)
1. After-cost expectancy, benchmark excess/losing conditions, and regime status displayed by the scoreboard come only from the authoritative PerformancePanel.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: After-cost expectancy, benchmark excess/losing conditions, and regime status displayed by the scoreboard come only from the authoritative PerformancePanel.


## History
- 2026-09-18T23:31:33Z dep_added: blocked_by VK-bns7
- 2026-09-18T23:31:33Z dep_added: blocked_by VK-jvku
- 2026-09-18T23:31:33Z dep_added: blocked_by VK-0pfo
- 2026-09-18T23:31:35Z dep_added: blocks VK-ealt
- 2026-09-18T23:31:46Z dep_added: blocks VK-hiuk
- 2026-09-19T01:37:43Z dep_added: blocked_by VK-rkdr
- 2026-09-20T14:53:40Z dep_removed: was_blocked_by VK-0pfo

## Links
- Parent: [[VK-rakf]]
- Blocks: [[VK-ealt]], [[VK-hiuk]]
- Blocked by: [[VK-bns7]], [[VK-jvku]], [[VK-rkdr]]
- Was blocked by: [[VK-0pfo]]

## Comments
