---
id: VK-0c4c
title: "Enforce walk-forward evaluation discipline"
status: closed
priority: 1
type: feature
labels: [integration, phase-1, walking-skeleton, delivered]
parent: VK-0auj
created_at: 2026-09-18T23:31:22Z
created_by: speed
updated_at: 2026-09-19T05:50:41Z
content_hash: "sha256:b79fe0aaee68d0884b685991d94d6b05bd09a24cf9aafdb6a9a326f9e8961985"
was_blocked_by: [VK-pg9j, VK-kmbs, VK-jkkn]
follows: [VK-kmbs, VK-jkkn]
assignee: dev-VK-0c4c
closed_at: 2026-09-19T05:50:41Z
close_reason: "Accepted: strict target-horizon and target-bar validation now applies to every BUY and FLAT prediction; the prior absent-target adversary returns BLOCKED with no imputed label."
---

## Description
## USER INTENT
The owner needs selection separated from untouched evaluation so a candidate cannot be graded on data that chose it.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement walk-forward evaluation with train before validation, selection on validation, locked variant, and test only the following window; enter at the next bar. Inputs are frozen `solana.bars` and `solana.events` descriptors, candidate/model profile, split policy, and feature provenance. Emit `fold_manifest.json`, train/validation/test membership, locked selection, row-level test predictions and trades, and a run report. A sample may train or tune only when feature observation and target completion precede the boundary. Embargo/purge gaps, fold order, expanding-window policy, and selection locks are explicit. Factory race output remains exploratory until the selected fingerprint is locked.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Exact reserve pricing: sibling exact-execution story.
- Statistical panels: lab stories.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 750 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
- src/gauntlet/judge/splits.py -> build_split_manifest(policy: SplitPolicy, population: FrozenPopulation) -> SplitManifest

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-kmbs: src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
  spec: evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation

### Acceptance Criteria (story contract)
1. Fold manifest records UTC boundaries, bars, horizon, lookback, normalization window, target horizon, embargo/purge, fold order, and selection locks.
2. Validation selects one variant and the following test window is untouched by that selection.
3. A target crossing a boundary, future normalization, or post-outcome membership mutation fails.
4. Locked candidate fingerprint, feature provenance, config hash, source descriptor hashes, and selected fold are recorded.
5. Row-level predictions and trades include timestamps, venue, token, intended action, labels, and OBSERVED/MODELED basis.
6. Entering at the next bar is enforced and any gap or missing dependency yields BLOCKED, not an imputed fill.
7. A factory race can enter only after its selected fingerprint is locked; ranking score is not judge evidence.

## Testing Requirements
- Unit: Test split generation, boundary crossing, fold locks, entry timing, and row schema.
- Integration tests: MANDATORY (no mocks). Evaluate a real synthetic multi-fold population from registered descriptors and verify locked selections, untouched test membership, and complete row-level replay inputs.
- Commands to run: `uv run pytest tests/judge/test_walk_forward.py`.

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
- [ ] AC #1: Fold manifest records UTC boundaries, bars, horizon, lookback, normalization window, target horizon, embargo/purge, fold order, and selection locks.
- [ ] AC #2: Validation selects one variant and the following test window is untouched by that selection.
- [ ] AC #3: A target crossing a boundary, future normalization, or post-outcome membership mutation fails.
- [ ] AC #4: Locked candidate fingerprint, feature provenance, config hash, source descriptor hashes, and selected fold are recorded.
- [ ] AC #5: Row-level predictions and trades include timestamps, venue, token, intended action, labels, and OBSERVED/MODELED basis.
- [ ] AC #6: Entering at the next bar is enforced and any gap or missing dependency yields BLOCKED, not an imputed fill.
- [ ] AC #7: A factory race can enter only after its selected fingerprint is locked; ranking score is not judge evidence.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: remove collector inversion from judge walking skeleton

GENERAL RULE SWEEP: No early-priority walking skeleton may be blocked by a lower-priority collector; collectors feed later real-data integration.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:
- src/gauntlet/judge/synthetic.py -> build_synthetic_population(seed: int, policy: SplitPolicy) -> FrozenPopulation

CONSUMES:
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-kmbs: src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
  spec: evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation

### Acceptance Criteria (repair revision)
1. The P1 walking skeleton generates and registers a deterministic synthetic solana_dex bars/events population locally; it has no Bitquery dependency and makes no network call.
2. Synthetic data is clearly labeled synthetic fixture evidence for wiring and is not promotable venue evidence.
3. Collector-derived descriptors bind only in later integration stories after the collector epic.
## nd_contract
status: delivered

### evidence
- Fix commit: `4242e830dcb426a07b305d200091b3a09da142ab` on `story/VK-0c4c`.
- `uv run pytest tests/judge/test_walk_forward.py` -> 5 passed.
- `uv run pytest tests/` -> 48 passed.
- `pvg verify src/gauntlet/judge/__init__.py src/gauntlet/judge/splits.py src/gauntlet/judge/synthetic.py src/gauntlet/judge/walk_forward.py tests/judge/test_walk_forward.py --format=text` -> PASSED, 5 files, 0 issues.
- `pvg story deliver VK-0c4c` -> OK using shared nd vault.

### proof
- [x] PM rejection resolved: exact target bars are required for BUY and FLAT; absent target timestamps produce BLOCKED with no label.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Rework Implementation Evidence (DELIVERED)

PROOF:

### Rejection Resolution
- Strict split membership now requires a bar to exist at every declared target completion timestamp and requires that timestamp to equal `signal + target_horizon * bar_interval`.
- Walk-forward evaluation now resolves and validates the exact target bar for EVERY prediction before constructing a label, prediction, or trade; the check no longer depends on BUY versus FLAT.
- Public evaluation converts the strict target-gap rejection into a machine-readable `BLOCKED` run with empty predictions/trades and writes the corresponding immutable blocked artifacts/event.
- Added a real, no-mock regression that registers a malformed synthetic bars descriptor declaring `2026-01-01T00:23:30Z` between real one-minute bars, supplies only the FLAT variant, proves `build_split_manifest` rejects `TARGET_BAR_MISSING`, and proves `evaluate_walk_forward` returns `BLOCKED` with no label or prediction.

### CI/Test Results
- Commands run:
  - `uv run pytest tests/judge/test_walk_forward.py`
  - `uv run pytest tests/`
  - `pvg verify src/gauntlet/judge/__init__.py src/gauntlet/judge/splits.py src/gauntlet/judge/synthetic.py src/gauntlet/judge/walk_forward.py tests/judge/test_walk_forward.py --format=text`
- Summary: judge integration PASS (5/5); full suite PASS (48/48); pvg verify PASS (5 files, 0 issues).
- Coverage: rejection-fix regression PASS; AC contract coverage remains 100% (10/10 original-plus-repair criteria). Line coverage is not configured in this dependency-free Phase 1 project.
- Key output:
  - `collected 5 items ... 5 passed in 0.22s`
  - `collected 48 items ... 48 passed in 0.59s`
  - `VERIFY: PASSED (5 files scanned, 0 issues)`

### Commit
- Branch: `story/VK-0c4c`
- Fix SHA: `4242e830dcb426a07b305d200091b3a09da142ab`
- Original rejected SHA: `7cd18956dc362f664b379555e4d76adf751693e8`
- Final story diff versus `epic/VK-0auj`: 5 files, 747 insertions (within under-750 LOC budget).

### pvg verify
- `VERIFY: PASSED (5 files scanned, 0 issues)`

### AC Verification After Rework
| AC # | Requirement | Rework Status | Evidence |
|---|---|---|---|
| 1 | Complete fold temporal metadata and locks | PASS | Existing split schema test plus strict target validation |
| 2 | Validation-only selection before untouched test | PASS | Existing real multi-fold integration test |
| 3 | Leakage/mutation failures | PASS | Existing target-boundary, future-normalization, and mutation tests |
| 4 | Locked provenance identities | PASS | Existing run-report assertions |
| 5 | Row labels use real declared target evidence | PASS | New FLAT absent-target regression emits no label/prediction |
| 6 | Exact next bar and every target gap BLOCK | PASS | Target validation is unconditional; regression returns `TARGET_BAR_MISSING` |
| 7 | Factory ranking not judge evidence | PASS | Existing factory ranking assertions |
| Repair 1 | Local deterministic registered synthetic population | PASS | Existing registration/determinism test |
| Repair 2 | Synthetic evidence not promotable | PASS | Existing fixture-label assertions |
| Repair 3 | No collector binding | PASS | Existing source/AST assertions |

LEARNINGS:
- The original implementation correctly guarded BUY outcomes but incorrectly treated FLAT labels as harmless; every emitted row must satisfy the same outcome-existence contract.
- Checking only the declared completion boundary allowed a timestamp to masquerade as evidence; exact horizon arithmetic plus target-row existence closes that gap.
- Turning a strict data-gap rejection into a typed BLOCKED run preserves machine-readable artifacts/events without imputing an outcome.
- The first delivery's 47 passing tests were insufficient because they validated BUY execution gaps but omitted a FLAT target-gap adversary; the new registered-descriptor regression now pins that case.

## nd_contract
status: delivered

### evidence
- Fix commit: `4242e830dcb426a07b305d200091b3a09da142ab` on `story/VK-0c4c`.
- `uv run pytest tests/judge/test_walk_forward.py` -> 5 passed.
- `uv run pytest tests/` -> 48 passed.
- `pvg verify ... --format=text` -> PASSED, 5 files, 0 issues.
- Regression: registered absent target timestamp + FLAT variant -> `TARGET_BAR_MISSING`, run status BLOCKED, empty predictions/trades, no imputed label.

### proof
- [x] AC #1: Fold manifest temporal metadata and selection locks remain complete.
- [x] AC #2: Validation-only selection and untouched test discipline remain verified.
- [x] AC #3: Target-boundary, future-normalization, and mutation attacks fail.
- [x] AC #4: Locked candidate/provenance/config/source/fold identities remain recorded.
- [x] AC #5: Labels are emitted only from an exact existing target bar, including FLAT predictions.
- [x] AC #6: Next-bar and target gaps return BLOCKED without imputed fills.
- [x] AC #7: Factory ranking remains exploratory and score-free judge evidence.
- [x] Repair AC #1: Deterministic local synthetic population remains registered without network/Bitquery.
- [x] Repair AC #2: Synthetic fixture remains non-promotable.
- [x] Repair AC #3: No collector-derived binding was introduced.

## nd_contract
status: in_progress

### evidence
- Rework claimed: 2026-09-19; rejection target is exact target-bar existence for every BUY/FLAT prediction.

### proof
- [ ] (pending rework)

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-19.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Commit: `7cd18956dc362f664b379555e4d76adf751693e8` (`story/VK-0c4c`).
- `uv run pytest tests/judge/test_walk_forward.py` -> 4 passed.
- `uv run pytest tests/` -> 47 passed.
- `pvg verify src/gauntlet/judge/__init__.py src/gauntlet/judge/splits.py src/gauntlet/judge/synthetic.py src/gauntlet/judge/walk_forward.py tests/judge/test_walk_forward.py --format=text` -> PASSED, 5 files, 0 issues.
- `pvg story deliver VK-0c4c` -> OK using shared nd vault.

### proof
- [x] AC #1: Complete fold manifest temporal metadata and selection locks verified.
- [x] AC #2: Validation-only selection and untouched following test membership verified.
- [x] AC #3: Boundary-crossing target, future normalization, and mutation rejections verified.
- [x] AC #4: Candidate/provenance/config/source/fold identity recorded.
- [x] AC #5: Row-level prediction/trade labels, timestamps, venue/token/action, and basis verified.
- [x] AC #6: Exact next-bar entry and BLOCKED gap/dependency policy verified.
- [x] AC #7: Factory race remains exploratory until fingerprint lock; ranking score excluded.
- [x] Repair AC #1: Deterministic registered local synthetic population with no network/Bitquery verified.
- [x] Repair AC #2: Synthetic fixture remains non-promotable venue evidence.
- [x] Repair AC #3: No collector-derived descriptor binding introduced.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `uv run pytest tests/judge/test_walk_forward.py`
  - `uv run pytest tests/`
  - `pvg verify src/gauntlet/judge/__init__.py src/gauntlet/judge/splits.py src/gauntlet/judge/synthetic.py src/gauntlet/judge/walk_forward.py tests/judge/test_walk_forward.py --format=text`
- Summary: judge integration PASS (4/4); full suite PASS (47/47); pvg verify PASS (5 files, 0 issues).
- Coverage: AC contract coverage 100% (10/10 original-plus-repair criteria). Line coverage was not collected because this Phase 1 project has no configured coverage tool or dependency.
- Key output:
  - `collected 4 items ... 4 passed in 0.14s`
  - `collected 47 items ... 47 passed in 0.61s`
  - `VERIFY: PASSED (5 files scanned, 0 issues)`

### Commit
- Branch: `story/VK-0c4c`
- SHA: `7cd18956dc362f664b379555e4d76adf751693e8`
- Diff budget: 5 files changed, 749 insertions (story limit: ~8 files, under 750 changed LOC).

### Wiring
- `src/gauntlet/judge/synthetic.py:129` registers immutable synthetic bars/events descriptors through the existing descriptor registry and emits no network/Bitquery call.
- `src/gauntlet/judge/splits.py:111` builds canonical strict train/validation/test memberships and pending selection locks.
- `src/gauntlet/judge/walk_forward.py:271` evaluates dependency state, selects only on validation, locks the selected fingerprint, executes next-bar test entries, writes immutable run artifacts, and appends a hash-chained event.
- Real resolver wiring is exercised by `tests/judge/test_walk_forward.py:25` through `resolve_config`; no config logic was duplicated.

### pvg verify
- `VERIFY: PASSED (5 files scanned, 0 issues)`

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | UTC boundaries, bars, horizon, lookback, normalization, target horizon, embargo/purge, fold order, selection locks | `src/gauntlet/judge/splits.py` | `tests/judge/test_walk_forward.py::test_split_manifest_records_strict_boundaries_labels_and_locks` | PASS |
| 2 | Validation selects one variant and following test window is untouched | `src/gauntlet/judge/walk_forward.py::_select` and `evaluate_walk_forward` | `test_real_multi_fold_evaluation_selects_on_validation_and_replays_rows` | PASS |
| 3 | Boundary-crossing targets, future normalization, and post-outcome mutation fail | `src/gauntlet/judge/splits.py::_membership`; `walk_forward.py::_provenance` and `_validate_request` | `test_split_manifest...` and `test_fail_closed_rejections...` | PASS |
| 4 | Locked fingerprint, provenance, config hash, source hashes, selected fold recorded | `walk_forward.py::evaluate_walk_forward` | `test_real_multi_fold...` | PASS |
| 5 | Row predictions/trades carry timestamps, venue, token, action, labels, and MODELED basis | `walk_forward.py::Prediction` and `Trade` | `test_real_multi_fold...` | PASS |
| 6 | Next-bar entry and gaps/missing dependencies BLOCK without fills | `walk_forward.py::_evaluate_fold` and `_dependency` | `test_real_multi_fold...` and `test_fail_closed...` | PASS |
| 7 | Factory output remains exploratory until selected fingerprint lock; ranking score is not judge evidence | `walk_forward.py::FactoryRankingEntry` and run report | `test_real_multi_fold...` | PASS |
| Repair 1 | Deterministic local synthetic solana_dex bars/events population, no network/Bitquery | `synthetic.py::build_synthetic_population` | `test_synthetic_population_is_deterministic_registered_and_local` | PASS |
| Repair 2 | Fixture labeled synthetic and not promotable venue evidence | `synthetic.py::BarRow`, `EventRow`, `FrozenPopulation` | `test_synthetic_population...` | PASS |
| Repair 3 | Collector-derived descriptors do not bind in this skeleton | Judge dependency roots are only synthetic descriptors; no collector import | AST/source assertion in `test_synthetic_population...` | PASS |

LEARNINGS:
- Rebuilding the expected split manifest inside evaluation is an inexpensive strong invariant for detecting post-outcome membership tampering.
- Completion-aware boundaries (signal cutoff plus target-horizon cushion) make label leakage explicit instead of silently dropping incomplete final rows.
- Population-specific synthetic artifact IDs allow different seeds to coexist as independent immutable version-1 descriptors in one local registry.

### OBSERVATIONS (unrelated)
- None.

## nd_contract
status: delivered

### evidence
- Commit: `7cd18956dc362f664b379555e4d76adf751693e8` on `story/VK-0c4c`.
- Tests: `uv run pytest tests/judge/test_walk_forward.py` -> 4 passed; `uv run pytest tests/` -> 47 passed.
- Verification: `pvg verify ... --format=text` -> PASSED, 5 files, 0 issues.
- Immutable wiring: synthetic descriptor trials, write-once run files, and one hash-chained `gate.evaluate` event are verified by the real integration test.

### proof
- [x] AC #1: Fold manifest records every declared temporal and selection-lock field.
- [x] AC #2: Validation-only selection locks one variant before the untouched following test window.
- [x] AC #3: Target-boundary, future-normalization, and population/split mutation attacks fail closed.
- [x] AC #4: Candidate, feature, config, source-descriptor, and selected-fold provenance is recorded.
- [x] AC #5: Complete row-level prediction/trade replay fields include labels and MODELED basis.
- [x] AC #6: Entries require the exact next bar; gaps/missing dependencies return BLOCKED without imputation.
- [x] AC #7: Factory ranking remains exploratory and its score is excluded from judge evidence.
- [x] Repair AC #1: Deterministic synthetic population is generated and registered locally with no network or Bitquery dependency.
- [x] Repair AC #2: Synthetic fixture is explicitly non-promotable venue evidence.
- [x] Repair AC #3: No collector-derived descriptor is bound by this walking skeleton.

## nd_contract
status: in_progress

### evidence
- Claimed: 2026-09-19

### proof
- [ ] (pending)

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The P1 walking skeleton generates and registers a deterministic synthetic solana_dex bars/events population locally; it has no Bitquery dependency and makes no network call.
- [ ] Repair AC #2: Synthetic data is clearly labeled synthetic fixture evidence for wiring and is not promotable venue evidence.
- [ ] Repair AC #3: Collector-derived descriptors bind only in later integration stories after the collector epic.


## History
- 2026-09-18T23:31:22Z dep_added: blocked_by VK-pg9j
- 2026-09-18T23:31:23Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:23Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:23Z dep_added: blocks VK-2g0f
- 2026-09-18T23:31:24Z dep_added: blocks VK-ddoh
- 2026-09-18T23:31:25Z dep_added: blocks VK-sbdy
- 2026-09-18T23:31:27Z dep_added: blocks VK-aumt
- 2026-09-18T23:31:36Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:42Z dep_added: blocks VK-vqvy
- 2026-09-19T01:37:43Z dep_removed: was_blocked_by VK-pg9j
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs
- 2026-09-19T04:41:26Z dep_removed: was_blocked_by VK-jkkn
- 2026-09-19T05:04:39Z status: open -> in_progress
- 2026-09-19T05:04:39Z auto-follows: linked to predecessor VK-kmbs
- 2026-09-19T05:04:39Z auto-follows: linked to predecessor VK-jkkn
- 2026-09-19T05:04:39Z claimed by dev-VK-0c4c
- 2026-09-19T05:29:35Z status: in_progress -> in_progress
- 2026-09-19T05:37:41Z status: in_progress -> open
- 2026-09-19T05:37:41Z released by speed
- 2026-09-19T05:39:09Z status: open -> in_progress
- 2026-09-19T05:39:09Z claimed by dev-VK-0c4c
- 2026-09-19T05:46:18Z status: in_progress -> in_progress
- 2026-09-19T05:50:41Z status: in_progress -> closed
- 2026-09-19T05:50:41Z dep_removed: no_longer_blocks VK-2g0f
- 2026-09-19T05:50:41Z dep_removed: no_longer_blocks VK-ddoh
- 2026-09-19T05:50:41Z dep_removed: no_longer_blocks VK-sbdy
- 2026-09-19T05:50:41Z dep_removed: no_longer_blocks VK-aumt
- 2026-09-19T05:50:41Z dep_removed: no_longer_blocks VK-dblr
- 2026-09-19T05:50:41Z dep_removed: no_longer_blocks VK-vqvy

## Links
- Parent: [[VK-0auj]]
- Was blocked by: [[VK-pg9j]], [[VK-kmbs]], [[VK-jkkn]]
- Follows: [[VK-kmbs]], [[VK-jkkn]]

## Comments

### 2026-09-19T05:37:41Z speed
## PM Decision
REJECTED [2026-09-19]:

EXPECTED: AC #6 requires that entering at the next bar is enforced and that “any gap or missing dependency yields BLOCKED, not an imputed fill.” The strict split must also preserve the declared target window for every row.

DELIVERED: At commit 7cd18956dc362f664b379555e4d76adf751693e8, `src/gauntlet/judge/walk_forward.py:212-215` validates the target bar only when `intended != "FLAT"`; it then unconditionally reads `rows[exit_index]` as the outcome. `src/gauntlet/judge/splits.py:_membership` checks only that the declared completion precedes the segment boundary and does not require a bar at `signal + target_horizon * bar_interval`.

GAP: A registered synthetic-style bars descriptor can declare a target completion timestamp at which no bar exists (for example `bar-000023` at `2026-01-01T00:23:30Z` between one-minute bars). With the selected variant FLAT, public `evaluate_walk_forward` returns status `OK`, emits a prediction whose `label_completed_at_utc` names the absent timestamp, and computes its label from `2026-01-01T00:25:00Z` instead. This is an accepted target gap/imputed outcome and violates AC #6 (and undermines the row-label evidence required by AC #5). My adversarial public-API reproduction ended with: `FAIL accepted absent target timestamp 2026-01-01T00:23:30Z`; `FAIL label sourced from 2026-01-01T00:25:00Z not declared target`.

FIX: In the strict split contract, reject a row unless feature observation is available at/before signal, the target completion is exactly the declared UTC target horizon, and a bar exists at that completion timestamp. In evaluation, require the exact target bar for every prediction regardless of BUY/FLAT; return the existing machine-readable BLOCKED path before constructing a label, prediction, or trade. Add a no-mock regression test using a registered malformed synthetic-style population with an absent target timestamp and a FLAT selected variant.

Independent verification also passed: targeted judge suite 4/4, full suite 47/47, `pvg verify` 5 files/0 issues, diff 5 files/749 insertions, no collector/network wiring, and adversarial checks for `TARGET_CROSSES_BOUNDARY`, `FUTURE_FEATURE_REJECTED`, `POPULATION_MUTATED`, `SPLIT_MUTATED`, and `FUTURE_NORMALIZATION_REJECTED`.

DISCOVERED_BUG:
  title: Walk-forward accepts absent target timestamps for FLAT predictions
  context: A registered bars population can declare an impossible target completion timestamp between bars. `build_split_manifest` accepts it because it only checks the segment boundary, and `_evaluate_fold` skips exact target-bar validation when intended action is FLAT. Public evaluation returns OK and computes the label from the policy-horizon bar even though no row exists at the declared completion timestamp.
  affected_files: src/gauntlet/judge/splits.py; src/gauntlet/judge/walk_forward.py; tests/judge/test_walk_forward.py
  discovered_during: VK-0c4c

## nd_contract
status: rejected

### evidence
- Reviewed commit 7cd18956dc362f664b379555e4d76adf751693e8 and delivered proof.
- Re-ran `uv run pytest tests/judge/test_walk_forward.py -vv` -> 4 passed.
- Re-ran `uv run pytest tests/ -vv` -> 47 passed.
- Re-ran `pvg verify ... --format=text` -> PASSED, 5 files, 0 issues.
- Adversarial public API reproduction accepted an absent target timestamp and returned OK with an imputed outcome basis.

### proof
- [ ] AC #5: Row label evidence can name a target timestamp at which no bar exists.
- [ ] AC #6: A target gap is not BLOCKED when the selected action is FLAT.
