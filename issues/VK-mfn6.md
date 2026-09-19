---
id: VK-mfn6
title: "Register Kronos model lineage"
status: open
priority: 2
type: feature
labels: [integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:19Z
created_by: speed
updated_at: 2026-09-18T23:31:19Z
content_hash: "sha256:eadbf04df4cc374b4b17206166c727dfea3440381ddd64f5376e958f8feef165"
blocked_by: [VK-jkkn, VK-kmbs, VK-wa2q]
blocks: [VK-7ubc, VK-zvia, VK-ldg1]
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


## History
- 2026-09-18T23:31:19Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:19Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:19Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:20Z dep_added: blocks VK-7ubc
- 2026-09-18T23:31:26Z dep_added: blocks VK-zvia
- 2026-09-18T23:31:40Z dep_added: blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-7ubc]], [[VK-zvia]], [[VK-ldg1]]
- Blocked by: [[VK-jkkn]], [[VK-kmbs]], [[VK-wa2q]]

## Comments
