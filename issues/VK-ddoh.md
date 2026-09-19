---
id: VK-ddoh
title: "Record untouched prospective signals"
status: open
priority: 1
type: feature
labels: [integration, phase-1]
parent: VK-0auj
created_at: 2026-09-18T23:31:23Z
created_by: speed
updated_at: 2026-09-18T23:31:23Z
content_hash: "sha256:868eb66daa2dc3d1f56704945e01332bc27db875e0bc710f228ddf6330d4e791"
blocked_by: [VK-0c4c, VK-jkkn]
blocks: [VK-zvia, VK-vqvy]
was_blocked_by: [VK-wa2q]
---

## Description
## USER INTENT
The owner needs signals committed before outcomes are knowable so prospective evidence cannot be backfilled to manufacture confidence.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement the prospective recorder. Before outcome can be known, append candidate/model/config/policy fingerprints, signal timestamp and all information then available, intended action, notional, horizon, execution assumptions, confidence/path share and semantics, and dependency snapshot/status. Outcomes append later with venue state used to resolve them. Records are hash-chained and immutable. A late signal is labeled historical and can never satisfy dual temporal evidence. Open, skipped, and failure reasons have immutable status transitions.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Prospective outcome statistical scoring: lab stories.
- Live paper trading daemon or order placement: prohibited.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 600 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/judge/prospective.py -> append_signal(record: ProspectiveSignal) -> ProspectiveRecord
- src/gauntlet/judge/prospective.py -> resolve_outcome(record_id: str, outcome: ProspectiveOutcome) -> ProspectiveRecord

CONSUMES:
- VK-0c4c: src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
  spec: evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
- VK-wa2q: src/gauntlet/ledger/events.py -> append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
  spec: append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig

### Acceptance Criteria (story contract)
1. Pre-outcome records are append-only, hash-chained, and include every declared fingerprint, action, assumption, confidence semantic, and dependency snapshot.
2. Outcome append never mutates the pre-outcome signal bytes or status history.
3. A signal first recorded after label availability is labeled historical and is ineligible for prospective gate credit.
4. Open, skipped, execution-failure, and resolved transitions record actor, reason, and timestamp.
5. The dependency snapshot distinguishes OBSERVED and MODELED values and preserves exact descriptor hashes.
6. Tampering with either signal or outcome history is detectable by chain verification.

## Testing Requirements
- Unit: Test schema completeness, time ordering, transition immutability, historical labeling, and tamper detection.
- Integration tests: MANDATORY (no mocks). Commit real synthetic signals before labels exist in a temporary chain, resolve outcomes later, attempt a late backfilled signal, and verify classifications and hashes.
- Commands to run: `uv run pytest tests/judge/test_prospective.py`.

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
- [ ] AC #1: Pre-outcome records are append-only, hash-chained, and include every declared fingerprint, action, assumption, confidence semantic, and dependency snapshot.
- [ ] AC #2: Outcome append never mutates the pre-outcome signal bytes or status history.
- [ ] AC #3: A signal first recorded after label availability is labeled historical and is ineligible for prospective gate credit.
- [ ] AC #4: Open, skipped, execution-failure, and resolved transitions record actor, reason, and timestamp.
- [ ] AC #5: The dependency snapshot distinguishes OBSERVED and MODELED values and preserves exact descriptor hashes.
- [ ] AC #6: Tampering with either signal or outcome history is detectable by chain verification.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:24Z dep_added: blocked_by VK-0c4c
- 2026-09-18T23:31:24Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:24Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:26Z dep_added: blocks VK-zvia
- 2026-09-18T23:31:42Z dep_added: blocks VK-vqvy
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-zvia]], [[VK-vqvy]]
- Blocked by: [[VK-0c4c]], [[VK-jkkn]]
- Was blocked by: [[VK-wa2q]]

## Comments
