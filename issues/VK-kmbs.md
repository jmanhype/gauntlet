---
id: VK-kmbs
title: "Register evidence descriptors with fail-closed dependencies"
status: in_progress
priority: 0
type: feature
labels: [integration, phase-1]
parent: VK-egll
created_at: 2026-09-18T23:31:15Z
created_by: speed
updated_at: 2026-09-19T03:19:17Z
content_hash: "sha256:3d7fa19d538205f264a85e192b77e2b9e12155c3e0f2ec37cf7ca9876224b424"
blocks: [VK-jkkn, VK-pg9j, VK-mfn6, VK-0pfo, VK-0c4c, VK-2e0k, VK-3f9f, VK-4qfy, VK-3v14]
was_blocked_by: [VK-1vhm, VK-wa2q]
assignee: dev-VK-kmbs
follows: [VK-1vhm, VK-wa2q]
---

## Description
## USER INTENT
The owner needs every gate input classified and time-bound so stale, corrupt, or unknown evidence blocks promotion rather than masquerading as a valid result.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement immutable `gauntlet.evidence.v1` descriptors. Required fields are exactly `descriptor_schema`, `artifact_id`, `descriptor_id`, `descriptor_version`, `descriptor_hash`, `supersedes_descriptor_hash`, `effective_at_utc`, `superseded_at_utc`, `kind`, `venue_track`, `content_hash`, `source`, `observation_basis`, `coverage`, `freshness`, `quality`, `dependencies`, `criticality`, and `downstream_metrics`. Build a directed dependency graph and evaluate hash/schema validity, provenance reachability, freshness at `as_of`, quality, recursive dependency health, OBSERVED/MODELED eligibility, and policy criticality. Corrections and quarantine append superseding descriptor versions; original bytes never change. UNKNOWN criticality is gate-critical.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Collector-specific quarantine creation: lands in collector health work.
- Deterministic gate precedence after dependency evaluation: lands in the decision epic.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 750 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
- src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
- src/gauntlet/data/quarantine.py -> quarantine_descriptor(original_hash: str, reason: QuarantineReason, actor: Actor) -> DescriptorRegistration
- tests/integrity/test_dependency_graph.py -> closure, time travel, quarantine, and fail-closed cases

CONSUMES:
- VK-1vhm: src/gauntlet/contracts/schemas.py -> validate(instance: object, schema_id: str) -> ValidationResult
  spec: validate(instance: object, schema_id: str) -> ValidationResult
- VK-wa2q: src/gauntlet/ledger/trials.py -> append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult
  spec: append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult

### Acceptance Criteria (story contract)
1. Descriptor registration validates the complete schema, canonical hash, content hash, and dependency references before ledgering.
2. Dependency closure evaluates the seven architecture checks in order and returns a graph hash plus affected metrics and coverage.
3. Gate-critical missing, stale, corrupt, incomplete, replay-failed, or UNKNOWN inputs mark dependent metrics INVALID and the result BLOCKED.
4. Explicitly noncritical gaps leave unaffected metrics valid while visibly reducing coverage.
5. Descriptor selection honors `effective_at_utc <= as_of` and `superseded_at_utc > as_of`, while a run manifest bound to an exact hash keeps that hash.
6. Quarantine creates a superseding immutable version referencing the exact original descriptor hash; original bytes and historical resolution remain unchanged.
7. A MODELED value cannot satisfy a rule requiring OBSERVED outcomes, reserve state, realized fills, external claims, or untouched prospective evidence.
8. Malformed or cyclic dependency data returns `GRAPH_MALFORMED` rather than crashing or partially selecting descriptors.

## Testing Requirements
- Unit: Test schema rejection, time-bound selection, recursive health, criticality, observation basis, graph hashes, and malformed graphs.
- Integration tests: MANDATORY (no mocks). Register a real multi-level artifact graph in temporary storage, evaluate at multiple timestamps, quarantine one leaf, and prove both historical and later behavior without file mutation.
- Commands to run: `uv run pytest tests/integrity/test_dependency_graph.py`.

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
- Epic containment: VK-egll.

### proof
- [ ] AC #1: Descriptor registration validates the complete schema, canonical hash, content hash, and dependency references before ledgering.
- [ ] AC #2: Dependency closure evaluates the seven architecture checks in order and returns a graph hash plus affected metrics and coverage.
- [ ] AC #3: Gate-critical missing, stale, corrupt, incomplete, replay-failed, or UNKNOWN inputs mark dependent metrics INVALID and the result BLOCKED.
- [ ] AC #4: Explicitly noncritical gaps leave unaffected metrics valid while visibly reducing coverage.
- [ ] AC #5: Descriptor selection honors `effective_at_utc <= as_of` and `superseded_at_utc > as_of`, while a run manifest bound to an exact hash keeps that hash.
- [ ] AC #6: Quarantine creates a superseding immutable version referencing the exact original descriptor hash; original bytes and historical resolution remain unchanged.
- [ ] AC #7: A MODELED value cannot satisfy a rule requiring OBSERVED outcomes, reserve state, realized fills, external claims, or untouched prospective evidence.
- [ ] AC #8: Malformed or cyclic dependency data returns `GRAPH_MALFORMED` rather than crashing or partially selecting descriptors.

## Acceptance Criteria


## Design


## Notes
NORMATIVE DESCRIPTOR ENUMERATIONS (authoritative for implementation):
- criticality: GATE_CRITICAL | NON_CRITICAL | UNKNOWN; UNKNOWN is fail-closed and equivalent to GATE_CRITICAL until a policy version classifies it.
- quality.state: VALID | STALE | CORRUPT | INCOMPLETE | QUARANTINED.
- observation_basis: OBSERVED | MODELED.
- venue_track: solana_dex | hyperliquid | cross_venue_transfer | external.
## nd_contract
status: in_progress

### evidence
- Claimed: 2026-09-18
- Worktree: story/VK-kmbs at 66555f6061d9aa371b9a4ba45d946498e83e37a0

### proof
- [ ] (pending)

## History
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-1vhm
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:16Z dep_added: blocks VK-jkkn
- 2026-09-18T23:31:17Z dep_added: blocks VK-pg9j
- 2026-09-18T23:31:19Z dep_added: blocks VK-mfn6
- 2026-09-18T23:31:22Z dep_added: blocks VK-0pfo
- 2026-09-18T23:31:23Z dep_added: blocks VK-0c4c
- 2026-09-18T23:31:29Z dep_added: blocks VK-2e0k
- 2026-09-18T23:31:38Z dep_added: blocks VK-3f9f
- 2026-09-19T01:37:42Z dep_added: blocks VK-4qfy
- 2026-09-19T01:37:42Z dep_added: blocks VK-3v14
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q
- 2026-09-19T03:19:17Z status: open -> in_progress
- 2026-09-19T03:19:17Z auto-follows: linked to predecessor VK-1vhm
- 2026-09-19T03:19:17Z auto-follows: linked to predecessor VK-wa2q
- 2026-09-19T03:19:17Z claimed by dev-VK-kmbs

## Links
- Parent: [[VK-egll]]
- Blocks: [[VK-jkkn]], [[VK-pg9j]], [[VK-mfn6]], [[VK-0pfo]], [[VK-0c4c]], [[VK-2e0k]], [[VK-3f9f]], [[VK-4qfy]], [[VK-3v14]]
- Was blocked by: [[VK-1vhm]], [[VK-wa2q]]
- Follows: [[VK-1vhm]], [[VK-wa2q]]

## Comments

### 2026-09-18T23:33:03Z speed
RECOMMEND hard-tdd: time-bound descriptor selection and recursive fail-closed behavior are state-machine/security-critical. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: time-bound descriptor selection and recursive fail-closed behavior are state-machine/security-critical. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
