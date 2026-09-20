---
id: VK-tr7s
title: "E2e: compare four policy baselines on frozen evidence"
status: closed
priority: 1
type: task
parent: VK-1rbc
created_at: 2026-09-20T17:12:45Z
created_by: speed
updated_at: 2026-09-20T19:06:11Z
content_hash: "sha256:7edd32658850746dc70fcb85897cb73b644c06af15e2bd16926737239ff4414d"
labels: [e2e, capstone, walking-skeleton, delivered]
assignee: dev-VK-tr7s
follows: [VK-aej2]
closed_at: 2026-09-20T19:06:11Z
close_reason: "Accepted: independent local gates and required GitHub CI pass; all 11 AC verified."
---

## Description
## USER INTENT
The owner needs to know whether a confidence-gated Jev-style decision policy beats a simple hand rule, an un-gated model policy, and a generic LLM-layer policy after costs, abstention, slippage, and deterministic risk vetoes—not merely whether a model predicted individual outcomes.

## Context (Embedded)
Gauntlet already has immutable trial/event ledgers, evidence descriptors, deterministic policy precedence, paper-portfolio risk boundaries, and synthetic/prospective evaluation primitives. This story adds a policy-level benchmark that runs four declared arms over one frozen evidence snapshot. The first implementation is local and synthetic/modeled: no network inference, no external trading account, and no real-money order interface.

The four required arms are:
1. HAND_RULE: deterministic baseline without model confidence.
2. LLM_LAYER: generic recorded model decision without Jev-specific gating.
3. UNGATED_JEV: Jev-style confidence/output used at every opportunity.
4. GATED_JEV: confidence gate plus abstention/fallback plus deterministic risk veto.

## OUT OF SCOPE
- Live LLM/Jev/TypeSafe inference.
- Real-money orders or exchange integration.
- New market-data population or Bitquery capture.
- Replacing the deterministic gate engine.
- Changing the risk kernel semantics.

## DIFF BUDGET
- ~9 files, under 1,100 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/policy/benchmark.py -> PolicyArmSpec, PolicyBenchmarkConfig, PolicyArmMetrics, PolicyBenchmarkResult, run_policy_benchmark(frozen_rows, arms, config) -> PolicyBenchmarkResult
- src/gauntlet/policy/benchmark.py -> deterministic four-arm synthetic fixture constructors
- tests/policy/test_policy_benchmark.py -> exhaustive equal-input, metric, cost, veto, abstention, and immutability coverage
- tests/fixtures/policy/frozen-evidence-v1.json -> synthetic frozen evidence rows with explicit MODELED basis
- evidence/policy-benchmark/policy-benchmark-v1.json -> checked-in synthetic benchmark report

CONSUMES:
- (existing): src/gauntlet/contracts/canonical.py -> canonical_json(value) -> bytes, sha256_digest(data) -> str
- (existing): src/gauntlet/ledger/events.py -> append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
- (existing): src/gauntlet/risk/kernel.py -> evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult

## Acceptance Criteria
1. All four required arms execute over the exact same frozen row list and snapshot hash.
2. Every arm receives identical feature fields, cost policy, slippage policy, risk policy, and fallback action.
3. Report metrics include Sharpe ratio, Sortino ratio, max drawdown, hit rate, gross and net return, slippage cost, decision cost per million, total modeled cost, coverage, abstention rate, incorrect accepted decisions, risk vetoes, and fallback count.
4. Empty-set or zero-variance return cases report explicit null risk-adjusted metrics rather than fabricated infinities.
5. UNGATED_JEV has 100% model-decision coverage but may differ in accepted-action coverage because deterministic eligibility still applies.
6. GATED_JEV abstains or falls back below its confidence threshold.
7. A risk-veto boundary forces approved size/action to zero without changing any arm's raw decision evidence.
8. The report records every arm's input snapshot hash, policy hash, cost hash, risk hash, and MODELED observation basis.
9. Running the benchmark twice with the same inputs and seed produces byte-identical canonical JSON.
10. Mutating any policy arm, cost field, risk field, or frozen row changes the report identity.
11. No order-placement interface or real-money activation command is added.

## Testing Requirements
- Unit: metric formulas, zero-variance behavior, threshold gating, risk veto, fallback, cost/slippage arithmetic, report hashing.
- Integration: MUST run all four real synthetic arms locally over one frozen fixture with no mocks around benchmark orchestration.
- E2e: CLI or function entry point writes a canonical report and, when a data root is supplied, appends immutable trial/event evidence.
- Commands:
  - uv run --frozen --group dev pytest -q tests/policy/test_policy_benchmark.py
  - uv run --frozen --group dev pytest -q
  - pvg verify src/gauntlet/policy/benchmark.py --format=text
  - git diff --check

## MANDATORY SKILLS
None identified.

## nd_contract
status: new

### evidence
- Operator selected the four-baseline policy benchmark as the Gauntlet half of the cross-project calibrated-policy goal.

### proof
- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-09-20]: Independently reviewed the story-specific 1,092-line implementation and dependency boundary, reran 24 targeted tests, the full 74-test suite, scoped verifier, whitespace checks, canonical report regeneration, and parent-root risk I/O containment. The benchmark consumes the tracked VK-0pfo RiskPolicyVersion/RiskRequest/PaperPortfolio through evaluate_risk and preserves non-CONTINUE => HOLD/zero-size semantics. GitHub PR 1 CI passed at head 6e9688206963fa06f59eacccab07666c8439d8db with CLEAN merge state; story implementation commit remains 7da5aa47d9436a3a47a0143af629afcf30c97c59.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-20.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

- `uv run --frozen --group dev pytest -q tests/policy/test_policy_benchmark.py` — 24 passed.
- `uv run --frozen --group dev pytest -q` — 74 passed; printed BLOCKED lines are the existing intentional synthetic-policy fixture output.
- `pvg verify src/gauntlet/policy/benchmark.py --format=text` — PASSED, 1 file, 0 issues.
- `git diff --check` and `git diff --cached --check` — pass.

### CI/Test Results

- Targeted policy benchmark: 24/24 passed.
- Full suite: 74/74 passed.
- Scoped verifier: 0 issues.
- Whitespace checks: pass.
- Risk containment: four deliberate arm-level vetoes evaluated; parent GAUNTLET_DATA_ROOT file count 0.
- Canonical evidence: stored bytes exactly equal regenerated canonical bytes plus newline.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Four arms, exact same rows/hash | PASS | all arms share frozen snapshot hash `sha256:7c625211fd3adb6543c1d892910d9529393990e15481cf7202ff6037c03e76d0`. |
| 2. Identical shared inputs | PASS | common feature fields, configuration, combined cost hash, and tracked risk hash. |
| 3. Required metrics | PASS | coverage, abstention, gross/net return, slippage, decision and total cost, hit rate, Sharpe, Sortino, drawdown, incorrect accepts, vetoes, fallback. |
| 4. Empty/zero-variance nulls | PASS | explicit null risk-adjusted values; no infinities. |
| 5. UNGATED coverage semantics | PASS | 100% model decisions; deterministic eligibility/risk still change accepted coverage. |
| 6. GATED abstention/fallback | PASS | threshold behavior and one fallback covered. |
| 7. Hard risk veto | PASS | real tracked RiskPolicyVersion/RiskRequest/PaperPortfolio through evaluate_risk; non-CONTINUE => HOLD/size 0 and raw evidence preserved. |
| 8. Input/policy/cost/risk/basis hashes | PASS | top-level and per-arm identities include MODELED basis and required hashes. |
| 9. Deterministic canonical report | PASS | rerun byte/hash tests and checked-in artifact equality. |
| 10. Material mutations change identity | PASS | arm/cost/slippage/threshold/fallback/config/row mutations covered. |
| 11. No order/real-money interface | PASS | AST regression and implementation contain no order-placement API. |

Summary: added a deterministic four-arm calibrated-policy benchmark over frozen MODELED evidence, integrated the tracked paper-risk kernel without uncontrolled ledger writes, and emitted canonical auditable evidence.

Commit SHA: 7da5aa47d9436a3a47a0143af629afcf30c97c59

Dependency base: dispatcher cherry-picked accepted VK-0pfo commit 28ea5312d3fe797f55291856ffa61b5adaa936ea as 3769f6c before story implementation because VK-tr7s declares the risk kernel as a consumed dependency.

Story-specific changed-line budget: 1,092 intended lines (814 source + 276 tests + 1 fixture + 1 evidence), under the 1,100-line budget.

## nd_contract
status: delivered

### evidence
- Required targeted/full/verifier/whitespace outputs above.
- Commit `7da5aa47d9436a3a47a0143af629afcf30c97c59`.
- Dependency base `3769f6c`.

### proof
- [x] AC #1: Four required arms consume the same frozen list and snapshot hash.
- [x] AC #2: Features, costs, slippage, risk, and fallback are shared identically.
- [x] AC #3: All required policy-level metrics are reported.
- [x] AC #4: Empty/zero-variance risk-adjusted metrics use explicit nulls.
- [x] AC #5: Ungated model coverage and deterministic accepted coverage are separated.
- [x] AC #6: Gated Jev abstains/falls back below threshold.
- [x] AC #7: Real risk-kernel boundary forces zero exposure without changing raw evidence.
- [x] AC #8: Snapshot/policy/cost/risk hashes and MODELED basis are recorded.
- [x] AC #9: Same inputs/seed produce byte-identical canonical JSON.
- [x] AC #10: Material mutations change report identity.
- [x] AC #11: No order-placement or real-money activation interface is added.

## History
- 2026-09-20T17:13:08Z status: open -> in_progress
- 2026-09-20T17:13:08Z auto-follows: linked to predecessor VK-aej2
- 2026-09-20T17:13:08Z claimed by dev-VK-tr7s
- 2026-09-20T19:03:42Z status: in_progress -> in_progress
- 2026-09-20T19:06:11Z status: in_progress -> closed

## Links
- Parent: [[VK-1rbc]]
- Follows: [[VK-aej2]]

## Comments
