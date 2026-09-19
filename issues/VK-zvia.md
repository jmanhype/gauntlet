---
id: VK-zvia
title: "Score decision-signal calibration"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-18T23:31:26Z
created_by: speed
updated_at: 2026-09-18T23:31:26Z
content_hash: "sha256:b752a5f7f431d30b6cbe5009e794e793babb91b0e4b50fb3c5d5541df0a309f4"
blocks: [VK-2e0k, VK-vqvy]
was_blocked_by: [VK-ddoh, VK-mfn6]
---

## Description
## USER INTENT
The owner needs confidence claims measured on untouched outcomes rather than trusting marketed capability.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Compute Brier score, expected calibration error, reliability by confidence bin, threshold sweep, coverage/selective-risk, and gated-versus-ungated/abstain comparison from decision/confidence records with immutable outcomes and explicit confidence semantics. Calibration applies to every probability, confidence, strength, or path-share signal used in a decision and to external confidence claims. A confidence gate fails when selective performance is worse than abstaining or ungated policy under the predeclared tolerance. Historical records are not prospective evidence.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Collecting external claims: Scarlett collector story.
- Choosing the policy threshold: immutable policy/decision story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/lab/calibration.py -> compute_calibration(records: list[ConfidenceOutcome], policy: CalibrationPolicy) -> CalibrationPanel

CONSUMES:
- VK-ddoh: src/gauntlet/judge/prospective.py -> resolve_outcome(record_id: str, outcome: ProspectiveOutcome) -> ProspectiveRecord
  spec: resolve_outcome(record_id: str, outcome: ProspectiveOutcome) -> ProspectiveRecord
- VK-mfn6: src/gauntlet/model/inference.py -> run_inference(context: FrozenContext, model: ModelRegistration, profile: ModelProfile) -> InferenceArtifact
  spec: run_inference(context: FrozenContext, model: ModelRegistration, profile: ModelProfile) -> InferenceArtifact

### Acceptance Criteria (story contract)
1. Panel reports Brier, ECE, reliability bins, threshold sweep, coverage/selective-risk, gated/ungated comparison, versions, and verdicts.
2. Confidence semantics and outcome definitions are explicit and immutable per panel.
3. Only untouched prospective outcomes satisfy prospective calibration; historical labels are reported separately.
4. External confidence claims are decomposition/calibration evidence, never accepted capability claims.
5. Worse-than-abstain or worse-than-ungated selective performance fails under predeclared tolerance.
6. Missing outcomes or confidence semantics yield BLOCKED rather than a neutral score.

## Testing Requirements
- Unit: Use published small-vector oracles for Brier/ECE and property-test bin boundaries.
- Integration tests: MANDATORY (no mocks). Score real synthetic prospective records from committed pre-outcome signals and separately score a historical set; verify prospective/historical classification and verdicts.
- Commands to run: `uv run pytest tests/lab/test_calibration.py`.

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
- Epic containment: VK-0auj.

### proof
- [ ] AC #1: Panel reports Brier, ECE, reliability bins, threshold sweep, coverage/selective-risk, gated/ungated comparison, versions, and verdicts.
- [ ] AC #2: Confidence semantics and outcome definitions are explicit and immutable per panel.
- [ ] AC #3: Only untouched prospective outcomes satisfy prospective calibration; historical labels are reported separately.
- [ ] AC #4: External confidence claims are decomposition/calibration evidence, never accepted capability claims.
- [ ] AC #5: Worse-than-abstain or worse-than-ungated selective performance fails under predeclared tolerance.
- [ ] AC #6: Missing outcomes or confidence semantics yield BLOCKED rather than a neutral score.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:26Z dep_added: blocked_by VK-ddoh
- 2026-09-18T23:31:26Z dep_added: blocked_by VK-mfn6
- 2026-09-18T23:31:30Z dep_added: blocks VK-2e0k
- 2026-09-18T23:31:43Z dep_added: blocks VK-vqvy
- 2026-09-19T16:28:10Z dep_removed: was_blocked_by VK-ddoh
- 2026-09-19T17:06:08Z dep_removed: was_blocked_by VK-mfn6

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-2e0k]], [[VK-vqvy]]
- Was blocked by: [[VK-ddoh]], [[VK-mfn6]]

## Comments
