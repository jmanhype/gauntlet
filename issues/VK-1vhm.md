---
id: VK-1vhm
title: "Establish canonical artifact contracts"
status: in_progress
priority: 0
type: feature
labels: [integration, phase-1, walking-skeleton, delivered]
parent: VK-egll
created_at: 2026-09-18T23:31:15Z
created_by: speed
updated_at: 2026-09-19T02:33:04Z
content_hash: "sha256:03998e098af70b2ff3ad11cdd551e0651353cc76cfd992a0934a7606509b081b"
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
## nd_contract
status: delivered

### evidence
- Authoritative delivery follows `pvg story deliver VK-1vhm`; commit `26f70aeffa5013c86bfb5b5400853904107351ae`.
- `uv run pytest tests/integrity/test_contracts.py`: 6 passed. Coverage command: 81%. `pvg verify`: PASS for source and test files.

### proof
- [x] AC #1 through AC #7 verified in the AC Verification table above; all checkboxes are backed by the recorded commands and commit.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

PROOF:

### CI/Test Results
- Commands run:
  - `uv run pytest tests/integrity/test_contracts.py`
  - `uv run --with pytest-cov pytest tests/integrity/test_contracts.py --cov=gauntlet.contracts --cov-report=term-missing`
  - `uv run --no-sync python -m compileall -q src tests`
  - `git diff --check`
  - `pvg verify pyproject.toml src/gauntlet/__init__.py src/gauntlet/contracts/__init__.py src/gauntlet/contracts/canonical.py src/gauntlet/contracts/schemas.py src/gauntlet/contracts/manifests.py --format=text`
  - `pvg verify tests/integrity/test_contracts.py --format=text`
- Summary: contract/integration suite PASS (6/6); compile PASS; diff check PASS; pvg verify PASS.
- Coverage: 81% (`pytest-cov` total: 232 statements, 44 missed).
- Key output:
  - `collected 6 items`
  - `tests/integrity/test_contracts.py ...... [100%]`
  - `6 passed in 0.03s`
  - `TOTAL ... 81%`
  - `VERIFY: PASSED (5 files scanned, 0 issues)`
  - `VERIFY: PASSED (1 files scanned, 0 issues)`
- Integration proof: the no-mock test builds a real temporary embedded/external artifact tree, verifies its Merkle root, copies the tree, flips one payload byte, observes `ARTIFACT_HASH_MISMATCH`, and re-verifies the original plus compares its original bytes.

### Commit
- Branch: `story/VK-1vhm`
- SHA: `26f70aeffa5013c86bfb5b5400853904107351ae`
- Diff budget: 7 files, 499 inserted lines.

### pvg verify
- `VERIFY: PASSED (5 files scanned, 0 issues)`
- `VERIFY: PASSED (1 files scanned, 0 issues)`

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|------|-------------|---------------|---------------|--------|
| 1 | Deterministic canonical JSON; NaN and non-string-key rejection | `src/gauntlet/contracts/canonical.py` | `tests/integrity/test_contracts.py::test_canonical_json_is_deterministic_and_fail_closed` | PASS |
| 2 | `sha256:<64 lowercase hex>` exact-byte digests | `src/gauntlet/contracts/canonical.py` | `tests/integrity/test_contracts.py::test_digest_is_lowercase_and_exact_byte_bound` | PASS |
| 3 | Descriptor/trial/event/policy/manifest validation with unknown-discriminator rejection | `src/gauntlet/contracts/schemas.py` | `tests/integrity/test_contracts.py::test_registered_envelopes_and_discriminators` | PASS |
| 4 | File/external hashes, storage-relative paths, and Merkle root verification | `src/gauntlet/contracts/manifests.py` | `tests/integrity/test_contracts.py::test_real_manifest_success_tamper_and_original_stability` and `::test_manifest_integrity_failures_are_read_only_and_machine_readable` | PASS |
| 5 | Exclusive creation refuses non-empty directories and existing immutable files | `src/gauntlet/contracts/manifests.py::create_exclusive` | `tests/integrity/test_contracts.py::test_exclusive_create_refuses_nonempty_directory_and_existing_file` | PASS |
| 6 | Machine-readable integrity failures with no artifact writes | `src/gauntlet/contracts/manifests.py::ManifestVerification` / `IntegrityFailure` | manifest failure/tamper tests in `tests/integrity/test_contracts.py` | PASS |
| 7 | Typed public functions and deterministic outputs | typed signatures in `canonical.py`, `schemas.py`, and `manifests.py` | deterministic/equivalence assertions across all six tests | PASS |

LEARNINGS:
- Expose error codes as attributes and assert the attribute directly; matching `pytest.raises(..., match=...)` against `str(exception)` does not inspect custom code fields.
- Path-traversal manifests are fail-closed at schema validation, producing `SCHEMA_INVALID` with the precise `$.files[N].path` error path before filesystem resolution.
- `uv sync` creates transient `uv.lock` and editable-install metadata; they were deliberately not committed because this story's boundary specified the pyproject scaffold and a 7-file/500-line budget.

### OBSERVATIONS (unrelated)
- [CONCERN] global tooling: `pvg notes search "gauntlet canonical manifest integrity"` reports `vlt: vault "Claude" not found` from both worktree and project root. No project code depends on that optional knowledge lookup.

## nd_contract
status: delivered

### evidence
- Commands and outputs recorded above; all 6 tests passed at commit `26f70aeffa5013c86bfb5b5400853904107351ae`; coverage 81%; pvg verify passed.
- Commit: `26f70aeffa5013c86bfb5b5400853904107351ae` on `story/VK-1vhm` (7 files, 499 insertions).

### proof
- [x] AC #1: Canonical JSON serializes equivalent objects to identical bytes and rejects NaN and non-string object keys.
- [x] AC #2: SHA-256 digests are emitted as `sha256:<64 lowercase hexadecimal characters>` and verify against exact bytes.
- [x] AC #3: Schema validation accepts the Phase 1 descriptor, trial, event, policy, and manifest envelopes and rejects unknown required discriminator values.
- [x] AC #4: Manifest verification checks every file hash, external content hash, storage-relative path, and Merkle root.
- [x] AC #5: Exclusive creation refuses to replace a non-empty output directory or existing immutable file.
- [x] AC #6: A tampered manifest, missing artifact, or hash mismatch returns a machine-readable integrity error and writes no artifact.
- [x] AC #7: All public functions have typed signatures and deterministic outputs.


## nd_contract
status: in_progress

### evidence
- Claimed 2026-09-19 in story worktree story/VK-1vhm.

### proof
- [ ] Pending implementation and verification.

## Implementation Evidence

### CI/Test Results
Commands run:
- `uv run pytest tests/integrity/test_contracts.py`
- `uv run --with pytest-cov pytest tests/integrity/test_contracts.py --cov=gauntlet.contracts --cov-report=term-missing`
- `pvg verify ... --format=text`

Summary: PASS — 6 passed; integration no-mock real-tree tamper test PASS; coverage 81%; pvg verify PASS.
Commit SHA: `26f70aeffa5013c86bfb5b5400853904107351ae` on `story/VK-1vhm`.

## nd_contract
status: delivered

### evidence
- Delivery repair: appended the authoritative delivered contract after prior note blocks so the last nd_contract is delivered.
- Commit `26f70aeffa5013c86bfb5b5400853904107351ae`; `uv run pytest tests/integrity/test_contracts.py` -> 6 passed; coverage 81%; pvg verify PASS.

### proof
- [x] AC #1 through AC #7: verified by the Implementation Evidence table and recorded test output.

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
- 2026-09-19T02:30:15Z status: in_progress -> in_progress

## Links
- Parent: [[VK-egll]]
- Blocks: [[VK-wa2q]], [[VK-kmbs]], [[VK-jkkn]], [[VK-bns7]], [[VK-52g6]], [[VK-3f9f]], [[VK-aej2]]

## Comments

### 2026-09-18T23:33:03Z speed
RECOMMEND hard-tdd: canonical hashing and immutable manifests are security-critical foundations where subtle bugs poison every artifact. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: canonical hashing and immutable manifests are security-critical foundations where subtle bugs poison every artifact. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
