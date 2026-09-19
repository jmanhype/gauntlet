---
id: VK-0c4c
title: "Enforce walk-forward evaluation discipline"
status: open
priority: 1
type: feature
labels: [integration, phase-1, walking-skeleton]
parent: VK-0auj
created_at: 2026-09-18T23:31:22Z
created_by: speed
updated_at: 2026-09-19T01:37:43Z
content_hash: "sha256:ced226c2f6298f1a749389a62e2aa03534d625b96d4411942d4a9a9b25b6dbe5"
blocks: [VK-2g0f, VK-ddoh, VK-sbdy, VK-aumt, VK-dblr, VK-vqvy]
was_blocked_by: [VK-pg9j, VK-kmbs, VK-jkkn]
---

## Description
## USER INTENT
The owner needs selection separated from untouched evaluation so a candidate cannot be graded on data that chose it.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement walk-forward evaluation with train before validation, selection on validation, locked variant, and test only the following window; enter at the next bar. Inputs are frozen `solana.bars` and `solana.events` descriptors, candidate/model profile, split policy, and feature provenance. Emit `fold_manifest.json`, train/validation/test membership, locked selection, row-level test predictions and trades, and a run report. A sample may train or tune only when feature observation and target completion precede the boundary. Embargo/purge gaps, fold order, expanding-window policy, and selection locks are explicit. Factory race output remains exploratory until the selected fingerprint is locked.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Exact reserve pricing: sibling exact-execution story.
- Statistical panels: lab stories.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~8 files, under 750 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
- src/gauntlet/judge/splits.py -> build_split_manifest(policy: SplitPolicy, population: FrozenPopulation) -> SplitManifest

CONSUMES:
- VK-pg9j: src/gauntlet/audit/collectors/bitquery.py -> derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
  spec: derive_solana_tables(raw_snapshot: SnapshotDescriptor) -> DerivedVenueData
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-kmbs: src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
  spec: evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation

### Acceptance Criteria (story contract)
1. Fold manifest records UTC boundaries, bars, horizon, lookback, normalization window, target horizon, embargo/purge, fold order, and selection locks.
2. Validation selects one variant and the following test window is untouched by that selection.
3. A target crossing a boundary, future normalization, or post-outcome membership mutation fails.
4. Locked candidate fingerprint, feature provenance, config hash, source descriptor hashes, and selected fold are recorded.
5. Row-level predictions and trades include timestamps, venue, token, intended action, labels, and OBSERVED/MODELED basis.
6. Entering at the next bar is enforced and any gap or missing dependency yields BLOCKED, not an imputed fill.
7. A factory race can enter only after its selected fingerprint is locked; ranking score is not judge evidence.

## Testing Requirements
- Unit: Test split generation, boundary crossing, fold locks, entry timing, and row schema.
- Integration tests: MANDATORY (no mocks). Evaluate a real synthetic multi-fold population from registered descriptors and verify locked selections, untouched test membership, and complete row-level replay inputs.
- Commands to run: `uv run pytest tests/judge/test_walk_forward.py`.

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
- [ ] AC #1: Fold manifest records UTC boundaries, bars, horizon, lookback, normalization window, target horizon, embargo/purge, fold order, and selection locks.
- [ ] AC #2: Validation selects one variant and the following test window is untouched by that selection.
- [ ] AC #3: A target crossing a boundary, future normalization, or post-outcome membership mutation fails.
- [ ] AC #4: Locked candidate fingerprint, feature provenance, config hash, source descriptor hashes, and selected fold are recorded.
- [ ] AC #5: Row-level predictions and trades include timestamps, venue, token, intended action, labels, and OBSERVED/MODELED basis.
- [ ] AC #6: Entering at the next bar is enforced and any gap or missing dependency yields BLOCKED, not an imputed fill.
- [ ] AC #7: A factory race can enter only after its selected fingerprint is locked; ranking score is not judge evidence.

## Acceptance Criteria


## Design


## Notes
ANCHOR REPAIR: remove collector inversion from judge walking skeleton

GENERAL RULE SWEEP: No early-priority walking skeleton may be blocked by a lower-priority collector; collectors feed later real-data integration.

BOUNDARY REVISION (AUTHORITATIVE):
PRODUCES:
- src/gauntlet/judge/synthetic.py -> build_synthetic_population(seed: int, policy: SplitPolicy) -> FrozenPopulation

CONSUMES:
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-kmbs: src/gauntlet/data/dependency.py -> evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation
  spec: evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation

### Acceptance Criteria (repair revision)
1. The P1 walking skeleton generates and registers a deterministic synthetic solana_dex bars/events population locally; it has no Bitquery dependency and makes no network call.
2. Synthetic data is clearly labeled synthetic fixture evidence for wiring and is not promotable venue evidence.
3. Collector-derived descriptors bind only in later integration stories after the collector epic.

## nd_contract
status: new

### evidence
- Anchor repair applied 2026-09-18 after adversarial backlog rejection.
- Existing story ID and epic containment preserved; this append-only revision supersedes the conflicting original boundary sentence/dependency only.

### proof
- [ ] Repair AC #1: The P1 walking skeleton generates and registers a deterministic synthetic solana_dex bars/events population locally; it has no Bitquery dependency and makes no network call.
- [ ] Repair AC #2: Synthetic data is clearly labeled synthetic fixture evidence for wiring and is not promotable venue evidence.
- [ ] Repair AC #3: Collector-derived descriptors bind only in later integration stories after the collector epic.


## History
- 2026-09-18T23:31:22Z dep_added: blocked_by VK-pg9j
- 2026-09-18T23:31:23Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:23Z dep_added: blocked_by VK-kmbs
- 2026-09-18T23:31:23Z dep_added: blocks VK-2g0f
- 2026-09-18T23:31:24Z dep_added: blocks VK-ddoh
- 2026-09-18T23:31:25Z dep_added: blocks VK-sbdy
- 2026-09-18T23:31:27Z dep_added: blocks VK-aumt
- 2026-09-18T23:31:36Z dep_added: blocks VK-dblr
- 2026-09-18T23:31:42Z dep_added: blocks VK-vqvy
- 2026-09-19T01:37:43Z dep_removed: was_blocked_by VK-pg9j
- 2026-09-19T04:11:59Z dep_removed: was_blocked_by VK-kmbs
- 2026-09-19T04:41:26Z dep_removed: was_blocked_by VK-jkkn

## Links
- Parent: [[VK-0auj]]
- Blocks: [[VK-2g0f]], [[VK-ddoh]], [[VK-sbdy]], [[VK-aumt]], [[VK-dblr]], [[VK-vqvy]]
- Was blocked by: [[VK-pg9j]], [[VK-kmbs]], [[VK-jkkn]]

## Comments
