---
id: VK-jkkn
title: "Resolve immutable run configurations"
status: open
priority: 0
type: feature
labels: [integration, phase-1, rejected]
parent: VK-egll
created_at: 2026-09-18T23:31:16Z
created_by: speed
updated_at: 2026-09-19T04:35:18Z
content_hash: "sha256:c7064baf68c175239158639cc552fb98b56370cac62f66f6526c44bc14b15003"
blocks: [VK-pg9j, VK-mfn6, VK-si5s, VK-0pfo, VK-0c4c, VK-ddoh, VK-dblr, VK-3f9f, VK-rkdr]
was_blocked_by: [VK-1vhm, VK-kmbs]
follows: [VK-1vhm, VK-kmbs, VK-wa2q]
---

## Description
## USER INTENT
The owner needs a complete visible configuration for every run so no hidden default or threshold can alter research interpretation.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement immutable versioned profiles and a shared resolver. Every run resolves defaults, profile, explicit CLI/MCP overrides, environment-independent research values, artifact versions, and hashes into one canonical configuration. `--show-config` prints it; `--diff-config` compares it to a profile or prior run. Runtime paths and secret names may be redacted only under a versioned rule that never changes a research threshold. Research- or state-mutating services reject incomplete or hidden values.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- CLI/MCP command surfaces and parity: lands in the shared-interface story.
- Collector credential injection: lands in collector stories.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 450 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- src/gauntlet/config/diff.py -> diff_config(left: ResolvedConfig, right: ResolvedConfig) -> ConfigDiff

CONSUMES:
- VK-1vhm: src/gauntlet/contracts/canonical.py -> canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str
  spec: canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str
- VK-kmbs: src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
  spec: register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration

### Acceptance Criteria (story contract)
1. A profile plus explicit overrides resolves to a canonical artifact with a stable SHA-256 configuration hash.
2. Every default, override, policy/model/code version, and artifact version appears in the resolved output.
3. Secret values are never accepted or emitted; only a versioned redaction rule may name a secret-bearing field without exposing its value.
4. A hidden or incomplete research-critical value returns `CONFIG_INVALID` before mutation.
5. Config diff identifies added, removed, changed, redacted, and threshold-bearing values without losing provenance.
6. A configuration referenced by a trial or snapshot is immutable and later profile edits do not change its hash.

## Testing Requirements
- Unit: Test precedence, canonical hashing, redaction, immutability, invalid values, and diff completeness.
- Integration tests: MANDATORY (no mocks). Resolve a real TOML profile with overrides, register it through the contract layer, mutate the source profile, and prove the prior resolved hash and bytes remain unchanged.
- Commands to run: `uv run pytest tests/integrity/test_resolved_config.py`.

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
- [ ] AC #1: A profile plus explicit overrides resolves to a canonical artifact with a stable SHA-256 configuration hash.
- [ ] AC #2: Every default, override, policy/model/code version, and artifact version appears in the resolved output.
- [ ] AC #3: Secret values are never accepted or emitted; only a versioned redaction rule may name a secret-bearing field without exposing its value.
- [ ] AC #4: A hidden or incomplete research-critical value returns `CONFIG_INVALID` before mutation.
- [ ] AC #5: Config diff identifies added, removed, changed, redacted, and threshold-bearing values without losing provenance.
- [ ] AC #6: A configuration referenced by a trial or snapshot is immutable and later profile edits do not change its hash.

## Acceptance Criteria


## Design


## Notes
## nd_contract
status: delivered

### evidence
- Branch `story/VK-jkkn`; commit `93d54b15d532aac56b476720024d0851e2e75b7b`.
- `uv run pytest tests/integrity/test_resolved_config.py`: 5 passed.
- `uv run pytest tests/`: 26 passed.
- `uv run --with pytest-cov pytest tests/integrity/test_resolved_config.py --cov=gauntlet.config --cov-report=term-missing`: 5 passed, 93% coverage.
- `pvg verify src/gauntlet/config/__init__.py src/gauntlet/config/resolver.py src/gauntlet/config/diff.py tests/integrity/test_resolved_config.py --format=text`: PASSED.
- Delivery label applied by `pvg story deliver VK-jkkn`.

### proof
- [x] AC #1: Stable canonical SHA-256 resolution proven by deterministic real-profile test.
- [x] AC #2: Complete defaults, overrides, versions, provenance, and artifact versions asserted in canonical output.
- [x] AC #3: Secret rejection and versioned redaction proven without emitting secret/path input values.
- [x] AC #4: Invalid/hidden/incomplete configurations return `CONFIG_INVALID` without creating the data root.
- [x] AC #5: Diff categories, provenance, hashes, threshold classification, and version drift proven.
- [x] AC #6: Contract-registered bytes and hash remain unchanged after source profile mutation.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `uv run pytest tests/integrity/test_resolved_config.py`
  - `uv run pytest tests/`
  - `uv run --with pytest-cov pytest tests/integrity/test_resolved_config.py --cov=gauntlet.config --cov-report=term-missing`
  - `pvg verify src/gauntlet/config/__init__.py src/gauntlet/config/resolver.py src/gauntlet/config/diff.py tests/integrity/test_resolved_config.py --format=text`
- Summary: targeted PASS 5/5; full suite PASS 26/26; `gauntlet.config` coverage 93% (214 statements, 14 missed); pvg verify PASS.
- Key output:
  - Targeted: `collected 5 items` → `5 passed in 0.05s`
  - Full: `collected 26 items` → `26 passed in 0.38s`
  - Coverage: `TOTAL 214 14 93%`
  - Verify: `VERIFY: PASSED (4 files scanned, 0 issues)`

### Commit
- Branch: `story/VK-jkkn`
- SHA: `93d54b15d532aac56b476720024d0851e2e75b7b`
- Commit: `feat(VK-jkkn): resolve immutable run configurations`
- Changed files: 4 files, 449 inserted lines (within the under-450 changed-LOC budget).

### pvg verify
- `VERIFY: PASSED (4 files scanned, 0 issues)`

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|------|-------------|---------------|---------------|--------|
| 1 | Profile plus explicit overrides resolves to a canonical artifact with stable SHA-256 hash. | `src/gauntlet/config/resolver.py::resolve_config` | `tests/integrity/test_resolved_config.py::test_real_profile_overrides_and_complete_canonical_hash` | PASS |
| 2 | Defaults, overrides, provenance, policy/model/code versions, and all artifact versions are visible in the result. | `src/gauntlet/config/resolver.py::resolve_config` | `test_real_profile_overrides_and_complete_canonical_hash` | PASS |
| 3 | Secret material is rejected; runtime path and secret-name fields use only the versioned redaction rule and never emit input values. | `resolver.py::_reject_secrets`, `_redacted`, `resolve_config` | `test_versioned_redaction_and_secret_refusal_are_fail_closed` | PASS |
| 4 | Unknown, hidden, incomplete, malformed, or invalid version inputs return machine-readable `CONFIG_INVALID` before mutation. | `resolver.py::ConfigError`, `_invalid`, validators, `resolve_config` | `test_versioned_redaction_and_secret_refusal_are_fail_closed`; `test_missing_incomplete_and_malformed_inputs_reject_before_mutation` | PASS |
| 5 | Diff reports added, removed, changed, redacted, and threshold-bearing leaves while retaining left/right provenance and hashes. | `src/gauntlet/config/diff.py::diff_config` | `test_diff_preserves_provenance_and_classifies_material_changes` | PASS |
| 6 | A resolved configuration registered through the contract layer remains byte/hash immutable after later profile edits. | `resolver.py::ResolvedConfig`; real integration registration in test | `test_contract_registration_freezes_bytes_against_later_profile_edits` | PASS |

LEARNINGS:
- Real TOML plus a real immutable descriptor registration gives a compact end-to-end proof that source-profile mutation cannot rewrite a sealed config.
- Separating the canonical artifact from its terminal hash avoids self-referential hashing while still allowing consumers to recompute the digest from exact bytes.
- Diffing effective values plus explicit override/version provenance catches both value drift and provenance drift without duplicating every profile/default field.

### OBSERVATIONS (unrelated)
- [ISSUE] Paivot vault search: `pvg notes search` from the worktree and project root failed because it selected unavailable vault `Claude`; `pvg nd` correctly used the shared `nd-vault`. Story execution was unaffected.

### DISCOVERED_BUG
  title: pvg notes search selects an unavailable configured vault
  context: Running `pvg notes search "VK-jkkn resolved configuration"` and `pvg notes search "resolved configuration"` returned `vlt: vault "Claude" not found. Available: vault, .vault, nd-vault, ...`. Live nd operations worked through `/Users/speed/Downloads/AI_Videos/google-usercontent/gauntlet/.git/paivot/nd-vault`.
  affected_files: Paivot/vlt vault-selection configuration outside this repository story scope
  discovered_during: VK-jkkn

## nd_contract
status: delivered

### evidence
- Commit `93d54b15d532aac56b476720024d0851e2e75b7b` on `story/VK-jkkn`.
- `uv run pytest tests/integrity/test_resolved_config.py`: 5 passed.
- `uv run pytest tests/`: 26 passed.
- `uv run --with pytest-cov pytest tests/integrity/test_resolved_config.py --cov=gauntlet.config --cov-report=term-missing`: 5 passed, 93% coverage.
- `pvg verify <4 changed files> --format=text`: PASSED, 0 issues.

### proof
- [x] AC #1: Stable canonical SHA-256 resolution proven by deterministic real-profile test.
- [x] AC #2: Complete defaults, overrides, versions, provenance, and artifact versions asserted in canonical output.
- [x] AC #3: Secret rejection and versioned redaction proven without emitting secret/path input values.
- [x] AC #4: Invalid/hidden/incomplete configurations return `CONFIG_INVALID` without creating the data root.
- [x] AC #5: Diff categories, provenance, hashes, threshold classification, and version drift proven.
- [x] AC #6: Contract-registered bytes and hash remain unchanged after source profile mutation.

## nd_contract
status: in_progress

### evidence
- Claimed: 2026-09-19
- Worktree: /Users/speed/Downloads/AI_Videos/google-usercontent/gauntlet/.claude/worktrees/dev-VK-jkkn
- Branch: story/VK-jkkn

### proof
- [ ] (pending)

## History
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-1vhm
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:17Z dep_added: blocks VK-pg9j
- 2026-09-18T23:31:19Z dep_added: blocks VK-mfn6
- 2026-09-18T23:31:20Z dep_added: blocks VK-si5s
- 2026-09-18T23:31:21Z dep_added: blocks VK-0pfo
- 2026-09-18T23:31:23Z dep_added: blocks VK-0c4c
- 2026-09-18T23:31:24Z dep_added: blocks VK-ddoh
- 2026-09-18T23:31:36Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:38Z dep_added: blocks VK-3f9f
- 2026-09-19T01:37:42Z dep_added: blocks VK-rkdr
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs
- 2026-09-19T04:15:20Z status: open -> in_progress
- 2026-09-19T04:15:20Z auto-follows: linked to predecessor VK-1vhm
- 2026-09-19T04:15:20Z auto-follows: linked to predecessor VK-kmbs
- 2026-09-19T04:15:20Z claimed by dev-VK-jkkn
- 2026-09-19T04:30:38Z status: in_progress -> in_progress
- 2026-09-19T04:30:38Z auto-follows: linked to predecessor VK-wa2q
- 2026-09-19T04:35:17Z status: in_progress -> open
- 2026-09-19T04:35:17Z released by speed

## Links
- Parent: [[VK-egll]]
- Blocks: [[VK-pg9j]], [[VK-mfn6]], [[VK-si5s]], [[VK-0pfo]], [[VK-0c4c]], [[VK-ddoh]], [[VK-dblr]], [[VK-3f9f]], [[VK-rkdr]]
- Was blocked by: [[VK-1vhm]], [[VK-kmbs]]
- Follows: [[VK-1vhm]], [[VK-kmbs]], [[VK-wa2q]]

## Comments
