---
id: VK-aej2
title: "Establish synthetic deterministic gate precedence"
status: in_progress
priority: 0
type: feature
labels: [integration, phase-1, walking-skeleton]
parent: VK-1rbc
created_at: 2026-09-19T01:37:42Z
created_by: speed
updated_at: 2026-09-19T04:45:11Z
content_hash: "sha256:1d5b11c2d0818e416e04bc1e37ce8996680c99406354fbeff7b413d01111cea1"
blocks: [VK-2e0k, VK-uyca]
was_blocked_by: [VK-1vhm]
assignee: dev-VK-aej2
follows: [VK-1vhm]
---

## Description
## USER INTENT
The owner needs the fail-closed decision pattern established before downstream evidence producers determine a real candidate outcome.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement the pure precedence kernel and synthetic panel-contract harness. Rules return PASS, FAIL, BLOCKED, or PENDING/INSUFFICIENT_EVIDENCE. Aggregate precedence is exactly: any BLOCKED, else any FAIL, else any PENDING or INSUFFICIENT_EVIDENCE, else PASS. Synthetic bundles carry rule IDs, formula IDs, policy/ruleset hashes, input hashes, values, comparators, thresholds, labels, states, and reasons. The kernel does no I/O, read wall-clock/current data, call an LLM, or infer thresholds.

Phase 1 boundaries:
- No order placement, real-money exposure, public API, daemon, multi-tenant access, or social claim.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted.

## OUT OF SCOPE
- Full real-evidence gate integration and manifest loading: owned by the existing deterministic gate story.
- Decision Snapshot persistence: owned by the snapshot story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~5 files, under 450 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/policy/precedence.py -> evaluate_precedence(rule_results: list[RuleResult]) -> GateState
- src/gauntlet/policy/synthetic.py -> build_synthetic_panel_bundle(seed: int) -> SyntheticEvidenceBundle

CONSUMES:
- VK-1vhm: src/gauntlet/contracts/canonical.py -> canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str
  spec: canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str

### Acceptance Criteria (story contract)
1. Exhaustive combinations prove BLOCKED > FAIL > INSUFFICIENT_EVIDENCE > PASS independent of rule order.
2. Synthetic panel bundles are content-hashed and contain every inspectable rule input and result field declared above.
3. Unknown or malformed rule output becomes BLOCKED.
4. The kernel performs no external I/O, current-data query, LLM call, or threshold inference.
5. A deterministic seed reproduces identical canonical bundle and output hashes.
6. The user-facing test output displays the selected precedence branch and every failed or blocked synthetic rule.

## Testing Requirements
- Unit: Exhaustively test state combinations, unknowns, malformed bundles, ordering independence, and deterministic hashes.
- Integration tests: MANDATORY (no mocks). Run the synthetic bundle through the real precedence function as a local end-to-end command/test with no mocks and verify canonical output plus selected branch.
- Commands to run: `uv run pytest tests/policy/test_precedence_skeleton.py`.

## MANDATORY SKILLS
None identified.

## Delivery Requirements
- Developer must paste test or CI output snippets into story notes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label; PM acceptance remains separate.

## nd_contract
status: new

### evidence
- Created 2026-09-18 to repair the documented Anchor rejection in the live Phase 1 backlog.
- Epic containment: VK-1rbc.

### proof
- [ ] AC #1: Exhaustive combinations prove BLOCKED > FAIL > INSUFFICIENT_EVIDENCE > PASS independent of rule order.
- [ ] AC #2: Synthetic panel bundles are content-hashed and contain every inspectable rule input and result field declared above.
- [ ] AC #3: Unknown or malformed rule output becomes BLOCKED.
- [ ] AC #4: The kernel performs no external I/O, current-data query, LLM call, or threshold inference.
- [ ] AC #5: A deterministic seed reproduces identical canonical bundle and output hashes.
- [ ] AC #6: The user-facing test output displays the selected precedence branch and every failed or blocked synthetic rule.

## Acceptance Criteria


## Design


## Notes
## nd_contract
status: in_progress

### evidence
- Claimed by developer agent for story/VK-aej2 on 2026-09-18.

### proof
- [ ] (pending)

## History
- 2026-09-19T01:37:42Z dep_added: blocked_by VK-1vhm
- 2026-09-19T01:37:43Z dep_added: blocks VK-2e0k
- 2026-09-19T01:37:44Z dep_added: blocks VK-uyca
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm
- 2026-09-19T04:45:11Z status: open -> in_progress
- 2026-09-19T04:45:11Z auto-follows: linked to predecessor VK-1vhm
- 2026-09-19T04:45:11Z claimed by dev-VK-aej2

## Links
- Parent: [[VK-1rbc]]
- Blocks: [[VK-2e0k]], [[VK-uyca]]
- Was blocked by: [[VK-1vhm]]
- Follows: [[VK-1vhm]]

## Comments

### 2026-09-19T01:39:43Z speed
RECOMMEND hard-tdd: exhaustive precedence and synthetic gate contracts are the core P0 QC pattern. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
