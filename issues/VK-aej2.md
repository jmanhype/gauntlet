---
id: VK-aej2
title: "Establish synthetic deterministic gate precedence"
status: closed
priority: 0
type: feature
labels: [integration, phase-1, walking-skeleton, delivered, accepted]
parent: VK-1rbc
created_at: 2026-09-19T01:37:42Z
created_by: speed
updated_at: 2026-09-19T05:02:19Z
content_hash: "sha256:f9e442e42148d5dde29e64eff70269d98d2b47679a6a75bb1466d54c5d0ad03f"
was_blocked_by: [VK-1vhm]
assignee: dev-VK-aej2
follows: [VK-1vhm]
closed_at: 2026-09-19T05:02:19Z
close_reason: "Accepted: independently verified fixed precedence, deterministic schema-valid synthetic bundles, fail-closed malformed handling, purity, hashes, integration output, tests, coverage, scope, and diff budget at db2c5b8."
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
status: delivered

### evidence
- Branch: story/VK-aej2
- Commit: db2c5b8ee16511557064530c6429142df8da1e60
- Required test: uv run pytest tests/policy/test_precedence_skeleton.py -> 8 passed in 0.02s
- Full suite: uv run pytest tests/ -> 43 passed in 0.43s
- Scoped coverage: uv run --with pytest-cov pytest tests/ --cov=gauntlet.policy --cov=gauntlet.contracts.schemas --cov-report=term -> TOTAL 89% (228 statements, 25 missed)
- Delivery gate: pvg verify <5 changed files> --include-tests --format=text -> VERIFY: PASSED (5 files scanned, 0 issues)
- Delivery label: pvg story deliver VK-aej2 -> OK

### proof
- [x] AC #1: Exhaustive combinations and order permutations prove BLOCKED > FAIL > INSUFFICIENT_EVIDENCE > PASS.
- [x] AC #2: Synthetic panel bundle is content-hashed and exposes every declared inspectable field.
- [x] AC #3: Unknown or malformed rule output becomes BLOCKED.
- [x] AC #4: Kernel performs no external I/O, current-data query, LLM call, or threshold inference.
- [x] AC #5: Same seed reproduces canonical bundle/output hashes; different seed changes content.
- [x] AC #6: User-facing real integration output shows selected branch and every failed/blocked synthetic rule.

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
  - `uv run pytest tests/policy/test_precedence_skeleton.py`
  - `uv run pytest tests/`
  - `uv run --with pytest-cov pytest tests/ --cov=gauntlet.policy --cov=gauntlet.contracts.schemas --cov-report=term`
- Required targeted result: `8 passed in 0.02s`.
- Full-suite result: `43 passed in 0.43s` (baseline before change: `35 passed in 0.50s`).
- Scoped coverage: `TOTAL 228 statements, 25 missed, 89%`; new precedence module `100%`, policy package `100%`, synthetic module `83%`, extended schema validator `88%`.
- Warnings/failures: none in the recorded targeted, full, and coverage runs.
- Key user-facing integration output:
  - `AGGREGATE: BLOCKED (any BLOCKED)`
  - `OUTPUT_HASH: sha256:409b3773cb6832a298bd8364fd4d4f3481245facc42ae48fe5a452aa929f17a9`
  - `FAILED_OR_BLOCKED_RULES:`
  - `- synthetic.expectancy: FAIL — synthetic expectancy is below zero`
  - `- synthetic.replay_integrity: BLOCKED — one synthetic replay input is intentionally unavailable`

### Commit
- Branch: `story/VK-aej2`
- SHA: `db2c5b8ee16511557064530c6429142df8da1e60`
- Commit: `feat(VK-aej2): establish deterministic gate precedence`
- Diff: 5 files, 441 insertions, 1 deletion (within the ~5-file/under-450-changed-LOC budget).
- Push: intentionally not performed; dispatcher requested commit only and did not authorize push.

### pvg verify
- Command: `pvg verify src/gauntlet/contracts/schemas.py src/gauntlet/policy/__init__.py src/gauntlet/policy/precedence.py src/gauntlet/policy/synthetic.py tests/policy/test_precedence_skeleton.py --include-tests --format=text`
- Output: `VERIFY: PASSED (5 files scanned, 0 issues)`

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | Exhaustive combinations prove BLOCKED > FAIL > INSUFFICIENT_EVIDENCE > PASS independent of order | `src/gauntlet/policy/precedence.py:43` | `tests/policy/test_precedence_skeleton.py:25,32` | PASS |
| 2 | Content-hashed synthetic bundle contains all inspectable IDs, hashes, values, comparators, thresholds, labels, states, and reasons | `src/gauntlet/policy/synthetic.py:53,117`; schema at `src/gauntlet/contracts/schemas.py:26` | `tests/policy/test_precedence_skeleton.py:68,99` | PASS |
| 3 | Unknown or malformed rule output becomes BLOCKED | `src/gauntlet/policy/precedence.py:51` | `tests/policy/test_precedence_skeleton.py:41,99` | PASS |
| 4 | No external I/O, current-data query, LLM call, or threshold inference | pure `precedence.py`; seeded pure `synthetic.py` | `tests/policy/test_precedence_skeleton.py:52` plus real end-to-end test at line 116 | PASS |
| 5 | Deterministic seed reproduces canonical bundle and output hashes; different seed changes content | `src/gauntlet/policy/synthetic.py:117` | `tests/policy/test_precedence_skeleton.py:87` | PASS |
| 6 | User-facing output displays selected precedence branch and every failed/blocked synthetic rule | `SyntheticEvidenceBundle.output` in `src/gauntlet/policy/synthetic.py:124` | `tests/policy/test_precedence_skeleton.py:116` | PASS |

LEARNINGS:
- The synthetic bundle can remain completely local and deterministic by deriving only seed-bound artifact hashes from fixed rule contracts; rule states and thresholds stay explicit rather than inferred.
- The first malformed-bundle test exposed that the generic schema string check accepted an empty generator version; adding synthetic-specific non-empty validation closed that fail-closed gap before delivery.
- `pytest-cov` is not a project dependency, so scoped coverage was measured with an ephemeral `uv run --with pytest-cov` invocation without changing the project manifest or lockfile.

### OBSERVATIONS (unrelated)
- `pvg notes search` exited 1 because it selected vault `Claude`, while the available vault list included `nd-vault` and others. Story context was complete through `pvg nd show`, so implementation was not blocked.

### DISCOVERED_BUG
  title: pvg notes search selects an unavailable configured vault
  context: While following the developer vault-context check, both `pvg notes search 'VK-aej2 precedence synthetic evidence bundle'` and the pattern query failed with `vlt: vault "Claude" not found`. The live nd vault resolves correctly through `pvg nd`, so this appears isolated to pvg notes vault selection/configuration rather than backlog storage.
  affected_files: pvg notes/vault configuration (no repository source file identified)
  discovered_during: VK-aej2

## nd_contract
status: delivered

### evidence
- Commit: `db2c5b8ee16511557064530c6429142df8da1e60` on `story/VK-aej2`.
- Targeted: `uv run pytest tests/policy/test_precedence_skeleton.py` → `8 passed in 0.02s`.
- Full: `uv run pytest tests/` → `43 passed in 0.43s`.
- Scoped coverage: `89%` (228 statements, 25 missed).
- Static delivery gate: `pvg verify ... --include-tests --format=text` → `VERIFY: PASSED (5 files scanned, 0 issues)`.
- No merge and no push performed.

### proof
- [x] AC #1: Exhaustive state/multiplicity combinations and order permutations prove fixed precedence. (Code: `src/gauntlet/policy/precedence.py`, Test: `tests/policy/test_precedence_skeleton.py`)
- [x] AC #2: Synthetic bundle is canonical/content/output hashed and exposes every declared inspectable field. (Code: `src/gauntlet/policy/synthetic.py`, Test: same test file)
- [x] AC #3: Unknown and malformed rule outputs aggregate to BLOCKED. (Code: `src/gauntlet/policy/precedence.py`, Test: same test file)
- [x] AC #4: Kernel has no I/O/current-data/LLM/threshold-inference path. (Code: `src/gauntlet/policy/precedence.py`, Test: AST purity test and real integration)
- [x] AC #5: Same seed is byte/hash identical; different seed changes canonical content. (Code: `src/gauntlet/policy/synthetic.py`, Test: same test file)
- [x] AC #6: Real no-mock integration prints selected branch, output hash, and both failed/blocked rules. (Code: `src/gauntlet/policy/synthetic.py`, Test: same test file)

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
- 2026-09-19T04:57:30Z status: in_progress -> in_progress
- 2026-09-19T05:02:19Z status: in_progress -> closed
- 2026-09-19T05:02:19Z dep_removed: no_longer_blocks VK-2e0k
- 2026-09-19T05:02:19Z dep_removed: no_longer_blocks VK-uyca

## Links
- Parent: [[VK-1rbc]]
- Was blocked by: [[VK-1vhm]]
- Follows: [[VK-1vhm]]

## Comments

### 2026-09-19T01:39:43Z speed
RECOMMEND hard-tdd: exhaustive precedence and synthetic gate contracts are the core P0 QC pattern. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
