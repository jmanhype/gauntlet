---
id: VK-bns7
title: "Persist immutable Decision Snapshots"
status: open
priority: 0
type: feature
labels: [integration, phase-1]
parent: VK-1rbc
created_at: 2026-09-18T23:31:31Z
created_by: speed
updated_at: 2026-09-18T23:33:49Z
content_hash: "sha256:ec3115d415af1989a41d8a1850b0fe781e7628699121b349aa13eb6b339e7a85"
blocked_by: [VK-2e0k, VK-wa2q]
blocks: [VK-52g6, VK-1ptl, VK-21gm, VK-6khc, VK-dblr, VK-uyca, VK-3v14]
was_blocked_by: [VK-1vhm]
---

## Description
## USER INTENT
The owner needs the exact evidence and reveal sequence at decision time preserved separately from later projections or opinions.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement content-addressed write-once `data/decisions/<decision_id>/snapshot.json`, `manifest.json`, `evidence/`, `policy/`, and optional `projections/`. Snapshot facts include evidence set/version, inspectable gate calculation, gate state, policy disposition/version, optional advisory recommendation and visibility, owner decision slot, review mode, ordered reveal log, artifact versions, prior-snapshot delta, dependency health, recommendation model/agent version, and hashes. Manifest hashes embedded files and external artifact hashes/paths. Reconstruction starts from the manifest and blocks on missing source bytes, configuration, checkpoint, code version, or dependency definition. Owner actions extend but never rewrite the snapshot.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Owner authorization verification: sibling Ed25519 story.
- Scoreboard/Evidence Card rendering: surfaces epic.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 700 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/decisions/writer.py -> write_decision_snapshot(request: SnapshotRequest) -> DecisionSnapshot
- src/gauntlet/decisions/reconstructor.py -> reconstruct_snapshot(snapshot_hash: str, data_root: Path) -> SnapshotReconstruction

CONSUMES:
- VK-2e0k: src/gauntlet/policy/engine.py -> evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
  spec: evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
- VK-1vhm: src/gauntlet/contracts/manifests.py -> verify_manifest(manifest_path: Path, data_root: Path) -> ManifestVerification
  spec: verify_manifest(manifest_path: Path, data_root: Path) -> ManifestVerification
- VK-wa2q: src/gauntlet/ledger/events.py -> append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
  spec: append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult

### Acceptance Criteria (story contract)
1. Snapshot stores evidence, gate arithmetic, gate state, policy disposition, recommendation, owner slot, review mode, ordered reveal log, versions, delta, dependency health, and hashes as separate facts.
2. Manifest hashes every embedded file and records every external artifact content hash and storage-relative path.
3. Snapshot creation fails on invalid gate result, actor context, reveal log, event chain, or existing snapshot ID.
4. Reconstruction verifies all referenced bytes and preserves the exact recorded policy and artifact versions.
5. Deleting one required source artifact makes reconstruction BLOCKED and blocks promotion/export approval.
6. Recommendation recomputation never mutates the historical recommendation or snapshot.
7. Later projections can be deleted and regenerated without losing decision state.

## Testing Requirements
- Unit: Test snapshot schema, manifest Merkle root, write-once behavior, reveal ordering, and reconstruction.
- Integration tests: MANDATORY (no mocks). Write a real gate result with evidence and policy artifacts, reconstruct it, delete one referenced artifact on a copy, and prove verification blocks without mutating the original.
- Commands to run: `uv run pytest tests/decisions/test_snapshot.py`.

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
- [ ] AC #1: Snapshot stores evidence, gate arithmetic, gate state, policy disposition, recommendation, owner slot, review mode, ordered reveal log, versions, delta, dependency health, and hashes as separate facts.
- [ ] AC #2: Manifest hashes every embedded file and records every external artifact content hash and storage-relative path.
- [ ] AC #3: Snapshot creation fails on invalid gate result, actor context, reveal log, event chain, or existing snapshot ID.
- [ ] AC #4: Reconstruction verifies all referenced bytes and preserves the exact recorded policy and artifact versions.
- [ ] AC #5: Deleting one required source artifact makes reconstruction BLOCKED and blocks promotion/export approval.
- [ ] AC #6: Recommendation recomputation never mutates the historical recommendation or snapshot.
- [ ] AC #7: Later projections can be deleted and regenerated without losing decision state.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:31Z dep_added: blocked_by VK-2e0k
- 2026-09-18T23:31:31Z dep_added: blocked_by VK-1vhm
- 2026-09-18T23:31:32Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:32Z dep_added: blocks VK-52g6
- 2026-09-18T23:31:33Z dep_added: blocks VK-1ptl
- 2026-09-18T23:31:34Z dep_added: blocks VK-21gm
- 2026-09-18T23:31:35Z dep_added: blocks VK-6khc
- 2026-09-18T23:31:37Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:45Z dep_added: blocks VK-uyca
- 2026-09-19T01:37:42Z dep_added: blocks VK-3v14
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm

## Links
- Parent: [[VK-1rbc]]
- Blocks: [[VK-52g6]], [[VK-1ptl]], [[VK-21gm]], [[VK-6khc]], [[VK-dblr]], [[VK-uyca]], [[VK-3v14]]
- Blocked by: [[VK-2e0k]], [[VK-wa2q]]
- Was blocked by: [[VK-1vhm]]

## Comments

### 2026-09-18T23:33:04Z speed
RECOMMEND hard-tdd: write-once snapshots and reconstruction are integrity-critical. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: write-once snapshots and reconstruction are integrity-critical. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
