---
id: VK-kmbs
title: "Register evidence descriptors with fail-closed dependencies"
status: closed
priority: 0
type: feature
labels: [integration, phase-1, accepted]
parent: VK-egll
created_at: 2026-09-18T23:31:15Z
created_by: speed
updated_at: 2026-09-19T04:12:00Z
content_hash: "sha256:972aefc756d1238795c578935f98b57add5b40678fe06b49df6c7fed3df3ac71"
was_blocked_by: [VK-1vhm, VK-wa2q]
follows: [VK-1vhm, VK-wa2q]
assignee: dev-VK-kmbs
closed_at: 2026-09-19T04:11:59Z
close_reason: "Accepted: deterministic DFS postorder closes recursive fail-closed propagation; full and targeted suites pass"
led_to: [VK-jkkn, VK-0c4c, VK-mfn6, VK-pg9j]
---

## Description
## USER INTENT
The owner needs every gate input classified and time-bound so stale, corrupt, or unknown evidence blocks promotion rather than masquerading as a valid result.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement immutable `gauntlet.evidence.v1` descriptors. Required fields are exactly `descriptor_schema`, `artifact_id`, `descriptor_id`, `descriptor_version`, `descriptor_hash`, `supersedes_descriptor_hash`, `effective_at_utc`, `superseded_at_utc`, `kind`, `venue_track`, `content_hash`, `source`, `observation_basis`, `coverage`, `freshness`, `quality`, `dependencies`, `criticality`, and `downstream_metrics`. Build a directed dependency graph and evaluate hash/schema validity, provenance reachability, freshness at `as_of`, quality, recursive dependency health, OBSERVED/MODELED eligibility, and policy criticality. Corrections and quarantine append superseding descriptor versions; original bytes never change. UNKNOWN criticality is gate-critical.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Collector-specific quarantine creation: lands in collector health work.
- Deterministic gate precedence after dependency evaluation: lands in the decision epic.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 750 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
- src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
- src/gauntlet/data/quarantine.py -> quarantine_descriptor(original_hash: str, reason: QuarantineReason, actor: Actor) -> DescriptorRegistration
- tests/integrity/test_dependency_graph.py -> closure, time travel, quarantine, and fail-closed cases

CONSUMES:
- VK-1vhm: src/gauntlet/contracts/schemas.py -> validate(instance: object, schema_id: str) -> ValidationResult
  spec: validate(instance: object, schema_id: str) -> ValidationResult
- VK-wa2q: src/gauntlet/ledger/trials.py -> append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult
  spec: append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult

### Acceptance Criteria (story contract)
1. Descriptor registration validates the complete schema, canonical hash, content hash, and dependency references before ledgering.
2. Dependency closure evaluates the seven architecture checks in order and returns a graph hash plus affected metrics and coverage.
3. Gate-critical missing, stale, corrupt, incomplete, replay-failed, or UNKNOWN inputs mark dependent metrics INVALID and the result BLOCKED.
4. Explicitly noncritical gaps leave unaffected metrics valid while visibly reducing coverage.
5. Descriptor selection honors `effective_at_utc <= as_of` and `superseded_at_utc > as_of`, while a run manifest bound to an exact hash keeps that hash.
6. Quarantine creates a superseding immutable version referencing the exact original descriptor hash; original bytes and historical resolution remain unchanged.
7. A MODELED value cannot satisfy a rule requiring OBSERVED outcomes, reserve state, realized fills, external claims, or untouched prospective evidence.
8. Malformed or cyclic dependency data returns `GRAPH_MALFORMED` rather than crashing or partially selecting descriptors.

## Testing Requirements
- Unit: Test schema rejection, time-bound selection, recursive health, criticality, observation basis, graph hashes, and malformed graphs.
- Integration tests: MANDATORY (no mocks). Register a real multi-level artifact graph in temporary storage, evaluate at multiple timestamps, quarantine one leaf, and prove both historical and later behavior without file mutation.
- Commands to run: `uv run pytest tests/integrity/test_dependency_graph.py`.

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
- Epic containment: VK-egll.

### proof
- [ ] AC #1: Descriptor registration validates the complete schema, canonical hash, content hash, and dependency references before ledgering.
- [ ] AC #2: Dependency closure evaluates the seven architecture checks in order and returns a graph hash plus affected metrics and coverage.
- [ ] AC #3: Gate-critical missing, stale, corrupt, incomplete, replay-failed, or UNKNOWN inputs mark dependent metrics INVALID and the result BLOCKED.
- [ ] AC #4: Explicitly noncritical gaps leave unaffected metrics valid while visibly reducing coverage.
- [ ] AC #5: Descriptor selection honors `effective_at_utc <= as_of` and `superseded_at_utc > as_of`, while a run manifest bound to an exact hash keeps that hash.
- [ ] AC #6: Quarantine creates a superseding immutable version referencing the exact original descriptor hash; original bytes and historical resolution remain unchanged.
- [ ] AC #7: A MODELED value cannot satisfy a rule requiring OBSERVED outcomes, reserve state, realized fills, external claims, or untouched prospective evidence.
- [ ] AC #8: Malformed or cyclic dependency data returns `GRAPH_MALFORMED` rather than crashing or partially selecting descriptors.

## Acceptance Criteria


## Design


## Notes
NORMATIVE DESCRIPTOR ENUMERATIONS (authoritative for implementation):
- criticality: GATE_CRITICAL | NON_CRITICAL | UNKNOWN; UNKNOWN is fail-closed and equivalent to GATE_CRITICAL until a policy version classifies it.
- quality.state: VALID | STALE | CORRUPT | INCOMPLETE | QUARANTINED.
- observation_basis: OBSERVED | MODELED.
- venue_track: solana_dex | hyperliquid | cross_venue_transfer | external.


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-18.

### proof
- [x] Story closed after accepted label was applied.


## PM Decision
ACCEPTED [2026-09-18]: Rework reviewed at amended commit 046ad04ec031f5a8846d3a728ce37b2f6fa1e711 and all acceptance criteria meet the bar.

## nd_contract
status: accepted

### evidence
- Full PM suite: `uv run pytest tests/` -> 21 passed in 0.33s, 0 failed, 0 skipped, no warnings.
- Targeted PM regression: `uv run pytest tests/integrity/test_dependency_graph.py::test_wide_graph_propagates_deep_gate_critical_failure_to_root -q` -> 1 passed in 0.09s.
- PM static verification: `pvg verify ... --include-tests --format=text` -> PASSED, 5 files, 0 issues.
- Inspected `_materialize`: deterministic DFS postorder appends every descriptor only after all resolved dependencies; `evaluate_dependencies` propagates in that order.
- Inspected real wide-graph regression: root -> wide -> INCOMPLETE deep + four healthy fillers; asserts BLOCKED, core INVALID, filler VALID, affected metrics, coverage 0.5, seven selected nodes, and ordered propagated findings.
- Cumulative diff: 6 files, 737 insertions, 1 deletion, within budget; rework-only files are dependency.py and the regression test.

### proof
- [x] AC #1: Registration validation and ledger behavior verified.
- [x] AC #2: Ordered complete recursive closure now uses deterministic dependency-before-dependent postorder.
- [x] AC #3: Deep gate-critical INCOMPLETE failure reaches every transitive dependent and blocks root.
- [x] AC #4: Noncritical degradation remains visible without invalidating unaffected metrics.
- [x] AC #5: Time-bound selection and exact-hash binding remain intact.
- [x] AC #6: Quarantine remains append-only with original bytes/history preserved.
- [x] AC #7: MODELED evidence remains ineligible for observed-outcome rules.
- [x] AC #8: Malformed/cyclic graphs remain fail-closed without partial selection.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (REWORK DELIVERED)

PROOF:

### Rework Fix
- Rejection cause: recursive propagation used child-edge count as an ordering heuristic, which is not topological for wide/multi-level DAGs.
- Fix: `_materialize` now emits the deterministic DFS postorder after all dependencies of a node have been visited; `evaluate_dependencies` propagates recursive health in that order. Cyclic returns remain `GRAPH_MALFORMED`.
- Regression: `test_wide_graph_propagates_deep_gate_critical_failure_to_root` registers a real root -> wide -> [INCOMPLETE deep + four healthy fillers] graph in temporary storage with no mocks. It asserts root `BLOCKED`, `core.metric=INVALID`, `filler.metric=VALID`, affected metric exposure, coverage 0.5, all seven selected descriptors, and propagated findings at deep/wide/root.

### CI/Test Results
- Commands run:
  - `uv run pytest tests/`
  - `uv run --with pytest-cov pytest tests/ --cov=gauntlet --cov-report=term-missing`
  - `pvg verify .gitignore src/gauntlet/data/__init__.py src/gauntlet/data/descriptors.py src/gauntlet/data/dependency.py src/gauntlet/data/quarantine.py tests/integrity/test_dependency_graph.py --include-tests --format=text`
- Summary: full suite PASS — 21 tests, 21 passed, 0 failed, 0 skipped, 0 warnings.
- Coverage: 88% total (1088 statements, 129 missed); dependency module 93%.
- Key output:
  - `collected 21 items`
  - `tests/integrity/test_dependency_graph.py .......... [ 76%]`
  - `21 passed in 0.37s`
  - `TOTAL ... 88%`
  - `VERIFY: PASSED (5 files scanned, 0 issues)`

### Commit
- Branch: `story/VK-kmbs`
- Amended delivery SHA: `046ad04ec031f5a8846d3a728ce37b2f6fa1e711`
- Rejected predecessor: `43dd14eeef18443f3ca5314c4c721b62496a20d6`
- Cumulative diff budget versus `epic/VK-egll`: 737 insertions, 1 deletion.

### AC Verification
| AC # | Requirement | Rework Status | Evidence |
|------|-------------|---------------|----------|
| 1 | Registration validates schema, hashes, content, and dependencies before ledger append | PASS | Existing registration test remains green |
| 2 | Complete ordered recursive closure returns graph hash, metrics, and coverage | PASS | DFS postorder propagation plus wide real-graph regression |
| 3 | Gate-critical INCOMPLETE transitive dependency invalidates dependent metrics and blocks root | PASS | `core.metric=INVALID`, root `BLOCKED`, coverage 0.5 |
| 4 | Noncritical gaps degrade coverage without invalidating unaffected metrics | PASS | Existing noncritical test remains green |
| 5 | Time travel and exact-hash binding remain intact | PASS | Existing quarantine/time-travel test remains green |
| 6 | Quarantine remains append-only with immutable originals | PASS | Existing original-byte/history assertions remain green |
| 7 | MODELED evidence remains ineligible for observed rules | PASS | Existing MODELED case remains green |
| 8 | Malformed/cyclic graph returns GRAPH_MALFORMED without partial selection | PASS | Existing malformed test; cycle path preserved by postorder materializer |

LEARNINGS:
- Child-count sorting is not a topological sort: in wide DAGs, a parent can be processed before all descendants have propagated failure.
- Deterministic DFS postorder is produced from sorted roots and registered dependency order, preserving reproducible graph evaluation while guaranteeing dependencies precede dependents.
- The rework regression keeps a healthy parallel metric valid, exposing both propagation and coverage semantics rather than only a global blocked flag.

## nd_contract
status: delivered

### evidence
- Branch `story/VK-kmbs`, amended commit `046ad04ec031f5a8846d3a728ce37b2f6fa1e711`.
- `uv run pytest tests/`: 21 passed, 0 failed, 0 skipped.
- Coverage: 88% total; dependency module 93%.
- `pvg verify ... --include-tests --format=text`: PASSED, 0 issues.
- Cumulative diff: 737 insertions + 1 deletion.

### proof
- [x] AC #1: Registration validation and ledger behavior remain correct.
- [x] AC #2: Recursive closure now uses deterministic postorder and handles the rejected wide shape.
- [x] AC #3: Deep gate-critical INCOMPLETE failure propagates through wide to root and marks `core.metric` INVALID/BLOCKED.
- [x] AC #4: Noncritical degradation remains visible without invalidating unaffected metrics.
- [x] AC #5: Time travel and exact hash binding remain correct.
- [x] AC #6: Append-only quarantine behavior remains correct.
- [x] AC #7: MODELED evidence remains fail-closed for observed rules.
- [x] AC #8: Malformed/cyclic graph handling remains fail-closed.

## nd_contract
status: in_progress

### evidence
- Rework claimed: 2026-09-18
- Base commit: 43dd14eeef18443f3ca5314c4c721b62496a20d6

### proof
- [ ] Fix deterministic transitive dependency propagation and add PM-shaped regression.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-18.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Branch: `story/VK-kmbs`
- Commit: `43dd14eeef18443f3ca5314c4c721b62496a20d6`
- `uv run pytest tests/`: 20 passed, 0 failed, 0 skipped.
- Coverage: 88% total; new data modules 89%/93%/91%.
- `pvg verify ... --include-tests --format=text`: PASSED, 0 issues.
- Full evidence and AC table are in the preceding `Implementation Evidence (DELIVERED)` block.

### proof
- [x] AC #1: Registration validates schema, canonical hash, content hash, and dependency references before ledger append.
- [x] AC #2: Ordered seven-check closure returns graph hash, affected metrics, and coverage.
- [x] AC #3: Gate-critical failures mark dependent metrics INVALID and return BLOCKED.
- [x] AC #4: Noncritical gaps visibly reduce coverage without invalidating unaffected metrics.
- [x] AC #5: Time-bound selection and exact manifest hash binding both hold.
- [x] AC #6: Quarantine is append-only and preserves original bytes/history.
- [x] AC #7: MODELED evidence cannot satisfy observed-outcome rules.
- [x] AC #8: Malformed graph data returns GRAPH_MALFORMED without partial selection.

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
  - `uv run pytest tests/`
  - `uv run --with pytest-cov pytest tests/ --cov=gauntlet --cov-report=term-missing`
  - `pvg verify .gitignore src/gauntlet/data/__init__.py src/gauntlet/data/descriptors.py src/gauntlet/data/dependency.py src/gauntlet/data/quarantine.py tests/integrity/test_dependency_graph.py --include-tests --format=text`
- Summary: full suite PASS — 20 tests, 20 passed, 0 failed, 0 skipped, 0 warnings.
- Coverage: 88% total (1086 statements, 129 missed); new data modules: descriptors 89%, dependency 93%, quarantine 91%.
- Key output:
  - `collected 20 items`
  - `tests/integrity/test_dependency_graph.py ......... [ 75%]`
  - `20 passed in 0.46s`
  - `TOTAL ... 88%`
  - `VERIFY: PASSED (5 files scanned, 0 issues)`
- Integration proof: temporary real storage plus verified trial ledger; no test mocks. Coverage includes multilevel closure, historical/later `as_of`, exact-hash binding, append-only quarantine, fail-closed critical gaps, noncritical degradation, MODELED rejection, and malformed graph handling.

### Commit
- Branch: `story/VK-kmbs`
- SHA: `43dd14eeef18443f3ca5314c4c721b62496a20d6`
- Diff budget: 6 files, 747 insertions, 1 deletion (748 changed lines).

### pvg verify
- `VERIFY: PASSED (5 files scanned, 0 issues)`

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|------|-------------|---------------|---------------|--------|
| 1 | Complete schema, canonical descriptor hash, content hash, and dependency references validated before ledger append | `src/gauntlet/data/descriptors.py` (`validate_descriptor`, `_register`) | `tests/integrity/test_dependency_graph.py::test_registration_validates_schema_hashes_dependencies_and_ledgers_once` | PASS |
| 2 | Seven checks evaluated in declared order; graph hash, affected metrics, and coverage returned | `src/gauntlet/data/dependency.py` (`CHECK_ORDER`, `evaluate_dependencies`) | `test_real_multilevel_closure_time_travel_and_append_only_quarantine`, `test_noncritical_gap_degrades_coverage_without_invalidating_unaffected_metrics` | PASS |
| 3 | Gate-critical missing/stale/corrupt/incomplete/replay-failed/UNKNOWN inputs mark metrics INVALID and result BLOCKED | `src/gauntlet/data/dependency.py` (`_local_findings`, dependency propagation, `evaluate_dependencies`) | parameterized `test_gate_critical_failures_block_dependent_metric`; missing and corrupt tests | PASS |
| 4 | Noncritical gap leaves unaffected metrics valid and visibly reduces coverage | `src/gauntlet/data/dependency.py` (`evaluate_dependencies`) | `test_noncritical_gap_degrades_coverage_without_invalidating_unaffected_metrics` | PASS |
| 5 | Active version selected by effective/superseded time; exact manifest hash retained | `src/gauntlet/data/dependency.py` (`_active_by_id`, `_materialize`) | multilevel time-travel and exact-root-hash assertions in integration test | PASS |
| 6 | Quarantine creates immutable superseding version referencing original; original bytes/history unchanged | `src/gauntlet/data/quarantine.py`; append-only storage/ledger in `descriptors.py` | `test_real_multilevel_closure_time_travel_and_append_only_quarantine` | PASS |
| 7 | MODELED evidence cannot satisfy observed-outcome metric rules | `src/gauntlet/data/dependency.py` (`OBSERVATION_BASIS_ELIGIBILITY`) | parameterized MODELED case | PASS |
| 8 | Malformed or cyclic graph returns `GRAPH_MALFORMED` without crash or partial selection | `src/gauntlet/data/dependency.py` (`_materialize`, `_malformed`) | `test_corrupt_or_malformed_registry_fails_closed_without_crashing` | PASS |

LEARNINGS:
- Registering the resolved dependency hashes in the trial payload preserves derived lineage while still allowing a later active version to expose quarantine health at evaluation time.
- The unanchored `data/` ignore pattern silently excluded the required `src/gauntlet/data/` package; anchoring it to `/data/` was necessary for the story artifacts.
- Rebuilding the descriptor registry from the verified trial ledger avoids a second mutable index while keeping content and descriptor files independently verifiable.

### OBSERVATIONS (unrelated)
- [CONCERN] Repository has no `docs/findings/` directory at this story HEAD.

### DISCOVERED_BUG
  title: pvg notes search references unavailable Claude vault
  context: Session-start knowledge search ran `pvg notes search "VK-kmbs descriptor dependency quarantine"` and exited 1 with `vault "Claude" not found. Available: .vault, nd-vault, Obsidian Vault, Brand OS (AI Video Factory), vault`. A direct search of the shared nd vault returned no relevant notes. This did not affect code delivery but blocks the configured knowledge-search path.
  affected_files: project/global pvg notes adapter configuration
  discovered_during: VK-kmbs

## nd_contract
status: delivered

### evidence
- Branch `story/VK-kmbs`, commit `43dd14eeef18443f3ca5314c4c721b62496a20d6`.
- `uv run pytest tests/` — 20 passed, 0 failed, 0 skipped.
- Coverage command — 88% total; new modules 89%/93%/91%.
- `pvg verify ... --include-tests --format=text` — PASSED, 0 issues.
- Diff budget — 747 insertions + 1 deletion, under the 750 changed-line ceiling.

### proof
- [x] AC #1: Registration validates schema, canonical hash, content hash, and dependency references before appending the trial ledger record.
- [x] AC #2: Dependency closure returns ordered seven-check results, graph hash, affected metrics, and coverage.
- [x] AC #3: Gate-critical failures mark dependent metrics INVALID and return BLOCKED.
- [x] AC #4: Noncritical gaps degrade coverage without invalidating unaffected metrics.
- [x] AC #5: Time-bound selection and exact manifest hash binding both hold across quarantine.
- [x] AC #6: Quarantine is append-only and preserves original descriptor/content bytes and historical resolution.
- [x] AC #7: MODELED evidence is rejected for observed-outcome metric rules.
- [x] AC #8: Malformed graph data returns GRAPH_MALFORMED without partial selection.

## nd_contract
status: in_progress

### evidence
- Claimed: 2026-09-18
- Worktree: story/VK-kmbs at 66555f6061d9aa371b9a4ba45d946498e83e37a0

### proof
- [ ] (pending)

## History
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-1vhm
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:16Z dep_added: blocks VK-jkkn
- 2026-09-18T23:31:17Z dep_added: blocks VK-pg9j
- 2026-09-18T23:31:19Z dep_added: blocks VK-mfn6
- 2026-09-18T23:31:22Z dep_added: blocks VK-0pfo
- 2026-09-18T23:31:23Z dep_added: blocks VK-0c4c
- 2026-09-18T23:31:29Z dep_added: blocks VK-2e0k
- 2026-09-18T23:31:38Z dep_added: blocks VK-3f9f
- 2026-09-19T01:37:42Z dep_added: blocks VK-4qfy
- 2026-09-19T01:37:42Z dep_added: blocks VK-3v14
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q
- 2026-09-19T03:19:17Z status: open -> in_progress
- 2026-09-19T03:19:17Z auto-follows: linked to predecessor VK-1vhm
- 2026-09-19T03:19:17Z auto-follows: linked to predecessor VK-wa2q
- 2026-09-19T03:19:17Z claimed by dev-VK-kmbs
- 2026-09-19T03:56:00Z status: in_progress -> in_progress
- 2026-09-19T04:01:30Z status: in_progress -> open
- 2026-09-19T04:01:30Z released by speed
- 2026-09-19T04:03:20Z status: open -> in_progress
- 2026-09-19T04:03:20Z claimed by dev-VK-kmbs
- 2026-09-19T04:08:52Z status: in_progress -> in_progress
- 2026-09-19T04:11:59Z status: in_progress -> closed
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-jkkn
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-pg9j
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-mfn6
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-0pfo
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-0c4c
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-2e0k
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-3f9f
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-4qfy
- 2026-09-19T04:11:59Z dep_removed: no_longer_blocks VK-3v14

## Links
- Parent: [[VK-egll]]
- Was blocked by: [[VK-1vhm]], [[VK-wa2q]]
- Follows: [[VK-1vhm]], [[VK-wa2q]]
- Led to: [[VK-jkkn]], [[VK-0c4c]], [[VK-mfn6]], [[VK-pg9j]]

## Comments

### 2026-09-18T23:33:03Z speed
RECOMMEND hard-tdd: time-bound descriptor selection and recursive fail-closed behavior are state-machine/security-critical. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: time-bound descriptor selection and recursive fail-closed behavior are state-machine/security-critical. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-19T04:01:30Z speed
## PM Decision
REJECTED [$(date +%Y-%m-%d)]:
EXPECTED: AC #2 requires complete recursive dependency closure, and AC #3 requires a gate-critical incomplete input to mark every dependent metric INVALID and return BLOCKED.
DELIVERED: At commit 43dd14eeef18443f3ca5314c4c721b62496a20d6, src/gauntlet/data/dependency.py builds parent-to-child adjacency then processes nodes with `sorted(selected, key=lambda item: len(reverse.get(item, [])))`; child-edge count is not a topological order. A real temporary-storage probe registered root -> wide -> incomplete-deep plus healthy fillers and evaluated the root: `status=OK`, `metric_states={'core.metric': 'VALID'}`, and findings stopped at wide (`QUALITY_INCOMPLETE` propagated only from deep to wide), never reaching root.
GAP: Gate-critical recursive health is shape-dependent and can silently allow a transitive dependent to pass. This violates AC #2 (complete recursive closure) and AC #3 (critical incomplete input must block dependent metrics). The existing integration test only covers a narrow three-node chain and misses this case.
FIX: Materialize the DAG and perform deterministic postorder/topological recursive-health propagation (or iterate to a fixpoint). Add a no-mock wide/multi-level graph test that makes a deep gate-critical descriptor INCOMPLETE and asserts every transitive dependent metric is INVALID, root status is BLOCKED, affected metrics and coverage expose the failure, and ordered findings remain stable.
## nd_contract
status: rejected

### evidence
- PM full suite at delivered commit: `uv run pytest tests/` -> 20 passed in 0.30s.
- PM static verification: `pvg verify ... --include-tests --format=text` -> PASSED, 5 files, 0 issues.
- PM targeted no-mock temporary-storage graph probe reproduced failure: root status OK / core.metric VALID despite a transitive gate-critical INCOMPLETE dependency.
- Diff inspected at 43dd14eeef18443f3ca5314c4c721b62496a20d6: 6 files, 747 insertions, 1 deletion, within budget.

### proof
- [ ] AC #2: Recursive dependency closure is incomplete for non-chain DAG shapes.
- [ ] AC #3: A gate-critical INCOMPLETE transitive dependency failed to mark the dependent root metric INVALID or return BLOCKED.

### 2026-09-19T04:02:05Z speed
PM CORRECTION 2026-09-18: The prior rejection header's literal $(date +%Y-%m-%d) was a shell-quoting artifact. The intended header is REJECTED [2026-09-18]. The rejection verdict, criteria, evidence, and required fix are unchanged.
