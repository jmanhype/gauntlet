---
id: VK-1vhm
title: "Establish canonical artifact contracts"
status: in_progress
priority: 0
type: feature
labels: [integration, phase-1, walking-skeleton]
parent: VK-egll
created_at: 2026-09-18T23:31:15Z
created_by: speed
updated_at: 2026-09-19T02:09:40Z
content_hash: "sha256:c4ee23891e51fca2e8a7a10d9b278e2cb79e944d4b32eb9809d00bb3f80f229b"
blocks: [VK-wa2q, VK-kmbs, VK-jkkn, VK-bns7, VK-52g6, VK-3f9f, VK-aej2]
assignee: dev-VK-1vhm
---

## Description
## USER INTENT
The owner needs every artifact, manifest, and policy hash to have one deterministic representation before any research evidence is created.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Create the shared contract layer for canonical JSON, SHA-256 content addressing, schema validation, and immutable manifest verification. `payload_hash` hashes canonical payload JSON. An envelope hash omits only its own hash field and includes the prior head. Manifests must record every embedded or external file hash and storage-relative path. Exclusive creation must refuse overwrite of a non-empty destination.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Collector-specific pagination and budget behavior: lands in collector stories.
- Trial/event append semantics: lands in the append-only ledger story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~7 files, under 500 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/contracts/canonical.py -> canonical_json(value: object) -> bytes
- src/gauntlet/contracts/canonical.py -> sha256_digest(data: bytes) -> str
- src/gauntlet/contracts/schemas.py -> validate(instance: object, schema_id: str) -> ValidationResult
- src/gauntlet/contracts/manifests.py -> verify_manifest(manifest_path: Path, data_root: Path) -> ManifestVerification
- tests/integrity/test_contracts.py -> contract and tamper cases

CONSUMES:
- (none -- leaf story; this story creates its declared contract)

### Acceptance Criteria (story contract)
1. Canonical JSON serializes equivalent objects to identical bytes and rejects NaN and non-string object keys.
2. SHA-256 digests are emitted as `sha256:<64 lowercase hexadecimal characters>` and verify against exact bytes.
3. Schema validation accepts the Phase 1 descriptor, trial, event, policy, and manifest envelopes and rejects unknown required discriminator values.
4. Manifest verification checks every file hash, external content hash, storage-relative path, and Merkle root.
5. Exclusive creation refuses to replace a non-empty output directory or existing immutable file.
6. A tampered manifest, missing artifact, or hash mismatch returns a machine-readable integrity error and writes no artifact.
7. All public functions have typed signatures and deterministic outputs.

## Testing Requirements
- Unit: Test canonical ordering, digest formatting, schema acceptance/rejection, manifest roots, and exclusive-create behavior.
- Integration tests: MANDATORY (no mocks). Build a temporary content-addressed artifact tree from real files, verify it, mutate one byte on a copy, and prove verification fails without changing the original.
- Commands to run: `uv run pytest tests/integrity/test_contracts.py`.

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
- [ ] AC #1: Canonical JSON serializes equivalent objects to identical bytes and rejects NaN and non-string object keys.
- [ ] AC #2: SHA-256 digests are emitted as `sha256:<64 lowercase hexadecimal characters>` and verify against exact bytes.
- [ ] AC #3: Schema validation accepts the Phase 1 descriptor, trial, event, policy, and manifest envelopes and rejects unknown required discriminator values.
- [ ] AC #4: Manifest verification checks every file hash, external content hash, storage-relative path, and Merkle root.
- [ ] AC #5: Exclusive creation refuses to replace a non-empty output directory or existing immutable file.
- [ ] AC #6: A tampered manifest, missing artifact, or hash mismatch returns a machine-readable integrity error and writes no artifact.
- [ ] AC #7: All public functions have typed signatures and deterministic outputs.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:15Z dep_added: blocks VK-wa2q
- 2026-09-18T23:31:16Z dep_added: blocks VK-kmbs
- 2026-09-18T23:31:16Z dep_added: blocks VK-jkkn
- 2026-09-18T23:31:31Z dep_added: blocks VK-bns7
- 2026-09-18T23:31:32Z dep_added: blocks VK-52g6
- 2026-09-18T23:31:38Z dep_added: blocks VK-3f9f
- 2026-09-19T01:37:42Z dep_added: blocks VK-aej2
- 2026-09-19T02:09:40Z status: open -> in_progress
- 2026-09-19T02:09:40Z claimed by dev-VK-1vhm

## Links
- Parent: [[VK-egll]]
- Blocks: [[VK-wa2q]], [[VK-kmbs]], [[VK-jkkn]], [[VK-bns7]], [[VK-52g6]], [[VK-3f9f]], [[VK-aej2]]

## Comments

### 2026-09-18T23:33:03Z speed
RECOMMEND hard-tdd: canonical hashing and immutable manifests are security-critical foundations where subtle bugs poison every artifact. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: canonical hashing and immutable manifests are security-critical foundations where subtle bugs poison every artifact. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
