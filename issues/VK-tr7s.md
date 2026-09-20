---
id: VK-tr7s
title: "E2e: compare four policy baselines on frozen evidence"
status: in_progress
priority: 1
type: task
parent: VK-1rbc
created_at: 2026-09-20T17:12:45Z
created_by: speed
updated_at: 2026-09-20T17:13:08Z
content_hash: "sha256:f404b101fa9f302a8268b5978b0ac3ff03ca4d8f4f15d538f34df5676ec85d0e"
labels: [e2e, capstone, walking-skeleton]
assignee: dev-VK-tr7s
follows: [VK-aej2]
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


## History
- 2026-09-20T17:13:08Z status: open -> in_progress
- 2026-09-20T17:13:08Z auto-follows: linked to predecessor VK-aej2
- 2026-09-20T17:13:08Z claimed by dev-VK-tr7s

## Links
- Parent: [[VK-1rbc]]
- Follows: [[VK-aej2]]

## Comments
