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
updated_at: 2026-09-18T23:31:17Z
content_hash: "sha256:bdf00aaa0cc2999dd931049f522ff47ab774ca5771547852714db12ccc22ca03"
blocked_by: [VK-jkkn, VK-kmbs]
blocks: [VK-pol1, VK-bbmn, VK-jvku, VK-si5s, VK-ldg1, VK-4qfy]
was_blocked_by: [VK-wa2q]
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

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-pol1]], [[VK-bbmn]], [[VK-jvku]], [[VK-si5s]], [[VK-ldg1]], [[VK-4qfy]]
- Blocked by: [[VK-jkkn]], [[VK-kmbs]]
- Was blocked by: [[VK-wa2q]]

## Comments
