---
id: VK-ddoh
title: "Record untouched prospective signals"
status: closed
priority: 1
type: feature
labels: [integration, phase-1, delivered, accepted]
parent: VK-0auj
created_at: 2026-09-18T23:31:23Z
created_by: speed
updated_at: 2026-09-19T16:28:10Z
content_hash: "sha256:f2322de3ada3c436a3472aa8ed795fa56d12a0ea169f04a54ef80aa7fb4b1fb4"
was_blocked_by: [VK-wa2q, VK-jkkn, VK-0c4c]
assignee: dev-VK-ddoh
follows: [VK-wa2q, VK-jkkn, VK-0c4c]
closed_at: 2026-09-19T16:28:10Z
close_reason: "Accepted: independently reran story tests (4/4), full suite (52/52), pvg verify (3 files, 0 issues), git diff check, and diff-budget/hash inspection. Signals and outcomes are append-only/hash-chained, late signals are historical, transitions and dependency provenance are preserved, and tampering is detected."
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
## Implementation Evidence

Commands run:

```bash
cd /Users/speed/Downloads/AI_Videos/google-usercontent/gauntlet/.claude/worktrees/dev-VK-ddoh
git diff --check
uv run pytest tests/judge/test_prospective.py
uv run pytest
pvg verify src/gauntlet/judge/prospective.py src/gauntlet/judge/__init__.py tests/judge/test_prospective.py --include-tests --format=text
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Story tests: 4/4 passed.
- Full suite: 52/52 passed.
- `pvg verify`: passed for all 3 scanned files with zero issues.
- Diff budget: 598 insertions and 1 deletion, 599 changed LOC total, below the story’s 600 changed-LOC ceiling.
- The full suite’s policy fixture intentionally prints `AGGREGATE: BLOCKED` and two synthetic-rule diagnostics, but pytest completes with 52/52 passed. This is existing expected policy-test output, not a runtime failure.

### CI/Test Results

```text
tests/judge/test_prospective.py: 4 passed
full suite: 52 passed
pvg verify: PASSED (3 files scanned, 0 issues)
```

Summary: implemented append-only, hash-chained prospective signal records with complete fingerprints/action/assumptions/confidence semantics/dependency snapshots; immutable later outcomes and status transitions; historical classification for late signals; durable actor/reason/timestamp transitions; OBSERVED versus MODELED dependency provenance; tamper detection; and machine-readable fail-closed errors. No database engine, public API, daemon, trading, or order placement was added.

Commit SHA: a154005

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Pre-outcome records append-only/hash-chained with all declared evidence | PASS | `append_signal`, integration test, and chain verification. |
| 2. Outcome append never mutates signal bytes/status history | PASS | Signal bytes compared before/after resolution in integration test. |
| 3. Late signal labeled historical and ineligible for prospective credit | PASS | Late-signal test. |
| 4. Open/skipped/execution-failure/resolved transitions preserve actor/reason/timestamp | PASS | Transition tests. |
| 5. Dependency snapshot distinguishes OBSERVED/MODELED and exact descriptor hashes | PASS | Registry validation and snapshot mapping test. |
| 6. Signal/outcome tampering detected | PASS | Byte-tamper test returns invalid chain. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-18T23:31:24Z dep_added: blocked_by VK-0c4c
- 2026-09-18T23:31:24Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:24Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:26Z dep_added: blocks VK-zvia
- 2026-09-18T23:31:42Z dep_added: blocks VK-vqvy
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q
- 2026-09-19T04:41:26Z dep_removed: was_blocked_by VK-jkkn
- 2026-09-19T05:50:41Z dep_removed: was_blocked_by VK-0c4c
- 2026-09-19T13:04:44Z status: open -> in_progress
- 2026-09-19T13:04:44Z auto-follows: linked to predecessor VK-wa2q
- 2026-09-19T13:04:44Z auto-follows: linked to predecessor VK-jkkn
- 2026-09-19T13:04:44Z auto-follows: linked to predecessor VK-0c4c
- 2026-09-19T13:04:44Z claimed by dev-VK-ddoh
- 2026-09-19T16:27:04Z status: in_progress -> in_progress
- 2026-09-19T16:28:10Z status: in_progress -> closed
- 2026-09-19T16:28:10Z dep_removed: no_longer_blocks VK-zvia
- 2026-09-19T16:28:10Z dep_removed: no_longer_blocks VK-vqvy

## Links
- Parent: [[VK-0auj]]
- Was blocked by: [[VK-wa2q]], [[VK-jkkn]], [[VK-0c4c]]
- Follows: [[VK-wa2q]], [[VK-jkkn]], [[VK-0c4c]]

## Comments
