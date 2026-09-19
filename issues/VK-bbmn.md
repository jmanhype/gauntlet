---
id: VK-bbmn
title: "Isolate Scarlett evidence roles"
status: open
priority: 2
type: feature
labels: [external-integration, integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:18Z
created_by: speed
updated_at: 2026-09-18T23:33:48Z
content_hash: "sha256:7f2984034b4d565994459bd11546330ca9f01ea6d088e504353d80c4039ab120"
blocked_by: [VK-pg9j]
blocks: [VK-jvku, VK-l747, VK-ldg1]
---

## Description
## USER INTENT
The owner needs Scarlett claims decomposed and role-isolated so a benchmark or capability claim cannot silently strengthen its own candidate.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Snapshot Scarlett profiles, markets, forecasts, and setups with pagination, rate-limit/backoff metadata, collector version, fetch time, and content hash; preserve duplicate provenance and merge policy. Decompose each claim into claimed metric/capability, source, actual model/process identity, decision role, confidence semantics, materiality tolerance, and provenance. Emit role declarations: Benchmark permits independent comparison only; Candidate/information source requires model lineage and calibration and cannot benchmark that candidate; Audit target supports claim decomposition and cannot itself prove candidate edge. A contamination walk blocks incompatible roles unless explicit redesign and replacement benchmark are approved.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Statistical calibration math: lands in the lab calibration story.
- Owner approval of a role redesign: lands in the authorization story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~7 files, under 650 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/audit/collectors/scarlett.py -> snapshot_scarlett(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
- src/gauntlet/audit/claims.py -> decompose_claim(snapshot: SnapshotDescriptor) -> ClaimDecomposition
- src/gauntlet/audit/roles.py -> declare_role(artifact_id: str, role: ScarlettRole, trial_id: str) -> RoleDeclaration

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
  spec: collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
- VK-kmbs: src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
  spec: register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration

### Acceptance Criteria (story contract)
1. Real-endpoint verification (non-automatable): capture a minimum Scarlett snapshot and retain immutable pagination, fetch metadata, hashes, and a sanitized event.
2. Claim decomposition distinguishes claimed capability, actual model/process identity, decision role, confidence semantics, tolerance, and provenance.
3. Each trial/family receives an explicit role declaration and permitted-use constraints.
4. The provenance walk blocks the same Scarlett artifact as benchmark and candidate/information source without an approved replacement benchmark.
5. An audit-target artifact cannot become candidate-edge evidence without a separate registered candidate trial.
6. Duplicate IDs and merge policy remain reconstructible rather than silently replaced by recency.
7. Rate limiting and partial capture are recorded without credentials or retry storms.

## Testing Requirements
- Unit: Test claim schema, role matrix, duplicate provenance, and incompatible-role combinations.
- Integration tests: MANDATORY (no mocks). Capture the real endpoint, decompose one claim, register two conflicting role declarations, and prove contamination blocks before gate evaluation.
- Commands to run: `uv run pytest tests/audit/test_scarlett_roles.py` plus recorded real-endpoint evidence.

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
- Epic containment: VK-u40v.

### proof
- [ ] AC #1: Real-endpoint verification (non-automatable): capture a minimum Scarlett snapshot and retain immutable pagination, fetch metadata, hashes, and a sanitized event.
- [ ] AC #2: Claim decomposition distinguishes claimed capability, actual model/process identity, decision role, confidence semantics, tolerance, and provenance.
- [ ] AC #3: Each trial/family receives an explicit role declaration and permitted-use constraints.
- [ ] AC #4: The provenance walk blocks the same Scarlett artifact as benchmark and candidate/information source without an approved replacement benchmark.
- [ ] AC #5: An audit-target artifact cannot become candidate-edge evidence without a separate registered candidate trial.
- [ ] AC #6: Duplicate IDs and merge policy remain reconstructible rather than silently replaced by recency.
- [ ] AC #7: Rate limiting and partial capture are recorded without credentials or retry storms.

## Acceptance Criteria


## Design


## Notes
CONFIGURATION GATE (blocking):
- If the configured Scarlett source requires authentication, the owner provisions the credential only in the local process environment before capture; absence fails before any request and the value never enters arguments, payloads, events, reports, exports, or hashes.
- If no authentication is required, the immutable collector policy must explicitly declare that fact, the approved endpoint, rate limit, and minimum capture budget before collection proceeds.

## History
- 2026-09-18T23:31:18Z dep_added: blocked_by VK-pg9j
- 2026-09-18T23:31:19Z dep_added: blocks VK-jvku
- 2026-09-18T23:31:28Z dep_added: blocks VK-l747
- 2026-09-18T23:31:39Z dep_added: blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-jvku]], [[VK-l747]], [[VK-ldg1]]
- Blocked by: [[VK-pg9j]]

## Comments
