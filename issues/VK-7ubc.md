---
id: VK-7ubc
title: "Adapt Kronos with frozen temporal splits"
status: open
priority: 2
type: feature
labels: [integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:20Z
created_by: speed
updated_at: 2026-09-18T23:31:20Z
content_hash: "sha256:b46c6df04de81c14ea9df209ed5cbc9fccd8722114258b326b9edad5377f1009"
blocked_by: [VK-mfn6]
blocks: [VK-ldg1]
---

## Description
## USER INTENT
The owner needs model adaptation to remain a registered trial so checkpoint selection cannot reuse test or prospective outcomes.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement Kronos adaptation records containing dataset manifests, normalization statistics, train/validation/test windows, checkpoint, logs, and resolved configuration. Checkpoint selection follows the training/validation boundary, never test performance. Every split has UTC timestamps, bars, horizon, lookback, normalization window, target horizon, embargo/purge gaps, fold order, and selection locks. A sample can train or tune only when both feature observation time and target completion time precede the boundary. Frozen evaluation membership and source hashes cannot change; corrections create a new trial.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Walk-forward trading evaluation: lands in judge work.
- Live model serving or daemon: prohibited Phase 1 surface.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/model/adaptation.py -> run_adaptation(manifest: AdaptationManifest, model: ModelRegistration) -> AdaptationRun

CONSUMES:
- VK-mfn6: src/gauntlet/model/registry.py -> register_model(entry: ModelRegistryEntry) -> ModelRegistration; run_inference(context: FrozenContext, model: ModelRegistration, profile: ModelProfile) -> InferenceArtifact
  spec: register_model(entry: ModelRegistryEntry) -> ModelRegistration; run_inference(context: FrozenContext, model: ModelRegistration, profile: ModelProfile) -> InferenceArtifact

### Acceptance Criteria (story contract)
1. Adaptation creates or references a prior trial registration before training and binds exact split, feature, source, policy, and config hashes.
2. A target whose completion crosses the training boundary is rejected.
3. Normalization and checkpoint selection cannot use validation/test/prospective information.
4. Every fold and checkpoint selection is logged with actors, timestamps, metric inputs, and reason.
5. Mutating a frozen evaluation population creates a new trial and preserves the invalid population.
6. Replay resolves code version, dependency lock, source hashes, checkpoint, seeds, sampler settings, and normalization version.

## Testing Requirements
- Unit: Test boundary crossing, embargo/purge, fold locks, checkpoint selection, and replay metadata.
- Integration tests: MANDATORY (no mocks). Run a tiny deterministic adaptation on synthetic registered data, verify the run manifest, then mutate one frozen source and prove a new trial is required.
- Commands to run: `uv run pytest tests/model/test_adaptation.py`.

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
- [ ] AC #1: Adaptation creates or references a prior trial registration before training and binds exact split, feature, source, policy, and config hashes.
- [ ] AC #2: A target whose completion crosses the training boundary is rejected.
- [ ] AC #3: Normalization and checkpoint selection cannot use validation/test/prospective information.
- [ ] AC #4: Every fold and checkpoint selection is logged with actors, timestamps, metric inputs, and reason.
- [ ] AC #5: Mutating a frozen evaluation population creates a new trial and preserves the invalid population.
- [ ] AC #6: Replay resolves code version, dependency lock, source hashes, checkpoint, seeds, sampler settings, and normalization version.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:20Z dep_added: blocked_by VK-mfn6
- 2026-09-18T23:31:40Z dep_added: blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-ldg1]]
- Blocked by: [[VK-mfn6]]

## Comments
