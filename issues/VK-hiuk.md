---
id: VK-hiuk
title: "E2e: operate GAUNTLET through read-only surfaces"
status: open
priority: 3
type: feature
labels: [phase-1, capstone, e2e]
parent: VK-rakf
created_at: 2026-09-18T23:31:45Z
created_by: speed
updated_at: 2026-09-18T23:31:45Z
content_hash: "sha256:0dad79ae5c23836bba3384ecf0fcb0f656d09156bb2a9f64a2b246f76de6fd43"
blocked_by: [VK-1ptl, VK-21gm, VK-6khc, VK-ealt, VK-dblr, VK-3f9f, VK-ldg1, VK-vqvy, VK-uyca]
---

## Description
## USER INTENT
The owner can use the CLI or local FastMCP surface to review current evidence, render reports, and export an audit bundle without exposing authority or a trading verb.

Observable outcome: the owner can run the declared E2e command, inspect or display its output, and verify that the full path returns the declared result, stores its immutable artifacts, and emits the corresponding hash-verified events.

## Context (Embedded)
This is the E2e capstone for epic VK-rakf. It must exercise the completed epic from the owner perspective after every sibling story. It verifies real local files, chains, subprocesses, outputs, and exit codes. It does not establish new module semantics.

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
- tests/e2e/test_phase1_surfaces.py -> owner-perspective full-surface drill

CONSUMES:
- VK-1ptl: src/gauntlet/scoreboard/scoreboard.py -> project_scoreboard(snapshot_refs: list[SnapshotRef], as_of: datetime) -> ScoreboardProjection
  spec: project_scoreboard(snapshot_refs: list[SnapshotRef], as_of: datetime) -> ScoreboardProjection
- VK-21gm: src/gauntlet/scoreboard/evidence_card.py -> project_evidence_card(snapshot_hash: str, policy: ProjectionPolicy, format: OutputFormat) -> EvidenceCardProjection
  spec: project_evidence_card(snapshot_hash: str, policy: ProjectionPolicy, format: OutputFormat) -> EvidenceCardProjection
- VK-6khc: src/gauntlet/scoreboard/forensic.py -> export_audit_bundle(snapshot_hash: str, policy: BundlePolicy, destination: DestinationPolicy) -> AuditBundle
  spec: export_audit_bundle(snapshot_hash: str, policy: BundlePolicy, destination: DestinationPolicy) -> AuditBundle
- VK-ealt: src/gauntlet/scoreboard/report.py -> write_report(scope: ReportScope, formats: set[ReportFormat]) -> StaticReport
  spec: write_report(scope: ReportScope, formats: set[ReportFormat]) -> StaticReport
- VK-dblr: src/gauntlet/services/__init__.py -> dispatch_service(operation: ServiceOperation, envelope: ServiceEnvelope) -> ServiceEnvelope
  spec: dispatch_service(operation: ServiceOperation, envelope: ServiceEnvelope) -> ServiceEnvelope

### Acceptance Criteria (story contract)
1. A real owner run invokes matching CLI and local FastMCP operations, generates scoreboard/card/report outputs, exports a self-contained bundle, and verifies it after moving the original data root aside.
2. The E2e command or test exits nonzero on the first integrity, authorization, dependency, projection, or contract failure and emits machine-readable JSON identifying the failed stage.
3. The run records canonical success or error events with the prior event head and never invents an artifact.
4. 4. CLI and FastMCP canonical outputs, hashes, and events match for representative success and error paths. 5. The scoreboard prioritizes action and integrity over P&L and renders every mandatory field or labeled BLOCKED drill-down. 6. The audit bundle verifies independently with no secret or private owner material. 7. No interface exposes order placement, remote public access, or a collector call from a read path.

## Testing Requirements
- E2e tests ONLY. No unit tests, no integration tests. Tests must exercise the full system as a user would. No mocks of any kind.
- Commands to run: `uv run pytest tests/e2e/test_phase1_surfaces.py`.

## MANDATORY SKILLS
- None identified.

## Delivery Requirements
- Developer must paste unedited E2e output and artifact/event hashes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label.

## nd_contract
status: new

### evidence
- Created 2026-09-18 as the final capstone of epic VK-rakf.
- All sibling dependencies are explicitly recorded in nd.

### proof
- [ ] AC #1: Owner-perspective scenario executes successfully.
- [ ] AC #2: Failure path exits nonzero with machine-readable JSON.
- [ ] AC #3: Event integrity and no-artifact-on-error behavior are verified.
- [ ] AC #4: 4. CLI and FastMCP canonical outputs, hashes, and events match for representative success and error paths. 5. The scoreboard prioritizes action and integrity over P&L and renders every mandatory field or labeled BLOCKED drill-down. 6. The audit bundle verifies independently with no secret or private owner material. 7. No interface exposes order placement, remote public access, or a collector call from a read path.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:46Z dep_added: blocked_by VK-1ptl
- 2026-09-18T23:31:46Z dep_added: blocked_by VK-21gm
- 2026-09-18T23:31:46Z dep_added: blocked_by VK-6khc
- 2026-09-18T23:31:47Z dep_added: blocked_by VK-ealt
- 2026-09-18T23:31:47Z dep_added: blocked_by VK-dblr
- 2026-09-18T23:31:47Z dep_added: blocked_by VK-3f9f
- 2026-09-18T23:31:47Z dep_added: blocked_by VK-ldg1
- 2026-09-18T23:31:48Z dep_added: blocked_by VK-vqvy
- 2026-09-18T23:31:48Z dep_added: blocked_by VK-uyca

## Links
- Parent: [[VK-rakf]]
- Blocked by: [[VK-1ptl]], [[VK-21gm]], [[VK-6khc]], [[VK-ealt]], [[VK-dblr]], [[VK-3f9f]], [[VK-ldg1]], [[VK-vqvy]], [[VK-uyca]]

## Comments
