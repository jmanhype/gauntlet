---
id: VK-7ubc
title: "Adapt Kronos with frozen temporal splits"
status: closed
priority: 2
type: feature
labels: [integration, phase-1, delivered]
parent: VK-u40v
created_at: 2026-09-18T23:31:20Z
created_by: speed
updated_at: 2026-09-20T04:15:27Z
content_hash: "sha256:ca51d5fc8dbb8aa8d60af8e6a36c92be7d6130949fb801cf936261b5b3181696"
was_blocked_by: [VK-mfn6]
assignee: dev-VK-7ubc
follows: [VK-mfn6]
closed_at: 2026-09-20T04:15:27Z
close_reason: "Accepted: independently reran targeted/full tests, compile, scoped verify, static/secret checks, reviewed all six AC and immutable trial/replay evidence. Structural verify-delivery EOF warning is a recorded note-ordering false negative; substantive proof is complete."
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
Summary: frozen-split Kronos adaptation delivered and independently verified.

Commit SHA: 05e06326e02d0e3fd9b19c5e9b21be672f941413
## PM Decision
ACCEPTED [2026-09-20]: Independently reviewed the three-file diff, reran targeted/full suites, py_compile, scoped pvg verify, whitespace/static/secret checks, and confirmed the 546-insertion budget and all six AC. The remaining verify-delivery EOF item is a note-ordering false negative after multiple note appends; the required implementation, CI, summary, commit, proof, and AC fields are present.

## nd_contract
status: accepted

### evidence
- Independent targeted suite: 7/7 passed.
- Independent full suite: 66/66 passed.
- Scoped verify: 2 files, 0 issues.
- Commit: 05e06326e02d0e3fd9b19c5e9b21be672f941413.

### proof
- [x] AC-by-AC independently verified from code, tests, hashes, and command output.

## PM Decision

ACCEPTD_MARKER

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Delivery Evidence Addendum

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/gauntlet/.claude/worktrees/dev-VK-7ubc
uv run --frozen --group dev pytest -q tests/model/test_adaptation.py
uv run --frozen --group dev pytest -q
python3 -m py_compile src/gauntlet/model/adaptation.py src/gauntlet/model/__init__.py tests/model/test_adaptation.py
pvg verify src/gauntlet/model/adaptation.py src/gauntlet/model/__init__.py --format=text
git diff --check
```

### CI/Test Results

```text
tests/model/test_adaptation.py: 7 passed, 0 failed, 0 skipped
full suite: 66 passed, 0 failed, 0 skipped
py_compile: PASS
pvg verify: PASSED, 2 files scanned, 0 issues
git diff --check: PASS
```

The full suite prints the pre-existing intentional synthetic projection `AGGREGATE: BLOCKED` for two disclosed rules, but pytest exits 0 with 66 passed.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Prior trial registration and exact hashes | PASS | Trial precedes training; exact hashes are recorded. |
| 2. Boundary-crossing target rejected | PASS | Targeted test proves `FOLD_BOUNDARY_LEAK`. |
| 3. No future normalization/checkpoint selection | PASS | Train-only normalization and validation-only selection are asserted. |
| 4. Fold/checkpoint audit logs | PASS | Actor, UTC timestamp, metric input hashes, and reason are asserted. |
| 5. Frozen population mutation | PASS | New child trial preserves prior immutable bytes. |
| 6. Replay resolution | PASS | Complete replay metadata is asserted; gaps fail closed. |

## Summary

Implemented the frozen-split Kronos adaptation contract with immutable trial registration, leakage fail-closed checks, validation-only checkpoint selection, complete replay metadata, immutable artifacts/events, and real integration coverage.

Commit SHA: `05e06326e02d0e3fd9b19c5e9b21be672f941413`

## nd_contract
status: delivered

### evidence
- Targeted suite: 7/7 passed.
- Full suite: 66/66 passed.
- Scoped verifier: 2 files, 0 issues.
- Story commit: `05e06326e02d0e3fd9b19c5e9b21be672f941413`.

### proof
- [x] AC #1: Prior registration and exact hash binding.
- [x] AC #2: Boundary leakage rejected.
- [x] AC #3: Future normalization/selection excluded.
- [x] AC #4: Fold/checkpoint audit logs complete.
- [x] AC #5: Population mutation creates a new trial.
- [x] AC #6: Replay metadata complete and fail-closed.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run in the assigned story worktree:

```bash
uv run --frozen --group dev pytest -q tests/model/test_adaptation.py
uv run --frozen --group dev pytest -q
python3 -m py_compile src/gauntlet/model/adaptation.py src/gauntlet/model/__init__.py tests/model/test_adaptation.py
pvg verify src/gauntlet/model/adaptation.py src/gauntlet/model/__init__.py --format=text
git diff --check
```

Results:

- Targeted adaptation suite: 7 passed, 0 failed, 0 skipped.
- Full suite: 66 passed, 0 failed, 0 skipped. The output intentionally prints the existing synthetic gate projection `AGGREGATE: BLOCKED` with the two disclosed synthetic rules; pytest exits 0.
- Python compile: PASS.
- Scoped pvg verify: PASSED, 2 files scanned, 0 issues.
- git diff --check: PASS.
- Story commit: `05e06326e02d0e3fd9b19c5e9b21be672f941413`.

Source SHA-256:

```text
3b17f3fbb2fa68d11743f408bc80643fbe7a14c3fd1e64457d971a477a82f05e  src/gauntlet/model/adaptation.py
587c092de3e4e685ae6df86a26b00a95a84afa869c1de0ff9e6b2f2750b17b0e  tests/model/test_adaptation.py
adfd7f325a8e92924b3dc80b11dda36813f556d468ead15480601d6c80f1867a  src/gauntlet/model/__init__.py
```

Deterministic integration evidence:

```text
model_fingerprint=sha256:ba152251750337b9ef2dabbd965e9a37bcd8d6f1cf7f2d2e38889bbbbf91c8e7
source_descriptor_hash=sha256:718606e0ee65325354dc9ecfb77b1042ed4b9ce42ec30bf89f645c98e3ad58dc
trial_id=adaptation-sha256:f0495a4710d87d70eea6e909d4972432ead0599ec75379070764bf7ca1363836
run_hash=sha256:7301c11e0d8df6b65e78f350a6d61319bbe5f683abbf98562bc5faead37fdfa8
artifact_hash=sha256:cd224ce727948cd19640368aefb5be5e079c676c485e22113ef2a0efa308ba8d
checkpoint_hash=sha256:85bbd8dfe4849e23e23b35086f2375a9d07d1daea37554c36dd819ad316c1312
event_head_hash=sha256:ebb2d2d85d638f4016e0f0e0125c2f80a6fb719d99e6721dd9bc8dca69c5a9eb
chains_valid=True
```

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Prior trial registration and exact hashes | PASS | Trial is appended before training; report/trial bind manifest, population, split, model, feature, source, policy, and config hashes. |
| 2. Boundary-crossing target rejected | PASS | Parameterized integration test expects `FOLD_BOUNDARY_LEAK` before trial/artifact creation. |
| 3. No future normalization/checkpoint selection | PASS | Normalization uses train-complete rows only; selection is validation-only with test/prospective targets unread. |
| 4. Fold/checkpoint audit logs | PASS | Every log records actor, UTC timestamp, hashed metric inputs, and reason. |
| 5. Frozen population mutation | PASS | Registered v2 source creates a child trial; original descriptor/content/run bytes stay unchanged. |
| 6. Replay resolution | PASS | Replay records code, dependency lock, environment, sources, checkpoint, seeds, sampler, and normalization identity; gaps fail closed. |

LEARNINGS: Reusing the registered model/descriptor/ledger primitives kept adaptation replay immutable without introducing a database or external runtime. The strict 550-LOC budget was met at 546 insertions, but future sibling stories should split public dataclasses from execution logic if they approach the ceiling.

## History
- 2026-09-18T23:31:20Z dep_added: blocked_by VK-mfn6
- 2026-09-18T23:31:40Z dep_added: blocks VK-ldg1
- 2026-09-19T17:06:08Z dep_removed: was_blocked_by VK-mfn6
- 2026-09-20T03:45:51Z status: open -> in_progress
- 2026-09-20T03:45:51Z auto-follows: linked to predecessor VK-mfn6
- 2026-09-20T03:45:51Z claimed by dev-VK-7ubc
- 2026-09-20T04:09:17Z status: in_progress -> in_progress
- 2026-09-20T04:09:49Z status: in_progress -> in_progress
- 2026-09-20T04:10:20Z status: in_progress -> in_progress
- 2026-09-20T04:15:27Z status: in_progress -> closed
- 2026-09-20T04:15:27Z dep_removed: no_longer_blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Was blocked by: [[VK-mfn6]]
- Follows: [[VK-mfn6]]

## Comments
