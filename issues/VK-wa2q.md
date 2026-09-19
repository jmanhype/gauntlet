---
id: VK-wa2q
title: "Append immutable trial ledgers with operation events"
status: in_progress
priority: 0
type: feature
labels: [integration, phase-1]
parent: VK-egll
created_at: 2026-09-18T23:31:15Z
created_by: speed
updated_at: 2026-09-19T02:41:31Z
content_hash: "sha256:18785d9b65afb830dee378f38aa3cce8a190ce71a650df5ef6708571fcbfa7d1"
blocks: [VK-kmbs, VK-pg9j, VK-mfn6, VK-si5s, VK-jbae, VK-0pfo, VK-ddoh, VK-bns7, VK-52g6, VK-3f9f, VK-3v14]
was_blocked_by: [VK-1vhm]
assignee: dev-VK-wa2q
follows: [VK-1vhm]
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

## Links
- Parent: [[VK-egll]]
- Blocks: [[VK-kmbs]], [[VK-pg9j]], [[VK-mfn6]], [[VK-si5s]], [[VK-jbae]], [[VK-0pfo]], [[VK-ddoh]], [[VK-bns7]], [[VK-52g6]], [[VK-3f9f]], [[VK-3v14]]
- Was blocked by: [[VK-1vhm]]
- Follows: [[VK-1vhm]]

## Comments

### 2026-09-18T23:33:03Z speed
RECOMMEND hard-tdd: concurrent append and tamper-chain semantics are subtle and costly to detect later. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.

### 2026-09-18T23:33:49Z speed
RECOMMEND hard-tdd: concurrent append and tamper-chain semantics are subtle and costly to detect later. Adds RED/GREEN phases: roughly double the agent passes, tokens, and wall-clock time for this story.
