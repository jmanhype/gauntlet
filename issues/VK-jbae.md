---
id: VK-jbae
title: "Account for factory search budgets"
status: open
priority: 3
type: feature
labels: [integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:21Z
created_by: speed
updated_at: 2026-09-18T23:31:21Z
content_hash: "sha256:667a16dd51e54628313753ca0fb1e18cab7060fa6aade3985da8af14cf877e44"
blocked_by: [VK-si5s, VK-wa2q]
blocks: [VK-aumt, VK-ldg1]
---

## Description
## USER INTENT
The owner needs every attempted variant and budget decision retained so multiplicity and unbounded continuation cannot be hidden.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Record every attempted variant, evaluation count, changed axis, parent lineage, seed, score, failure, and budget consumption from immutable race artifacts. Enforce one major experimental axis at a time. A multi-axis exception must already be owner-authorized in the ledger before result interpretation and state why one axis cannot answer, every changed axis, the attribution question, and the controlled isolation/decomposition plan. Family trial/compute/data budgets and stop conditions are predeclared; continuation requires owner-approved renewal.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Owner signature verification: lands in the authorization story.
- Statistical multiplicity panels: lands in lab robustness work.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 550 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/factory/accounting.py -> record_search_result(race: RaceResult, lineage: TrialLineage) -> SearchAccounting
- src/gauntlet/factory/budgets.py -> evaluate_family_budget(family_id: str, as_of: datetime) -> BudgetState

CONSUMES:
- VK-si5s: src/gauntlet/factory/launcher.py -> launch_factory_race(command: FactoryCommand) -> FactoryArtifact
  spec: launch_factory_race(command: FactoryCommand) -> FactoryArtifact
- VK-wa2q: src/gauntlet/ledger/trials.py -> append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult
  spec: append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult

### Acceptance Criteria (story contract)
1. Every attempted variant and evaluation is appended, including failed and null-result variants.
2. Changed axes and parent lineage are recorded for each search result.
3. A result cannot be interpreted under an unauthorized multi-axis declaration.
4. Family trial, compute, and data budget consumption is derived only from immutable ledger entries and race artifacts.
5. Budget or stop-condition exhaustion produces a family stop state and prevents further factory work until an owner-approved renewal.
6. Renewal records reason, changed axis, revised budget, and the prior failure that makes renewal plausible.

## Testing Requirements
- Unit: Test lineage reduction, axis comparison, budget arithmetic, stop conditions, and renewal validation.
- Integration tests: MANDATORY (no mocks). Run two real tiny race records into one ledger family, exhaust the declared budget, and prove the next race is rejected until a recorded renewal.
- Commands to run: `uv run pytest tests/factory/test_accounting.py`.

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
- [ ] AC #1: Every attempted variant and evaluation is appended, including failed and null-result variants.
- [ ] AC #2: Changed axes and parent lineage are recorded for each search result.
- [ ] AC #3: A result cannot be interpreted under an unauthorized multi-axis declaration.
- [ ] AC #4: Family trial, compute, and data budget consumption is derived only from immutable ledger entries and race artifacts.
- [ ] AC #5: Budget or stop-condition exhaustion produces a family stop state and prevents further factory work until an owner-approved renewal.
- [ ] AC #6: Renewal records reason, changed axis, revised budget, and the prior failure that makes renewal plausible.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:21Z dep_added: blocked_by VK-si5s
- 2026-09-18T23:31:21Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:27Z dep_added: blocks VK-aumt
- 2026-09-18T23:31:41Z dep_added: blocks VK-ldg1

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-aumt]], [[VK-ldg1]]
- Blocked by: [[VK-si5s]], [[VK-wa2q]]

## Comments
