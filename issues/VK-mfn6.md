---
id: VK-mfn6
title: "Register Kronos model lineage"
status: closed
priority: 2
type: feature
labels: [integration, phase-1, accepted]
parent: VK-u40v
created_at: 2026-09-18T23:31:19Z
created_by: speed
updated_at: 2026-09-19T17:06:08Z
content_hash: "sha256:b1e41f03f737dd6b589fcc2abdaa116b8a617262dc8619e3d068a828d144d75a"
was_blocked_by: [VK-wa2q, VK-kmbs, VK-jkkn]
assignee: dev-VK-mfn6
follows: [VK-wa2q, VK-kmbs, VK-jkkn]
closed_at: 2026-09-19T17:06:07Z
close_reason: "Accepted: independently reran story/full suites (7/7 and 59/59), pvg verify, git diff check, static dependency/secret scans, deterministic hash review, and LOC/budget checks. Exact checkpoint lineage, point-in-time bounds, replayability, MODELED semantics, and missing-byte BLOCKED behavior are verified."
---

## Description
## USER INTENT
The owner needs every probability and forecast traceable to exact model bytes, context bounds, and sampling behavior before it can influence a decision.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement the Kronos registry and inference adapter. A registry entry records base/fine-tuned checkpoint hashes, architecture/config, training and domain window, license/provenance, hardware, and seeds. Inference records point-in-time context bounds, sampling parameters and sample count, generated paths, probabilities/path shares, semantics, and model fingerprint. Normalization uses only the lookback portion. Checkpoint bytes and preprocessing code/config hashes are required for replay. Model outputs are information sources and must later pass calibration; they are not oracle status.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Fine-tuning/adaptation split discipline: sibling adaptation story.
- Calibration scoring: lands in lab work.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~7 files, under 650 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/model/registry.py -> register_model(entry: ModelRegistryEntry) -> ModelRegistration
- src/gauntlet/model/inference.py -> run_inference(context: FrozenContext, model: ModelRegistration, profile: ModelProfile) -> InferenceArtifact

CONSUMES:
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-kmbs: src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
  spec: register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration

### Acceptance Criteria (story contract)
1. Registry entries reject missing checkpoint bytes, architecture/config hash, training/domain window, license/provenance, hardware, or seeds.
2. Inference artifacts bind exact model fingerprint, frozen context hash, lookback-only normalization, sampler settings, sample count, and output semantics.
3. Point-in-time context bounds prevent future features or targets from entering the context.
4. Generated paths, probabilities, and path shares retain OBSERVED/MODELED labeling and downstream calibration metadata.
5. Replay inputs include checkpoint bytes and preprocessing code/config hashes; missing bytes make the artifact non-replayable and dependent gates BLOCKED.
6. Duplicate checkpoint registration preserves both immutable observations rather than replacing lineage.

## Testing Requirements
- Unit: Test registry validation, normalization bounds, fingerprint stability, and replay input completeness.
- Integration tests: MANDATORY (no mocks). Run inference twice against a real tiny registered model artifact with a fixed seed and verify context, hashes, and deterministic output or declared tolerance.
- Commands to run: `uv run pytest tests/model/test_registry_inference.py`.

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
- [ ] AC #1: Registry entries reject missing checkpoint bytes, architecture/config hash, training/domain window, license/provenance, hardware, or seeds.
- [ ] AC #2: Inference artifacts bind exact model fingerprint, frozen context hash, lookback-only normalization, sampler settings, sample count, and output semantics.
- [ ] AC #3: Point-in-time context bounds prevent future features or targets from entering the context.
- [ ] AC #4: Generated paths, probabilities, and path shares retain OBSERVED/MODELED labeling and downstream calibration metadata.
- [ ] AC #5: Replay inputs include checkpoint bytes and preprocessing code/config hashes; missing bytes make the artifact non-replayable and dependent gates BLOCKED.
- [ ] AC #6: Duplicate checkpoint registration preserves both immutable observations rather than replacing lineage.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-19.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Commands run:

```bash
cd /Users/speed/Downloads/AI_Videos/google-usercontent/gauntlet/.claude/worktrees/dev-VK-mfn6
git diff --check
uv run pytest tests/model/test_registry_inference.py
uv run pytest tests/
pvg verify src/gauntlet/model/__init__.py src/gauntlet/model/inference.py src/gauntlet/model/registry.py tests/model/test_registry_inference.py --format=text
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Story tests: 7/7 passed.
- Full suite: 59/59 passed.
- `pvg verify`: passed with 4 files scanned and zero issues.
- Diff budget: 647 changed LOC, below the 650 LOC ceiling.
- Static source scan found no database engine, network client, subprocess, credential, or secret-bearing implementation.
- Deterministic replay hashes reported by the real tiny model integration remain stable:
  - model fingerprint `ba152251750337b9ef2dabbd965e9a37bcd8d6f1cf7f2d2e38889bbbbf91c8e7`
  - descriptor `bf5efb9f49d527438f74d1877f335fb4503088a6b84c9698b1564a83db9bc077`
  - context `7f6949c0671bb99ca6761f107b8fd7ad00d01f12f8594d9e5aad746c2408895f`
  - artifact `9a5a8c6bec0226977ea102318a09eeb81b7c3a7258947a325a9b0ab5d6bd22da`

### CI/Test Results

```text
tests/model/test_registry_inference.py: 7 passed
full suite: 59 passed
pvg verify: PASSED (4 files scanned, 0 issues)
```

Summary: implemented fail-closed Kronos model lineage registration, immutable checkpoint/descriptor/event evidence, exact model fingerprints, point-in-time context enforcement, lookback-only normalization, deterministic local inference, MODELED output semantics, replayable checkpoint/preprocessing evidence, and BLOCKED behavior when exact bytes are missing.

Commit SHA: 63d302a

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Registry rejects incomplete lineage | PASS | Validation tests. |
| 2. Inference binds model/context/sampling/semantics | PASS | Integration tests and stable hashes. |
| 3. Future features/targets rejected | PASS | Point-in-time parameterized tests. |
| 4. Paths/probabilities/shares remain MODELED with calibration metadata | PASS | Inference artifact assertions. |
| 5. Missing bytes create non-replayable BLOCKED output | PASS | Missing-checkpoint test. |
| 6. Duplicate checkpoint observations preserved | PASS | Duplicate-lineage test. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-18T23:31:19Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:19Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:19Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:20Z dep_added: blocks VK-7ubc
- 2026-09-18T23:31:26Z dep_added: blocks VK-zvia
- 2026-09-18T23:31:40Z dep_added: blocks VK-ldg1
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs
- 2026-09-19T04:41:26Z dep_removed: was_blocked_by VK-jkkn
- 2026-09-19T16:35:13Z status: open -> in_progress
- 2026-09-19T16:35:13Z auto-follows: linked to predecessor VK-wa2q
- 2026-09-19T16:35:13Z auto-follows: linked to predecessor VK-kmbs
- 2026-09-19T16:35:13Z auto-follows: linked to predecessor VK-jkkn
- 2026-09-19T16:35:13Z claimed by dev-VK-mfn6
- 2026-09-19T17:05:08Z status: in_progress -> in_progress
- 2026-09-19T17:06:08Z status: in_progress -> closed
- 2026-09-19T17:06:08Z dep_removed: no_longer_blocks VK-7ubc
- 2026-09-19T17:06:08Z dep_removed: no_longer_blocks VK-zvia
- 2026-09-19T17:06:08Z dep_removed: no_longer_blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Was blocked by: [[VK-wa2q]], [[VK-kmbs]], [[VK-jkkn]]
- Follows: [[VK-wa2q]], [[VK-kmbs]], [[VK-jkkn]]

## Comments
