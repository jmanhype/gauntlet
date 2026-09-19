---
id: VK-ldg1
title: "E2e: exercise isolated research inputs"
status: open
priority: 2
type: feature
labels: [phase-1, capstone, e2e]
parent: VK-u40v
created_at: 2026-09-18T23:31:38Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:1aa81ee036d603bb704e567da4c7793b3e6e50a6628e8bd6f5f6415a11891997"
blocked_by: [VK-pg9j, VK-pol1, VK-bbmn, VK-jvku, VK-7ubc, VK-si5s, VK-jbae, VK-0pfo, VK-4qfy]
blocks: [VK-hiuk]
was_blocked_by: [VK-mfn6]
---

## Description
## USER INTENT
The owner can collect minimum real venue/external snapshots, run isolated model and factory work, and see budgets, health, roles, and risk remain separated.

Observable outcome: the owner can run the declared E2e command, inspect or display its output, and verify that the full path returns the declared result, stores its immutable artifacts, and emits the corresponding hash-verified events.

## Context (Embedded)
This is the E2e capstone for epic VK-u40v. It must exercise the completed epic from the owner perspective after every sibling story. It verifies real local files, chains, subprocesses, outputs, and exit codes. It does not establish new module semantics.

Phase 1 boundaries:
- No order placement, real-money exposure, public API, daemon, multi-tenant access, or social claim.
- Paper/simulated records are evidence, not executions.
- No database engine dependency; all projections regenerate from immutable files.

## OUT OF SCOPE
- New feature behavior or repaired implementation semantics: a failing capstone creates a bug story rather than broadening this story.
- Live trading, public exposure, or remote access: explicit non-goals.

## DIFF BUDGET
~2 files, under 350 changed LOC.

## Boundary Map
PRODUCES:
- tests/e2e/test_isolated_inputs.py -> owner-perspective isolated-input drill

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
  spec: collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
- VK-pol1: src/gauntlet/audit/collectors/hyperliquid.py -> collect_hyperliquid(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
  spec: collect_hyperliquid(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
- VK-bbmn: src/gauntlet/audit/roles.py -> declare_role(artifact_id: str, role: ScarlettRole, trial_id: str) -> RoleDeclaration
  spec: declare_role(artifact_id: str, role: ScarlettRole, trial_id: str) -> RoleDeclaration
- VK-jvku: src/gauntlet/audit/health.py -> summarize_collection_health(scope: CollectionScope, as_of: datetime) -> CollectionHealth
  spec: summarize_collection_health(scope: CollectionScope, as_of: datetime) -> CollectionHealth
- VK-7ubc: src/gauntlet/model/adaptation.py -> run_adaptation(manifest: AdaptationManifest, model: ModelRegistration) -> AdaptationRun
  spec: run_adaptation(manifest: AdaptationManifest, model: ModelRegistration) -> AdaptationRun
- VK-jbae: src/gauntlet/factory/accounting.py -> evaluate_family_budget(family_id: str, as_of: datetime) -> BudgetState
  spec: evaluate_family_budget(family_id: str, as_of: datetime) -> BudgetState
- VK-0pfo: src/gauntlet/risk/kernel.py -> evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult
  spec: evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult

### Acceptance Criteria (story contract)
1. One real end-to-end local run executes approved minimum-cost Bitquery, Hyperliquid, and Scarlett collection; registers model and factory outputs; and evaluates paper risk and family budget without pooling venues or promoting a candidate.
2. The E2e command or test exits nonzero on the first integrity, authorization, dependency, projection, or contract failure and emits machine-readable JSON identifying the failed stage.
3. The run records canonical success or error events with the prior event head and never invents an artifact.
4. 4. Bitquery, Hyperliquid, and Scarlett real-endpoint evidence is present with sanitized events and immutable hashes; missing owner-approved credentials fail before spend. 5. A Scarlett benchmark/candidate conflict and a cross-venue pooling attempt both block. 6. Core never imports factory; factory subprocess output and search budget are content-hashed and exhausted on schedule. 7. Risk boundary changes disposition input without changing any evidence-gate arithmetic, and no order-placement verb exists.

## Testing Requirements
- E2e tests ONLY. No unit tests, no integration tests. Tests must exercise the full system as a user would. No mocks of any kind.
- Commands to run: `uv run pytest tests/e2e/test_isolated_inputs.py`.

## MANDATORY SKILLS
- None identified.

## Delivery Requirements
- Developer must paste unedited E2e output and artifact/event hashes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label.

## nd_contract
status: new

### evidence
- Created 2026-09-18 as the final capstone of epic VK-u40v.
- All sibling dependencies are explicitly recorded in nd.

### proof
- [ ] AC #1: Owner-perspective scenario executes successfully.
- [ ] AC #2: Failure path exits nonzero with machine-readable JSON.
- [ ] AC #3: Event integrity and no-artifact-on-error behavior are verified.
- [ ] AC #4: 4. Bitquery, Hyperliquid, and Scarlett real-endpoint evidence is present with sanitized events and immutable hashes; missing owner-approved credentials fail before spend. 5. A Scarlett benchmark/candidate conflict and a cross-venue pooling attempt both block. 6. Core never imports factory; factory subprocess output and search budget are content-hashed and exhausted on schedule. 7. Risk boundary changes disposition input without changing any evidence-gate arithmetic, and no order-placement verb exists.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: include reserve sibling

GENERAL RULE SWEEP: Every epic capstone is blocked by every sibling.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-4qfy: src/gauntlet/audit/collectors/solana_reserves.py -> derive_reserve_events(raw_snapshot: SnapshotDescriptor, events: VenueEvents) -> ReserveSeries
  spec: derive_reserve_events(raw_snapshot: SnapshotDescriptor, events: VenueEvents) -> ReserveSeries

### Acceptance Criteria (repair revision)
1. The isolated-inputs E2e drill proves event-level Solana reserves are captured/derived, hashed, and venue-separated.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The isolated-inputs E2e drill proves event-level Solana reserves are captured/derived, hashed, and venue-separated.


## History
- 2026-09-18T23:31:39Z dep_added: blocked_by VK-pg9j
- 2026-09-18T23:31:39Z dep_added: blocked_by VK-pol1
- 2026-09-18T23:31:39Z dep_added: blocked_by VK-bbmn
- 2026-09-18T23:31:39Z dep_added: blocked_by VK-jvku
- 2026-09-18T23:31:40Z dep_added: blocked_by VK-mfn6
- 2026-09-18T23:31:40Z dep_added: blocked_by VK-7ubc
- 2026-09-18T23:31:40Z dep_added: blocked_by VK-si5s
- 2026-09-18T23:31:40Z dep_added: blocked_by VK-jbae
- 2026-09-18T23:31:41Z dep_added: blocked_by VK-0pfo
- 2026-09-18T23:31:47Z dep_added: blocks VK-hiuk
- 2026-09-19T01:37:44Z dep_added: blocked_by VK-4qfy
- 2026-09-19T17:06:08Z dep_removed: was_blocked_by VK-mfn6

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-hiuk]]
- Blocked by: [[VK-pg9j]], [[VK-pol1]], [[VK-bbmn]], [[VK-jvku]], [[VK-7ubc]], [[VK-si5s]], [[VK-jbae]], [[VK-0pfo]], [[VK-4qfy]]
- Was blocked by: [[VK-mfn6]]

## Comments
