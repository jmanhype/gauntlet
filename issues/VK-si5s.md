---
id: VK-si5s
title: "Isolate factory candidate races"
status: open
priority: 3
type: feature
labels: [integration, phase-1]
parent: VK-u40v
created_at: 2026-09-18T23:31:20Z
created_by: speed
updated_at: 2026-09-18T23:31:20Z
content_hash: "sha256:032c8590a8df367369be1c36ba5c79c8f67fb59a6056b5a804b8d542272a509d"
blocked_by: [VK-pg9j]
blocks: [VK-jbae, VK-dblr, VK-ldg1]
was_blocked_by: [VK-wa2q, VK-jkkn]
---

## Description
## USER INTENT
The owner needs candidate invention to remain exploratory and runtime-isolated so factory scoring can never become the business gate.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Create separately locked `factory/pyproject.toml` and `factory/uv.lock` using `numpy==1.23.5`; core resolves `numpy>=2.0,<3.0`. Core launches factory only as a subprocess, for example `uv --project factory run ...`, and receives content-hashed artifact files. Candidate definitions record strategy family, prompt/module lineage, features, parameters, search space, execution assumptions, and seed. Races record variant ranking, score decomposition, signals, primitive trade/equity artifacts, engine identity, fallback disclosure, and exploratory labels. The root project has no factory workspace/source dependency.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Search accounting, one-axis authorization, and family budgets: sibling factory accounting story.
- Judge evidence and promotion: lands in judge and decision work.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~10 files, under 800 changed LOC.

## Boundary Map
PRODUCES:
- factory/pyproject.toml -> separately locked gauntlet-factory project
- factory/src/gauntlet_factory/race.py -> run_race(candidate: CandidateDefinition, data: FrozenPopulation, profile: FactoryProfile) -> RaceResult
- src/gauntlet/factory/launcher.py -> launch_factory_race(command: FactoryCommand) -> FactoryArtifact

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-wa2q: src/gauntlet/ledger/trials.py -> append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult
  spec: append_trial(payload: TrialPayload, actor: Actor, previous_head: str | None) -> LedgerAppendResult

### Acceptance Criteria (story contract)
1. Core import graph contains no factory module or dependency; root `uv.lock` resolves only core NumPy 2.x.
2. Factory lock resolves `numpy==1.23.5` and a wrong-version lock fails before execution.
3. Factory runs only as a subprocess and communicates through content-hashed artifact files, never live numerical objects.
4. A candidate definition is complete, immutable, and registered before race execution.
5. Race output labels composite score, fallback engine, and VBT simplification as exploratory and includes score decomposition and lineage.
6. A primitive race result is not judge evidence until a selected candidate fingerprint is locked and passed to judge evaluation.
7. Both lockfiles are verified independently in CI without installing one environment into the other.

## Testing Requirements
- Unit: Test lock resolution, subprocess boundary, candidate schema, artifact hashes, and core import graph.
- Integration tests: MANDATORY (no mocks). Launch a real tiny factory subprocess on synthetic locked data, verify returned artifact hashes and exploratory labels, and import every core module to prove isolation.
- Commands to run: `uv run pytest tests/factory/test_isolation.py` and `uv --project factory run pytest factory/tests/test_race.py`.

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
- [ ] AC #1: Core import graph contains no factory module or dependency; root `uv.lock` resolves only core NumPy 2.x.
- [ ] AC #2: Factory lock resolves `numpy==1.23.5` and a wrong-version lock fails before execution.
- [ ] AC #3: Factory runs only as a subprocess and communicates through content-hashed artifact files, never live numerical objects.
- [ ] AC #4: A candidate definition is complete, immutable, and registered before race execution.
- [ ] AC #5: Race output labels composite score, fallback engine, and VBT simplification as exploratory and includes score decomposition and lineage.
- [ ] AC #6: A primitive race result is not judge evidence until a selected candidate fingerprint is locked and passed to judge evaluation.
- [ ] AC #7: Both lockfiles are verified independently in CI without installing one environment into the other.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:20Z dep_added: blocked_by VK-pg9j
- 2026-09-18T23:31:20Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:20Z dep_added: blocked_by VK-wa2q
- 2026-09-18T23:31:21Z dep_added: blocks VK-jbae
- 2026-09-18T23:31:36Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:40Z dep_added: blocks VK-ldg1
- 2026-09-19T03:17:05Z dep_removed: was_blocked_by VK-wa2q
- 2026-09-19T04:41:26Z dep_removed: was_blocked_by VK-jkkn

## Links
- Parent: [[VK-u40v]]
- Blocks: [[VK-jbae]], [[VK-dblr]], [[VK-ldg1]]
- Blocked by: [[VK-pg9j]]
- Was blocked by: [[VK-wa2q]], [[VK-jkkn]]

## Comments
