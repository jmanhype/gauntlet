---
id: VK-pg9j
title: "Capture Bitquery Solana snapshots"
status: open
priority: 2
type: feature
labels: [external-integration, integration, phase-1, walking-skeleton]
parent: VK-u40v
created_at: 2026-09-18T23:31:17Z
created_by: speed
updated_at: 2026-09-20T04:18:55Z
content_hash: "sha256:4d89347db82edeaaef8448e77878331fc75cefaff8222e4e3c7d06bb706d6d03"
blocks: [VK-pol1, VK-bbmn, VK-jvku, VK-si5s, VK-ldg1, VK-4qfy]
was_blocked_by: [VK-wa2q, VK-kmbs, VK-jkkn]
assignee: dev-VK-pg9j
follows: [VK-wa2q, VK-kmbs, VK-jkkn]
---

## Description
## USER INTENT
The owner needs immutable Solana DEX bars and event snapshots so discovery evidence has explicit provenance and execution state.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement `audit/collectors/bitquery.py` as the only Bitquery collector. It records immutable request/response pages, cursors, terminal condition, source watermark, bounded exponential backoff, rate-limit behavior, API-cost events before and after capture, and content hashes. Credentials are injected only into the collector process and never accepted as CLI/MCP arguments or copied into payloads, events, reports, exports, or hashes. Raw-to-derived registration is atomic: `solana.bars` and `solana.events` descriptors plus Parquet partitions, transformation provenance, quality/freshness/criticality declarations, and descriptor hashes are present before complete state. Duplicate keys are collector identity, normalized request, cursor, source watermark, and payload hash.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Judge reserve pricing: lands in exact Solana execution.
- Hyperliquid and Scarlett collection: sibling collector stories.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 750 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/audit/collectors/bitquery.py -> collect_bitquery(request: CollectorRequest, budget: BudgetContext) -> CaptureResult
- src/gauntlet/audit/collectors/bitquery.py -> derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData

CONSUMES:
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-kmbs: src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
  spec: register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
- VK-wa2q: src/gauntlet/ledger/events.py -> append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult
  spec: append_event(event: EventRecord, previous_head: str | None) -> LedgerAppendResult

### Acceptance Criteria (story contract)
1. Blocking configuration sub-task: owner provisions `BITQUERY_API_KEY` only in the local process environment before real-endpoint verification; absence fails before spend.
2. Real-endpoint verification (non-automatable): run one owner-approved minimum-cost Bitquery capture and record command output plus artifact/event hashes without exposing the credential.
3. Every page records response hash, cursor, watermark, retry/backoff outcome, and terminal condition.
4. Pre- and post-capture cost events enforce the family/API budget; exhausted or unauthorized budget fails before additional spend.
5. Partial capture, truncation, malformed response, cursor regression, or checksum failure creates quarantined descriptor state and blocks dependent gates without overwriting raw bytes.
6. An exact redownload is retained as an immutable duplicate observation using the specified duplicate key; no older page is silently replaced.
7. Derived `solana.bars` and `solana.events` descriptors are registered atomically with transformation provenance and venue_track `solana_dex`.
8. Sanitized event output contains no bearer token, credential, or secret.

## Testing Requirements
- Unit: Use golden response pages to test pagination, malformed data, duplicate keys, budget exhaustion, and descriptor registration without network access.
- Integration tests: MANDATORY (no mocks). Run the real endpoint once under a tiny budget, then verify raw pages, derived Parquet, descriptors, cost events, and chain hashes from disk.
- Commands to run: `uv run pytest tests/collectors/test_bitquery.py` plus the recorded real-endpoint evidence.

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
- [ ] AC #1: Blocking configuration sub-task: owner provisions `BITQUERY_API_KEY` only in the local process environment before real-endpoint verification; absence fails before spend.
- [ ] AC #2: Real-endpoint verification (non-automatable): run one owner-approved minimum-cost Bitquery capture and record command output plus artifact/event hashes without exposing the credential.
- [ ] AC #3: Every page records response hash, cursor, watermark, retry/backoff outcome, and terminal condition.
- [ ] AC #4: Pre- and post-capture cost events enforce the family/API budget; exhausted or unauthorized budget fails before additional spend.
- [ ] AC #5: Partial capture, truncation, malformed response, cursor regression, or checksum failure creates quarantined descriptor state and blocks dependent gates without overwriting raw bytes.
- [ ] AC #6: An exact redownload is retained as an immutable duplicate observation using the specified duplicate key; no older page is silently replaced.
- [ ] AC #7: Derived `solana.bars` and `solana.events` descriptors are registered atomically with transformation provenance and venue_track `solana_dex`.
- [ ] AC #8: Sanitized event output contains no bearer token, credential, or secret.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:

```bash
cd /Users/speed/Downloads/AI_Videos/google-usercontent/gauntlet/.claude/worktrees/dev-VK-pg9j
git diff --check
uv run pytest tests/collectors/test_bitquery.py
uv run pytest
pvg verify src/gauntlet/audit/collectors/bitquery.py src/gauntlet/audit/collectors/parquet.py tests/collectors/test_bitquery.py --format=text
```

Offline progress results:

- Story tests: 8/8 passed.
- Full suite: 67/67 passed.
- Substantive changed-file verify: passed with zero issues.
- Offline collector commit: `33774bb`.

### Remaining blocker

AC #2 requires one owner-approved minimum-cost real Bitquery endpoint capture. This pass intentionally performed no network access and did not read, print, accept, or store `BITQUERY_API_KEY`. Calling the collector without an injected transport fails closed with `LIVE_ENDPOINT_BLOCKED` before budget spend or transport invocation. The story must remain open until the real-endpoint evidence is completed.

## nd_contract
status: in_progress

### evidence
- Offline/model-free collector implementation committed at `33774bb`.
- Independent story/full tests and substantive pvg verification passed.

### proof
- [ ] AC #1: Credential configuration behavior remains to be exercised against the real endpoint process.
- [ ] AC #2: Real-endpoint minimum-cost capture not yet run.
- [x] AC #3: Offline page/cursor/watermark/retry/terminal metadata implemented and tested.
- [x] AC #4: Offline pre/post budget behavior implemented and tested.
- [x] AC #5: Offline malformed/truncation/checksum/regression/partial quarantine implemented and tested.
- [x] AC #6: Immutable duplicate retention implemented and tested.
- [x] AC #7: Atomic bars/events descriptor provenance implemented and tested.
- [x] AC #8: Sanitized events/secret rejection implemented and tested.


## History
- 2026-09-18T23:31:17Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:17Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:17Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:18Z dep_added: blocks VK-pol1
- 2026-09-18T23:31:18Z dep_added: blocks VK-bbmn
- 2026-09-18T23:31:18Z dep_added: blocks VK-jvku
- 2026-09-18T23:31:20Z dep_added: blocks VK-si5s
- 2026-09-18T23:31:22Z dep_added: blocks VK-0c4c
- 2026-09-18T23:31:39Z dep_added: blocks VK-ldg1
- 2026-09-19T01:37:42Z dep_added: blocks VK-4qfy
- 2026-09-19T01:37:43Z dep_removed: no_longer_blocks VK-0c4c
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs
- 2026-09-19T04:41:26Z dep_removed: was_blocked_by VK-jkkn
- 2026-09-19T17:07:24Z status: open -> in_progress
- 2026-09-19T17:07:24Z auto-follows: linked to predecessor VK-wa2q
- 2026-09-19T17:07:24Z auto-follows: linked to predecessor VK-kmbs
- 2026-09-19T17:07:24Z auto-follows: linked to predecessor VK-jkkn
- 2026-09-19T17:07:24Z claimed by dev-VK-pg9j
- 2026-09-20T02:38:57Z status: in_progress -> open

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-pol1]], [[VK-bbmn]], [[VK-jvku]], [[VK-si5s]], [[VK-ldg1]], [[VK-4qfy]]
- Was blocked by: [[VK-wa2q]], [[VK-kmbs]], [[VK-jkkn]]
- Follows: [[VK-wa2q]], [[VK-kmbs]], [[VK-jkkn]]

## Comments

### 2026-09-20T02:38:57Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)

### 2026-09-20T04:18:55Z speed
Current dispatcher check: BITQUERY_API_KEY is absent from the coordinator environment (presence tested without reading or printing the value). No network request, credential lookup, or spend was attempted. VK-pg9j remains blocked for its owner-approved minimum-cost live capture until the operator injects the key only into the collector process.
