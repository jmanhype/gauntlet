---
id: VK-ealt
title: "Write static owner evidence reports"
status: open
priority: 3
type: feature
labels: [integration, phase-1]
parent: VK-rakf
created_at: 2026-09-18T23:31:35Z
created_by: speed
updated_at: 2026-09-18T23:31:35Z
content_hash: "sha256:5a25403bf706ede1a4ae43d5a15ee23df75961e367b6da4f70a9080c98890c9e"
blocked_by: [VK-1ptl, VK-21gm]
blocks: [VK-dblr, VK-hiuk]
---

## Description
## USER INTENT
The owner needs complete local reports with explicit stop, downgrade, renewal, and promotion conditions even without a dashboard.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Generate static Markdown/HTML plus JSON reports under `data/reports`. Report scoreboard sections, candidate Evidence Cards, blocked/quarantined evidence, family budgets, null results, execution assumptions, calibration, reconciliation, and next explicit actions. Reports are deterministic projections, accessible with textual states, mobile-readable, no mandatory font, color-blind-safe, and support no-color/ASCII. A null result is valuable output and must be preserved with attribution. Reports never make public performance claims.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- SMS/Hunter Stack alerts and web dashboards: Phase 2/3.
- External distribution or public claims: business non-goal.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 500 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/scoreboard/report.py -> write_report(scope: ReportScope, formats: set[ReportFormat]) -> StaticReport

CONSUMES:
- VK-1ptl: src/gauntlet/scoreboard/scoreboard.py -> project_scoreboard(snapshot_refs: list[SnapshotRef], as_of: datetime) -> ScoreboardProjection
  spec: project_scoreboard(snapshot_refs: list[SnapshotRef], as_of: datetime) -> ScoreboardProjection
- VK-21gm: src/gauntlet/scoreboard/evidence_card.py -> project_evidence_card(snapshot_hash: str, policy: ProjectionPolicy, format: OutputFormat) -> EvidenceCardProjection
  spec: project_evidence_card(snapshot_hash: str, policy: ProjectionPolicy, format: OutputFormat) -> EvidenceCardProjection

### Acceptance Criteria (story contract)
1. Markdown, HTML, and JSON outputs are generated under `data/reports` with stable projection hashes.
2. Every candidate and family shows explicit next kill, downgrade, renewal, stop, or promotion condition and current distance.
3. Blocked, quarantined, missing, stale, and invalid evidence is prominent rather than buried.
4. Null/rejected experiments and attribution remain visible.
5. Textual states satisfy PASS, FAIL, BLOCKED, INSUFFICIENT_EVIDENCE, STALE, and QUARANTINED accessibility requirements.
6. Reports contain no order-placement action, public claim, credential, or synthesized missing field.

## Testing Requirements
- Unit: Test deterministic rendering, accessibility states, JSON schema, and report completeness.
- Integration tests: MANDATORY (no mocks). Generate real reports from the scoreboard/card projections, delete them, regenerate, and compare hashes while proving blocked and null-result visibility.
- Commands to run: `uv run pytest tests/scoreboard/test_static_report.py`.

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
- [ ] AC #1: Markdown, HTML, and JSON outputs are generated under `data/reports` with stable projection hashes.
- [ ] AC #2: Every candidate and family shows explicit next kill, downgrade, renewal, stop, or promotion condition and current distance.
- [ ] AC #3: Blocked, quarantined, missing, stale, and invalid evidence is prominent rather than buried.
- [ ] AC #4: Null/rejected experiments and attribution remain visible.
- [ ] AC #5: Textual states satisfy PASS, FAIL, BLOCKED, INSUFFICIENT_EVIDENCE, STALE, and QUARANTINED accessibility requirements.
- [ ] AC #6: Reports contain no order-placement action, public claim, credential, or synthesized missing field.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:35Z dep_added: blocked_by VK-1ptl
- 2026-09-18T23:31:35Z dep_added: blocked_by VK-21gm
- 2026-09-18T23:31:37Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:47Z dep_added: blocks VK-hiuk

## Links
- Parent: [[VK-rakf]]
- Blocks: [[VK-dblr]], [[VK-hiuk]]
- Blocked by: [[VK-1ptl]], [[VK-21gm]]

## Comments
