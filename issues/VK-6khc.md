---
id: VK-6khc
title: "Export self-contained forensic bundles"
status: open
priority: 2
type: feature
labels: [integration, phase-1]
parent: VK-rakf
created_at: 2026-09-18T23:31:34Z
created_by: speed
updated_at: 2026-09-18T23:31:34Z
content_hash: "sha256:68da5e46c0a95667ea5d01b1f089748be1f2fbe2f23653121e430da8972c1331"
blocked_by: [VK-21gm, VK-bns7]
blocks: [VK-hiuk]
---

## Description
## USER INTENT
The owner can give a reviewer one bundle containing the exact decision, evidence, provenance, and replay checks without access to the live data root.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement `export_audit_bundle`. Copy or content-address every referenced artifact into an append-only self-contained directory with snapshot, reveal log, policy versions, code manifest, provenance graph, owner extensions, relevant hashes, and verification report. Create a bundle manifest and Merkle root. Export fails on missing artifact, verification failure, invalid destination policy, or a non-empty destination. The bundle verifies after the original data root is unavailable.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Publishing or transmitting a bundle: owner-controlled and outside Phase 1.
- Alert export: Phase 2.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/scoreboard/forensic.py -> export_audit_bundle(snapshot_hash: str, policy: BundlePolicy, destination: DestinationPolicy) -> AuditBundle

CONSUMES:
- VK-21gm: src/gauntlet/scoreboard/evidence_card.py -> project_evidence_card(snapshot_hash: str, policy: ProjectionPolicy, format: OutputFormat) -> EvidenceCardProjection
  spec: project_evidence_card(snapshot_hash: str, policy: ProjectionPolicy, format: OutputFormat) -> EvidenceCardProjection
- VK-bns7: src/gauntlet/decisions/writer.py -> write_decision_snapshot(request: SnapshotRequest) -> DecisionSnapshot
  spec: write_decision_snapshot(request: SnapshotRequest) -> DecisionSnapshot

### Acceptance Criteria (story contract)
1. Bundle contains snapshot, exact evidence, policy, provenance graph, transformation/run records, reveal log, recommendation, owner extensions, code manifest, and verification report.
2. Manifest records every content hash/path and a Merkle root; bundle append is write-once.
3. Export verifies source snapshot and all referenced artifacts before success.
4. A missing artifact or verification failure returns `ARTIFACT_MISSING` or `VERIFICATION_FAILED` and creates no partial bundle.
5. A non-empty destination fails without overwrite.
6. Bundle verification succeeds when the original data root is unavailable.
7. No credential, private owner material, signature, or unredacted secret enters the export.

## Testing Requirements
- Unit: Test manifest construction, Merkle verification, destination errors, and secret exclusion.
- Integration tests: MANDATORY (no mocks). Export a real snapshot with evidence/policy/owner extensions, move the original data root aside, and verify the self-contained bundle independently.
- Commands to run: `uv run pytest tests/scoreboard/test_forensic_export.py`.

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
- [ ] AC #1: Bundle contains snapshot, exact evidence, policy, provenance graph, transformation/run records, reveal log, recommendation, owner extensions, code manifest, and verification report.
- [ ] AC #2: Manifest records every content hash/path and a Merkle root; bundle append is write-once.
- [ ] AC #3: Export verifies source snapshot and all referenced artifacts before success.
- [ ] AC #4: A missing artifact or verification failure returns `ARTIFACT_MISSING` or `VERIFICATION_FAILED` and creates no partial bundle.
- [ ] AC #5: A non-empty destination fails without overwrite.
- [ ] AC #6: Bundle verification succeeds when the original data root is unavailable.
- [ ] AC #7: No credential, private owner material, signature, or unredacted secret enters the export.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:34Z dep_added: blocked_by VK-21gm
- 2026-09-18T23:31:35Z dep_added: blocked_by VK-bns7
- 2026-09-18T23:31:46Z dep_added: blocks VK-hiuk

## Links
- Parent: [[VK-rakf]]
- Blocks: [[VK-hiuk]]
- Blocked by: [[VK-21gm]], [[VK-bns7]]

## Comments
