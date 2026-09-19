---
id: VK-uyca
title: "E2e: record an owner decision from immutable evidence"
status: open
priority: 0
type: feature
labels: [phase-1, capstone, e2e]
parent: VK-1rbc
created_at: 2026-09-18T23:31:44Z
created_by: speed
updated_at: 2026-09-19T01:38:27Z
content_hash: "sha256:6df3f360a373b38df915ae4bc5b3e69fe5c6dc42df816a4a17f5d1354452fdb1"
blocked_by: [VK-2e0k, VK-bns7, VK-52g6, VK-aej2]
blocks: [VK-hiuk]
---

## Description
## USER INTENT
The owner can evaluate a gate, preserve its snapshot, sign one permitted decision locally, and see agents denied impersonation.

Observable outcome: the owner can run the declared E2e command, inspect or display its output, and verify that the full path returns the declared result, stores its immutable artifacts, and emits the corresponding hash-verified events.

## Context (Embedded)
This is the E2e capstone for epic VK-1rbc. It must exercise the completed epic from the owner perspective after every sibling story. It verifies real local files, chains, subprocesses, outputs, and exit codes. It does not establish new module semantics.

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
- tests/e2e/test_decision_authorization.py -> owner-perspective decision drill

CONSUMES:
- VK-2e0k: src/gauntlet/policy/engine.py -> evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
  spec: evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
- VK-bns7: src/gauntlet/decisions/writer.py -> write_decision_snapshot(request: SnapshotRequest) -> DecisionSnapshot
  spec: write_decision_snapshot(request: SnapshotRequest) -> DecisionSnapshot
- VK-52g6: src/gauntlet/auth/owner.py -> verify_owner_action(action: SignedOwnerAction, context: CapabilityContext) -> AuthorizationResult
  spec: verify_owner_action(action: SignedOwnerAction, context: CapabilityContext) -> AuthorizationResult

### Acceptance Criteria (story contract)
1. A real synthetic evidence bundle produces PASS, FAIL, BLOCKED, and INSUFFICIENT_EVIDENCE runs; one valid local owner action extends its snapshot and invalid/replayed/agent-submitted actions leave state unchanged.
2. The E2e command or test exits nonzero on the first integrity, authorization, dependency, projection, or contract failure and emits machine-readable JSON identifying the failed stage.
3. The run records canonical success or error events with the prior event head and never invents an artifact.
4. 4. Aggregate precedence is demonstrated exhaustively across the four states. 5. The signed owner extension records actor.kind=human while the original snapshot bytes remain byte-for-byte unchanged. 6. A FAIL override, where permitted, records a separate exception with forensics and unchanged computed gate results. 7. A BLOCKED dependency cannot be promoted by owner preference.

## Testing Requirements
- E2e tests ONLY. No unit tests, no integration tests. Tests must exercise the full system as a user would. No mocks of any kind.
- Commands to run: `uv run pytest tests/e2e/test_decision_authorization.py`.

## MANDATORY SKILLS
- None identified.

## Delivery Requirements
- Developer must paste unedited E2e output and artifact/event hashes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label.

## nd_contract
status: new

### evidence
- Created 2026-09-18 as the final capstone of epic VK-1rbc.
- All sibling dependencies are explicitly recorded in nd.

### proof
- [ ] AC #1: Owner-perspective scenario executes successfully.
- [ ] AC #2: Failure path exits nonzero with machine-readable JSON.
- [ ] AC #3: Event integrity and no-artifact-on-error behavior are verified.
- [ ] AC #4: 4. Aggregate precedence is demonstrated exhaustively across the four states. 5. The signed owner extension records actor.kind=human while the original snapshot bytes remain byte-for-byte unchanged. 6. A FAIL override, where permitted, records a separate exception with forensics and unchanged computed gate results. 7. A BLOCKED dependency cannot be promoted by owner preference.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: include synthetic precedence sibling

GENERAL RULE SWEEP: Every epic capstone is blocked by every sibling.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:

CONSUMES:
- VK-aej2: src/gauntlet/policy/precedence.py -> evaluate_precedence(rule_results: list[RuleResult]) -> GateState
  spec: evaluate_precedence(rule_results: list[RuleResult]) -> GateState

### Acceptance Criteria (repair revision)
1. The decision E2e drill begins from the synthetic precedence contract before exercising real evidence integration.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The decision E2e drill begins from the synthetic precedence contract before exercising real evidence integration.


## History
- 2026-09-18T23:31:45Z dep_added: blocked_by VK-2e0k
- 2026-09-18T23:31:45Z dep_added: blocked_by VK-bns7
- 2026-09-18T23:31:45Z dep_added: blocked_by VK-52g6
- 2026-09-18T23:31:48Z dep_added: blocks VK-hiuk
- 2026-09-19T01:37:44Z dep_added: blocked_by VK-aej2

## Links
- Parent: [[VK-1rbc]]
- Blocks: [[VK-hiuk]]
- Blocked by: [[VK-2e0k]], [[VK-bns7]], [[VK-52g6]], [[VK-aej2]]

## Comments
