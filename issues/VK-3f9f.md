---
id: VK-3f9f
title: "E2e: verify governance integrity end to end"
status: open
priority: 0
type: feature
labels: [phase-1, capstone, e2e]
parent: VK-egll
created_at: 2026-09-18T23:31:37Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:e4451e11ca3425aa70086dd34f69d91c7da4ea1425be3e57c7c238e5f3562688"
blocked_by: [VK-kmbs, VK-jkkn, VK-3v14]
blocks: [VK-hiuk]
was_blocked_by: [VK-1vhm, VK-wa2q]
---

## Description
## USER INTENT
The owner can register a synthetic trial, verify its immutable chains and descriptors, and see any tampered copy rejected before interpretation.

Observable outcome: the owner can run the declared E2e command, inspect or display its output, and verify that the full path returns the declared result, stores its immutable artifacts, and emits the corresponding hash-verified events.

## Context (Embedded)
This is the E2e capstone for epic VK-egll. It must exercise the completed epic from the owner perspective after every sibling story. It verifies real local files, chains, subprocesses, outputs, and exit codes. It does not establish new module semantics.

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
- tests/e2e/test_governance_integrity.py -> owner-perspective governance drill

CONSUMES:
- VK-1vhm: src/gauntlet/contracts/manifests.py -> verify_manifest(manifest_path: Path, data_root: Path) -> ManifestVerification
  spec: verify_manifest(manifest_path: Path, data_root: Path) -> ManifestVerification
- VK-wa2q: src/gauntlet/ledger/verify.py -> verify_chains(data_root: Path) -> ChainVerification
  spec: verify_chains(data_root: Path) -> ChainVerification
- VK-kmbs: src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
  spec: evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig

### Acceptance Criteria (story contract)
1. A real synthetic owner run resolves a profile, registers a complete trial, appends trial/error events, registers descriptors, evaluates dependencies, and verifies all heads and manifests.
2. The E2e command or test exits nonzero on the first integrity, authorization, dependency, projection, or contract failure and emits machine-readable JSON identifying the failed stage.
3. The run records canonical success or error events with the prior event head and never invents an artifact.
4. 4. A copied ledger with one rewritten, deleted, or reordered line fails verification while the original remains valid. 5. A stale, UNKNOWN-criticality, or quarantined dependency produces INVALID dependent metrics and BLOCKED rather than substitution. 6. The initially resolved configuration hash remains unchanged after editing the source profile.

## Testing Requirements
- E2e tests ONLY. No unit tests, no integration tests. Tests must exercise the full system as a user would. No mocks of any kind.
- Commands to run: `uv run pytest tests/e2e/test_governance_integrity.py`.

## MANDATORY SKILLS
- None identified.

## Delivery Requirements
- Developer must paste unedited E2e output and artifact/event hashes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label.

## nd_contract
status: new

### evidence
- Created 2026-09-18 as the final capstone of epic VK-egll.
- All sibling dependencies are explicitly recorded in nd.

### proof
- [ ] AC #1: Owner-perspective scenario executes successfully.
- [ ] AC #2: Failure path exits nonzero with machine-readable JSON.
- [ ] AC #3: Event integrity and no-artifact-on-error behavior are verified.
- [ ] AC #4: 4. A copied ledger with one rewritten, deleted, or reordered line fails verification while the original remains valid. 5. A stale, UNKNOWN-criticality, or quarantined dependency produces INVALID dependent metrics and BLOCKED rather than substitution. 6. The initially resolved configuration hash remains unchanged after editing the source profile.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: include durability sibling

GENERAL RULE SWEEP: Every epic capstone is blocked by every sibling.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-3v14: src/gauntlet/ledger/backup.py -> verify_backup(bundle_path: Path) -> BackupVerification
  spec: verify_backup(bundle_path: Path) -> BackupVerification

### Acceptance Criteria (repair revision)
1. The governance E2e drill proves a required-class backup restores and verifies before the epic closes.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The governance E2e drill proves a required-class backup restores and verifies before the epic closes.


## History
- 2026-09-18T23:31:38Z dep_added: blocked_by VK-1vhm
- 2026-09-18T23:31:38Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:38Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:38Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:47Z dep_added: blocks VK-hiuk
- 2026-09-19T01:37:43Z dep_added: blocked_by VK-3v14
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q

## Links
- Parent: [[VK-egll]]
- Blocks: [[VK-hiuk]]
- Blocked by: [[VK-kmbs]], [[VK-jkkn]], [[VK-3v14]]
- Was blocked by: [[VK-1vhm]], [[VK-wa2q]]

## Comments
