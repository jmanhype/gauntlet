---
id: VK-0pfo
title: "Separate portfolio risk from evidence gates"
status: open
priority: 2
type: feature
labels: [integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:21Z
created_by: speed
updated_at: 2026-09-18T23:31:21Z
content_hash: "sha256:1c780f5ae8644558e0df14d7340ba296a57cff117e2d5485e08ffd219ef9f0ed"
blocked_by: [VK-jkkn]
blocks: [VK-2e0k, VK-1ptl, VK-ldg1]
was_blocked_by: [VK-wa2q, VK-kmbs]
---

## Description
## USER INTENT
The owner needs risk boundaries enforced for paper research without letting conservative sizing cure an evidence failure or evidence PASS authorize exposure.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Import the QTS limits as canonical `policies/risk/qts.risk@v1.json` with lineage: source repository/file/content hash, import date, normalization, every parameter, unit, scope, semantics, venue applicability and adaptation, owner authorization, and original-to-GAUNTLET mapping. Implement versioned position sizing, exposure, drawdown, concentration, correlation, circuit-breaker, timing, and operating-boundary checks over paper portfolio state. Risk emits requested/approved size, checks, warnings, adjusted size, policy version, and boundary events. Portfolio state is MODELED. Risk can create HOLD, QUARANTINE, or stop but never changes evidence gate arithmetic or authorizes real money.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Importing external QTS files beyond the declared lineage artifact: out of scope.
- Evidence thresholds and promotion rules: decision-engine story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~7 files, under 650 changed LOC.

## Boundary Map
PRODUCES:
- policies/risk/qts.risk@v1.json -> canonical risk-policy manifest v1
- src/gauntlet/risk/import_qts.py -> import_qts(source: QTSSource, authorization: OwnerAuthorizationRef) -> RiskPolicyVersion
- src/gauntlet/risk/kernel.py -> evaluate_risk(request: RiskRequest, portfolio: PaperPortfolio, policy: RiskPolicyVersion) -> RiskCheckResult

CONSUMES:
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-wa2q: src/gauntlet/ledger/events.py -> append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
  spec: append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
- VK-kmbs: src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
  spec: register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration

### Acceptance Criteria (story contract)
1. Risk policy v1 is canonical, content-hashed, immutable, and carries complete QTS lineage and owner authorization reference.
2. Sizing/check output records requested size, approved/adjusted size, every check, warnings, policy version, and venue applicability.
3. Boundary events append limit/breaker state, duration, reason, affected track, actor, and timestamp without mutating gate arithmetic.
4. Changing sizing, stops, or exposure during optimization creates a new trial and trial-history input.
5. Portfolio and risk projections are labeled MODELED and never satisfy an OBSERVED-outcome gate rule.
6. A risk breach can yield HOLD, QUARANTINE, or stop while evidence PASS cannot override the boundary or authorize real exposure.
7. No order-placement interface or real-money activation command is added.

## Testing Requirements
- Unit: Test QTS field mapping, units, policy immutability, sizing adjustments, boundary events, and domain separation.
- Integration tests: MANDATORY (no mocks). Evaluate a real synthetic paper portfolio under imported limits, trigger one breaker, and verify gate inputs and recorded gate arithmetic remain unchanged while disposition input changes.
- Commands to run: `uv run pytest tests/risk/test_policy_kernel.py`.

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
- [ ] AC #1: Risk policy v1 is canonical, content-hashed, immutable, and carries complete QTS lineage and owner authorization reference.
- [ ] AC #2: Sizing/check output records requested size, approved/adjusted size, every check, warnings, policy version, and venue applicability.
- [ ] AC #3: Boundary events append limit/breaker state, duration, reason, affected track, actor, and timestamp without mutating gate arithmetic.
- [ ] AC #4: Changing sizing, stops, or exposure during optimization creates a new trial and trial-history input.
- [ ] AC #5: Portfolio and risk projections are labeled MODELED and never satisfy an OBSERVED-outcome gate rule.
- [ ] AC #6: A risk breach can yield HOLD, QUARANTINE, or stop while evidence PASS cannot override the boundary or authorize real exposure.
- [ ] AC #7: No order-placement interface or real-money activation command is added.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:21Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:22Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:22Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:31Z dep_added: blocks VK-2e0k
- 2026-09-18T23:31:33Z dep_added: blocks VK-1ptl
- 2026-09-18T23:31:41Z dep_added: blocks VK-ldg1
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-2e0k]], [[VK-1ptl]], [[VK-ldg1]]
- Blocked by: [[VK-jkkn]]
- Was blocked by: [[VK-wa2q]], [[VK-kmbs]]

## Comments
