---
id: VK-jkkn
title: "Resolve immutable run configurations"
status: open
priority: 0
type: feature
labels: [integration, phase-1]
parent: VK-egll
created_at: 2026-09-18T23:31:16Z
created_by: speed
updated_at: 2026-09-18T23:31:16Z
content_hash: "sha256:b8b20c287eb7602231fc9bb14ba46cdedeec2e0547d9a70ecbae02c31e83abd5"
blocked_by: [VK-kmbs]
blocks: [VK-pg9j, VK-mfn6, VK-si5s, VK-0pfo, VK-0c4c, VK-ddoh, VK-dblr, VK-3f9f, VK-rkdr]
was_blocked_by: [VK-1vhm]
---

## Description
## USER INTENT
The owner needs a complete visible configuration for every run so no hidden default or threshold can alter research interpretation.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement immutable versioned profiles and a shared resolver. Every run resolves defaults, profile, explicit CLI/MCP overrides, environment-independent research values, artifact versions, and hashes into one canonical configuration. `--show-config` prints it; `--diff-config` compares it to a profile or prior run. Runtime paths and secret names may be redacted only under a versioned rule that never changes a research threshold. Research- or state-mutating services reject incomplete or hidden values.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- CLI/MCP command surfaces and parity: lands in the shared-interface story.
- Collector credential injection: lands in collector stories.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~6 files, under 450 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- src/gauntlet/config/diff.py -> diff_config(left: ResolvedConfig, right: ResolvedConfig) -> ConfigDiff

CONSUMES:
- VK-1vhm: src/gauntlet/contracts/canonical.py -> canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str
  spec: canonical_json(value: object) -> bytes; sha256_digest(data: bytes) -> str
- VK-kmbs: src/gauntlet/data/descriptors.py -> register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration
  spec: register_descriptor(descriptor: EvidenceDescriptor) -> DescriptorRegistration

### Acceptance Criteria (story contract)
1. A profile plus explicit overrides resolves to a canonical artifact with a stable SHA-256 configuration hash.
2. Every default, override, policy/model/code version, and artifact version appears in the resolved output.
3. Secret values are never accepted or emitted; only a versioned redaction rule may name a secret-bearing field without exposing its value.
4. A hidden or incomplete research-critical value returns `CONFIG_INVALID` before mutation.
5. Config diff identifies added, removed, changed, redacted, and threshold-bearing values without losing provenance.
6. A configuration referenced by a trial or snapshot is immutable and later profile edits do not change its hash.

## Testing Requirements
- Unit: Test precedence, canonical hashing, redaction, immutability, invalid values, and diff completeness.
- Integration tests: MANDATORY (no mocks). Resolve a real TOML profile with overrides, register it through the contract layer, mutate the source profile, and prove the prior resolved hash and bytes remain unchanged.
- Commands to run: `uv run pytest tests/integrity/test_resolved_config.py`.

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
- [ ] AC #1: A profile plus explicit overrides resolves to a canonical artifact with a stable SHA-256 configuration hash.
- [ ] AC #2: Every default, override, policy/model/code version, and artifact version appears in the resolved output.
- [ ] AC #3: Secret values are never accepted or emitted; only a versioned redaction rule may name a secret-bearing field without exposing its value.
- [ ] AC #4: A hidden or incomplete research-critical value returns `CONFIG_INVALID` before mutation.
- [ ] AC #5: Config diff identifies added, removed, changed, redacted, and threshold-bearing values without losing provenance.
- [ ] AC #6: A configuration referenced by a trial or snapshot is immutable and later profile edits do not change its hash.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-1vhm
- 2026-09-18T23:31:16Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:17Z dep_added: blocks VK-pg9j
- 2026-09-18T23:31:19Z dep_added: blocks VK-mfn6
- 2026-09-18T23:31:20Z dep_added: blocks VK-si5s
- 2026-09-18T23:31:21Z dep_added: blocks VK-0pfo
- 2026-09-18T23:31:23Z dep_added: blocks VK-0c4c
- 2026-09-18T23:31:24Z dep_added: blocks VK-ddoh
- 2026-09-18T23:31:36Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:38Z dep_added: blocks VK-3f9f
- 2026-09-19T01:37:42Z dep_added: blocks VK-rkdr
- 2026-09-19T02:37:33Z dep_removed: was_blocked_by VK-1vhm

## Links
- Parent: [[VK-egll]]
- Blocks: [[VK-pg9j]], [[VK-mfn6]], [[VK-si5s]], [[VK-0pfo]], [[VK-0c4c]], [[VK-ddoh]], [[VK-dblr]], [[VK-3f9f]], [[VK-rkdr]]
- Blocked by: [[VK-kmbs]]
- Was blocked by: [[VK-1vhm]]

## Comments
