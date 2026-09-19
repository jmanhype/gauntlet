---
id: VK-wa2q
title: "Append immutable trial ledgers with operation events"
status: closed
priority: 0
type: feature
labels: [integration, phase-1, delivered]
parent: VK-egll
created_at: 2026-09-18T23:31:15Z
created_by: speed
updated_at: 2026-09-19T03:17:05Z
content_hash: "sha256:63861a10974c607ff0fe2724fcf210ff09c08087a8fc218f39aaf89e6c21952d"
was_blocked_by: [VK-1vhm]
assignee: dev-VK-wa2q
follows: [VK-1vhm]
closed_at: 2026-09-19T03:17:05Z
close_reason: "Accepted: independently tested and code-reviewed immutable trial/event chains at 824b1e6."
---

## Description
## USER INTENT
The owner needs failed and successful trials preserved with tamper-evident history so repeated experimentation cannot silently disappear.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement `data/ledger/trials.jsonl`, `data/ledger/events.jsonl`, `data/ledger/trial-head.json`, and regenerable `data/ledger/events-head.json`. Trial envelopes contain `schema_version`, `entry_type`, `trial_id`, `family_id`, `venue_track`, `recorded_at_utc`, typed `actor`, `payload_hash`, `previous_head_hash`, `entry_hash`, and payload. Event envelopes contain stable `event_id`, actor, verb, subject, argument/output/payload hashes, prior head, event hash, `status`, `error_class`, and trace. Appends serialize under a local exclusive lock. Trial registration records hypothesis and interpretation, family/strategy lineage, venue, data windows and descriptor hashes, features, full parameters/search space, execution assumptions and adverse scenarios, benchmark, budgets and stop condition, one-axis or approved exception, policy/risk/evaluation versions, resolved-config hash, dependencies, and criticality.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Descriptor dependency evaluation: lands in the descriptor graph story.
- Owner authorization of exceptions: lands in the Ed25519 authorization story.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 700 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/ledger/trials.py -> append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult
- src/gauntlet/ledger/events.py -> append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
- src/gauntlet/ledger/verify.py -> verify_chains(data_root: Path) -> ChainVerification
- src/gauntlet/ledger/heads.py -> regenerate_heads(data_root: Path) -> HeadState

CONSUMES:
- VK-1vhm: src/gauntlet/contracts/canonical.py -> canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str
  spec: canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str

### Acceptance Criteria (story contract)
1. A complete `trial.registered` entry can be appended once with the required typed payload and exact envelope fields.
2. Successful and failed service operations append canonical events with `status=OK|ERROR`, error class, hashes, actor, verb, subject, and trace.
3. Both chains recompute every payload, entry, and event hash and reject missing, reordered, rewritten, or deleted lines.
4. Failed calls append an error event without inventing an artifact or advancing a successful result head.
5. An existing immutable destination cannot be overwritten; unfinished runs remain incomplete.
6. No credential, private key, signature, unredacted external payload, or secret value enters either chain.
7. Head files are regenerable from verified bytes and report the current head and byte range.

## Testing Requirements
- Unit: Test required payload fields, error envelopes, hash construction, lock serialization, head regeneration, and rejection of malformed input.
- Integration tests: MANDATORY (no mocks). Run concurrent appends against a real temporary filesystem, verify both chains, then copy and mutate/delete/reorder lines and prove every tamper case fails while the original remains valid.
- Commands to run: `uv run pytest tests/integrity/test_ledger.py`.

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
- [ ] AC #1: A complete `trial.registered` entry can be appended once with the required typed payload and exact envelope fields.
- [ ] AC #2: Successful and failed service operations append canonical events with `status=OK|ERROR`, error class, hashes, actor, verb, subject, and trace.
- [ ] AC #3: Both chains recompute every payload, entry, and event hash and reject missing, reordered, rewritten, or deleted lines.
- [ ] AC #4: Failed calls append an error event without inventing an artifact or advancing a successful result head.
- [ ] AC #5: An existing immutable destination cannot be overwritten; unfinished runs remain incomplete.
- [ ] AC #6: No credential, private key, signature, unredacted external payload, or secret value enters either chain.
- [ ] AC #7: Head files are regenerable from verified bytes and report the current head and byte range.

## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-09-19]: Evidence reviewed and independently verified at story commit 824b1e668bb8261e92599db6260b263692e15fb3.

## nd_contract
status: accepted

### evidence
- Ran `uv run pytest tests/`: 11 passed in 0.22s.
- Ran `uv run pytest tests/integrity/test_ledger.py`: 5 passed in 0.19s.
- Ran `pvg verify` over all 7 delivered files: PASSED, 0 issues.
- Inspected commit 824b1e6: 7 files changed, 690 insertions; clean scope and no stub/TODO markers.
- Verified canonical hashing and write-once primitives are reused from gauntlet.contracts rather than reimplemented.
- Confirmed verify-delivery failures are the already recorded note-ordering false negative, not missing story evidence.

### proof
- [x] AC #1: typed trial payload and exact envelope verified.
- [x] AC #2: OK/ERROR canonical event contracts verified.
- [x] AC #3: payload/event/terminal hashes and tamper rejection verified.
- [x] AC #4: error events do not fabricate output or advance the trial head.
- [x] AC #5: locked append and stale-head rejection preserve immutable bytes.
- [x] AC #6: sensitive/unredacted material is rejected before writes.
- [x] AC #7: heads deterministically regenerate with byte ranges.

## nd_contract
status: delivered

### evidence
- Commit: `824b1e668bb8261e92599db6260b263692e15fb3` on `story/VK-wa2q`.
- Commands run: `uv run --with coverage coverage run -m pytest tests/`; `uv run --with coverage coverage report --include='src/gauntlet/ledger/*' --precision=2`; `uv run pytest tests/integrity/test_ledger.py`; `pvg verify src/gauntlet/ledger/__init__.py src/gauntlet/ledger/_common.py src/gauntlet/ledger/events.py src/gauntlet/ledger/heads.py src/gauntlet/ledger/trials.py src/gauntlet/ledger/verify.py tests/integrity/test_ledger.py --format=text`.
- Summary: full suite PASS 11/11; required ledger suite PASS 5/5; ledger coverage 85.61%; pvg verify PASS with 0 issues.
- Implementation evidence and AC table are in the `## Implementation Evidence (DELIVERED)` note above.

### proof
- [x] AC #1: complete typed `trial.registered` append and exact envelope.
- [x] AC #2: canonical OK/ERROR operation events with required metadata and hashes.
- [x] AC #3: both chains reject byte edits, deletion, and reorder while original verifies.
- [x] AC #4: failed events claim no artifact and preserve the trial result head.
- [x] AC #5: appends serialize and reject stale/conflicting prior heads without overwrite.
- [x] AC #6: sensitive credential/key/signature/unredacted payload material is rejected.
- [x] AC #7: heads regenerate deterministically with head and byte range.

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
  - `uv run --with coverage coverage run -m pytest tests/`
  - `uv run --with coverage coverage report --include='src/gauntlet/ledger/*' --precision=2`
  - `uv run pytest tests/integrity/test_ledger.py`
  - `pvg verify src/gauntlet/ledger/__init__.py src/gauntlet/ledger/_common.py src/gauntlet/ledger/events.py src/gauntlet/ledger/heads.py src/gauntlet/ledger/trials.py src/gauntlet/ledger/verify.py tests/integrity/test_ledger.py --format=text`
- Summary: full suite PASS (11/11); required ledger integration suite PASS (5/5); ledger coverage 85.61%; stub scan PASS.
- Key output:
  - Full suite: `collected 11 items ... 11 passed in 0.20s`
  - Targeted suite: `collected 5 items ... 5 passed in 0.22s`
  - Coverage total: `TOTAL 417 60 85.61%`
  - Verify: `VERIFY: PASSED (7 files scanned, 0 issues)`

### Commit
- Branch: `story/VK-wa2q`
- SHA: `824b1e668bb8261e92599db6260b263692e15fb3`
- Diff budget: 7 files changed, 690 insertions (story limit ~8 files / under 700 LOC)

### pvg verify
- `VERIFY: PASSED (7 files scanned, 0 issues)`

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|------|-------------|---------------|---------------|--------|
| 1 | Complete `trial.registered` payload appends once with exact envelope fields | `src/gauntlet/ledger/trials.py:15`, `src/gauntlet/ledger/trials.py:29` | `tests/integrity/test_ledger.py:40` | PASS |
| 2 | OK/ERROR canonical events carry actor, verb, subject, hashes, error class, and trace | `src/gauntlet/ledger/events.py:13`, `src/gauntlet/ledger/events.py:21` | `tests/integrity/test_ledger.py:40` | PASS |
| 3 | Both chains recompute payload/body and terminal hashes and reject edits, deletion, and reorder | `src/gauntlet/ledger/verify.py:20`, `src/gauntlet/ledger/_common.py:202` | `tests/integrity/test_ledger.py:113` | PASS |
| 4 | ERROR events use zero output hash, preserve the trial ledger/head, and extend only the event chain | `src/gauntlet/ledger/events.py:21`, `src/gauntlet/ledger/_common.py:150` | `tests/integrity/test_ledger.py:40` | PASS |
| 5 | Appends are lock-serialized, reject stale prior heads, and never truncate existing bytes | `src/gauntlet/ledger/_common.py:261` | `tests/integrity/test_ledger.py:66`, `tests/integrity/test_ledger.py:100` | PASS |
| 6 | Credential/private-key/signature/unredacted payload keys and obvious secret values fail closed | `src/gauntlet/ledger/_common.py:181` | `tests/integrity/test_ledger.py:78` | PASS |
| 7 | Heads regenerate deterministically from verified ledger bytes and report head plus byte range | `src/gauntlet/ledger/heads.py:10`, `src/gauntlet/ledger/_common.py:306` | `tests/integrity/test_ledger.py:40` | PASS |

LEARNINGS:
- Reusing `canonical_json`, registered schemas, and `create_exclusive` kept hash and write-once semantics aligned with the upstream contract story.
- Passing the expected prior head explicitly makes restart and conflict behavior observable: the append re-verifies bytes under the local lock and rejects a stale head without touching the ledger.
- Event payload integrity is most robust when `payload_hash` covers the canonical non-integrity event body; verification can then recompute it without storing an unredacted external payload.
- Real-file copies proved all six chain/tamper combinations while retaining a valid original control tree.

## nd_contract
status: delivered

### evidence
- Commit: `824b1e668bb8261e92599db6260b263692e15fb3` on `story/VK-wa2q`.
- Full suite: `uv run --with coverage coverage run -m pytest tests/` -> 11 passed.
- Required suite: `uv run pytest tests/integrity/test_ledger.py` -> 5 passed.
- Coverage: 85.61% for `src/gauntlet/ledger/*`.
- Stub scan: `pvg verify ... --format=text` -> `VERIFY: PASSED (7 files scanned, 0 issues)`.
- Diff budget: 7 files, 690 inserted lines.

### proof
- [x] AC #1: Complete typed trial registration and exact envelope are appended once and verified.
- [x] AC #2: Successful and failed canonical operation events include all required metadata and hashes.
- [x] AC #3: Both chains detect byte edits, deletion, and reorder while the original remains valid.
- [x] AC #4: Failed events record errors without claiming an artifact or mutating the successful trial head.
- [x] AC #5: Lock serialization and prior-head verification reject stale/conflicting appends without overwrite.
- [x] AC #6: Sensitive keys, authorization material, and obvious private/API-key values are rejected before writes.
- [x] AC #7: Head projections deterministically regenerate from verified ledger bytes with current head and byte range.

## nd_contract
status: in_progress

### evidence
- Claimed: 2026-09-19
- Scope: implement the four PRODUCES ledger modules and real-file integrity tests only.

### proof
- [ ] (pending)

## History
- 2026-09-18T23:31:15Z dep_added: blocked_by VK-1vhm
- 2026-09-18T23:31:16Z dep_added: blocks VK-kmbs
- 2026-09-18T23:31:17Z dep_added: blocks VK-pg9j
- 2026-09-18T23:31:19Z dep_added: blocks VK-mfn6
- 2026-09-18T23:31:21Z dep_added: blocks VK-si5s
- 2026-09-18T23:31:21Z dep_added: blocks VK-jbae
- 2026-09-18T23:31:22Z dep_added: blocks VK-0pfo
- 2026-09-18T23:31:24Z dep_added: blocks VK-ddoh
- 2026-09-18T23:31:32Z dep_added: blocks VK-bns7
- 2026-09-18T23:31:32Z dep_added: blocks VK-52g6
- 2026-09-18T23:31:38Z dep_added: blocks VK-3f9f
- 2026-09-19T01:37:42Z dep_added: blocks VK-3v14
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm
- 2026-09-19T02:41:31Z status: open -> in_progress
- 2026-09-19T02:41:31Z auto-follows: linked to predecessor VK-1vhm
- 2026-09-19T02:41:31Z claimed by dev-VK-wa2q
- 2026-09-19T03:11:31Z status: in_progress -> in_progress
- 2026-09-19T03:17:05Z status: in_progress -> closed
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-kmbs
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-pg9j
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-mfn6
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-si5s
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-jbae
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-0pfo
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-ddoh
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-bns7
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-52g6
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-3f9f
- 2026-09-19T03:17:05Z dep_removed: no_longer_blocks VK-3v14

## Links
- Parent: [[VK-egll]]
- Was blocked by: [[VK-1vhm]]
- Follows: [[VK-1vhm]]

## Comments

### 2026-09-18T23:33:03Z speed
RECOMMEND hard-tdd: concurrent append and tamper-chain semantics are subtle and costly to detect later. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: concurrent append and tamper-chain semantics are subtle and costly to detect later. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-19T03:13:39Z speed
DISCOVERED_BUG:
  title: pvg verify-delivery misreads newest-first nd contract notes
  context: VK-wa2q has label delivered and multiple delivered nd_contract notes, including the newest authoritative note with commit SHA, commands, summary, and checked ACs. pvg story verify-delivery reports authoritative contract not delivered and says implementation evidence is missing while pvg nd show displays that evidence. The oldest in_progress claim note remains physically last in the rendered Notes section because nd update --append-notes inserts newer notes first.
  affected_files: pvg story verify-delivery / nd note ordering
  discovered_during: VK-wa2q
