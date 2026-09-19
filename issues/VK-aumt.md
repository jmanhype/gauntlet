---
id: VK-aumt
title: "Quantify uncertainty across trial lineage"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-18T23:31:26Z
created_by: speed
updated_at: 2026-09-18T23:31:26Z
content_hash: "sha256:6d080cc4692a94d369b22eb0415b2df4c2a591f7927d0fbec40069ff227f0fff"
blocked_by: [VK-0c4c, VK-8ch2, VK-jbae]
blocks: [VK-2e0k, VK-vqvy]
---

## Description
## USER INTENT
The owner needs repeated experimentation and non-normal behavior accounted for before any robustness claim.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Compute bootstrap or equivalent uncertainty plus explicit multiplicity accounting using PSR, DSR, PBO, FDR, or documented equivalents from locked evaluation trades, trial lineage, search accounting, and statistical policy. Report each diagnostic name, version, assumptions, inputs, PASS/FAIL/NOT_RUN, and omission reason. Missing, broken, or unverifiable lineage is gate-critical BLOCKED; valid lineage with insufficient observations is INSUFFICIENT_EVIDENCE; valid lineage disproving a threshold is FAIL.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Determining aggregate gate precedence: decision-engine story.
- Factory execution itself: factory stories.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~7 files, under 650 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/lab/robustness.py -> compute_robustness(trades: LockedTrades, lineage: TrialLineage, policy: StatisticalPolicy) -> RobustnessPanel

CONSUMES:
- VK-0c4c: src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
  spec: evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
- VK-8ch2: src/gauntlet/lab/effective_evidence.py -> compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel
  spec: compute_effective_evidence(rows: RowLevelEvidence, policy: EffectiveEvidencePolicy) -> EffectiveEvidencePanel
- VK-jbae: src/gauntlet/factory/accounting.py -> record_search_result(race: RaceResult, lineage: TrialLineage) -> SearchAccounting
  spec: record_search_result(race: RaceResult, lineage: TrialLineage) -> SearchAccounting

### Acceptance Criteria (story contract)
1. Panel includes uncertainty and at least the declared multiplicity diagnostics with versions and inputs.
2. Every omitted diagnostic is labeled NOT_RUN with a recorded justification.
3. Lineage includes total related trials, failed ancestors, search evaluations, changed axes, exceptions, risk versions, and venue/role declarations.
4. Broken or unverifiable lineage yields BLOCKED rather than an isolated candidate metric.
5. Non-normality and serial dependence are handled by the declared statistical policy.
6. Deterministic seeds/resamples are recorded and output is reproducible or within declared tolerance.

## Testing Requirements
- Unit: Property-test bootstrap stability, multiplicity accounting, serial handling, and lineage validation.
- Integration tests: MANDATORY (no mocks). Compute a real panel from exact trades plus immutable search lineage, then remove one ancestor event and prove lineage verification blocks the panel.
- Commands to run: `uv run pytest tests/lab/test_robustness.py`.

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
- [ ] AC #1: Panel includes uncertainty and at least the declared multiplicity diagnostics with versions and inputs.
- [ ] AC #2: Every omitted diagnostic is labeled NOT_RUN with a recorded justification.
- [ ] AC #3: Lineage includes total related trials, failed ancestors, search evaluations, changed axes, exceptions, risk versions, and venue/role declarations.
- [ ] AC #4: Broken or unverifiable lineage yields BLOCKED rather than an isolated candidate metric.
- [ ] AC #5: Non-normality and serial dependence are handled by the declared statistical policy.
- [ ] AC #6: Deterministic seeds/resamples are recorded and output is reproducible or within declared tolerance.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:27Z dep_added: blocked_by VK-0c4c
- 2026-09-18T23:31:27Z dep_added: blocked_by VK-8ch2
- 2026-09-18T23:31:27Z dep_added: blocked_by VK-jbae
- 2026-09-18T23:31:30Z dep_added: blocks VK-2e0k
- 2026-09-18T23:31:43Z dep_added: blocks VK-vqvy

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-2e0k]], [[VK-vqvy]]
- Blocked by: [[VK-0c4c]], [[VK-8ch2]], [[VK-jbae]]

## Comments
