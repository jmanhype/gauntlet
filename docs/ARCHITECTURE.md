# GAUNTLET Architecture

Status: proposed architecture derived from owner-confirmed artifacts — `BUSINESS.md`
commit `c4a58ef`, `DESIGN.md` commit `1b1f5c5`, and `INTERFACE_DESIGN.md`

This document turns the approved business and design contracts into an
implementable Phase 1 architecture. It is subordinate to those documents. If a
future implementation or technical proposal conflicts with them, the approved
business/design contract wins and this architecture must be revised through a
versioned change.

## 1. Architecture forces and non-goals

GAUNTLET is a local, cadence-driven research system, not a latency-sensitive
trading service. Its governing quality is **prospective defensibility**: every
decision must be reconstructible from immutable local evidence and every failed
trial must remain attributable.

The architecture therefore optimizes in this order:

1. evidence integrity and replayability;
2. fail-closed dependency handling;
3. deterministic review and promotion semantics;
4. operator clarity through projections;
5. research throughput;
6. implementation simplicity.

Phase 1 explicitly excludes order placement, real-money exposure, public APIs,
long-running servers, multi-tenant access, and social claims. Paper or simulated
orders are evidence records, not executions.

## 2. System overview and control flow

The core assembly line is a directed, content-hashed evidence pipeline. Solid
arrows produce immutable artifacts; policy consumes artifacts only after they
are registered in the append-only ledger.

```text
               ┌────────────────────────────────────────────────┐
               │ collectors (audit / venue snapshots)           │
               │ append-only raw snapshots, no UI reads API      │
               └───────────────┬────────────────────────────────┘
                               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐
│ factory  │──▶│ judge    │──▶│ lab      │──▶│ gate     │──▶│ scoreboard │
│ GEPA/VBT │   │ WF/exact │   │ metrics  │   │ policy   │   │ projections│
└──────────┘   └──────────┘   └──────────┘   └────────────┘   └────────────┘
      ▲              ▲              ▲              ▲
      │              │              │              │
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐
│ model   │   │ risk     │   │ audit    │   │ ledger     │
│ Kronos  │   │ policy   │   │ roles    │   │ snapshots  │
└──────────┘   └──────────┘   └──────────┘   └────────────┘
```

A normal review follows this sequence:

1. A trial is registered before search or interpretation. Its immutable
   resolved configuration, hypothesis, axes, budgets, venue track, and data
   windows are written to the trial ledger.
2. Factory/model work generates candidate variants only on declared training
   and validation data.
3. Judge work locks the selected variant and evaluates a following test fold
   with venue-specific execution state. Untouched prospective paper records are
   appended before their outcomes are known.
4. Lab work independently computes calibration, effective evidence, dominance,
   robustness, reconciliation, and other required panels from immutable source
   artifacts.
5. The dependency-aware data layer marks unavailable or invalid critical inputs
   before policy evaluation.
6. The deterministic gate/policy engine produces a gate state and policy
   disposition. It never asks an agent to choose the verdict.
7. A Decision Snapshot persists the decision facts. Scoreboard and Evidence
   Cards are reproducible projections of that snapshot and its artifact graph.
8. Optional owner action is appended as a separate decision record; it never
   rewrites the computed gate.

## 3. Repository and runtime topology

Phase 1 is a Python/uv monorepo with one core package and seven bounded modules.
The module directory is the trust boundary; cross-module calls use typed
artifacts and registered manifest contracts rather than shared mutable objects.

```text
gauntlet/
  pyproject.toml                 # core project; NumPy 2.x lock
  uv.lock
  src/gauntlet/
    cli.py                       # Phase 1 CLI; thin wrapper over core services
    mcp.py                       # FastMCP spawned on demand; same verbs
    contracts/                   # schemas, canonical JSON, hashes, manifests
    ledger/                      # append-only ledger and events.jsonl
    data/                        # descriptors, dependency graph, quarantine
  policy/                      # deterministic gates and policy manifests
  judge/
  lab/
  model/
  audit/
      collectors/                # Bitquery, Hyperliquid, and Scarlett adapters
    risk/
    scoreboard/
  policies/                      # immutable policy and transition manifests
  profiles/                      # immutable run profiles
  data/                          # GAUNTLET_DATA_ROOT default/local artifacts
    raw/                         # append-only venue and external snapshots
      solana_dex/
      hyperliquid/
      external/
    evidence/                    # content-addressed derived artifacts
    decisions/                   # immutable Decision Snapshots
    reports/                     # regenerable static projections
  factory/
    pyproject.toml              # separately locked gauntlet-factory project
    uv.lock
    src/gauntlet_factory/       # NumPy 1.23.5 / VBT / GEPA candidate work
  tests/
```

`contracts`, `ledger`, `data`, and `policy` are supporting layers, not eighth
business modules. They provide shared guarantees while the seven named modules
remain responsible for domain behavior.

## 4. Module boundaries and artifact contracts

Each PRODUCES row is immutable once registered. A CONSUMES reference must name
an artifact ID/content hash or a validated append-only stream, never an
in-memory value from another module. Unknown or unregistered inputs are
gate-critical failures.

### 4.1 `judge/` — walk-forward and execution referee

**Responsibility**

Own temporal evaluation and realistic venue-specific execution. It extracts the
proven discipline from `walk_forward_validate.py`, `exact_quote_backtest.py`,
and `paper_trade_harness.py`: train before validation, select on validation,
lock the variant, test only the following window, enter at the next bar, and
quote Solana fills against contemporaneous AMM reserve state.

It is deliberately hostile to claimed winners. It does not invent candidates and
does not decide policy. It emits enough row-level detail for every downstream
metric to be independently recomputed.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| Walk-forward run | `fold_manifest.json`, train/validation/test membership, locked selection, row-level test predictions and trades, run report | Frozen `solana.bars` and `solana.events` descriptors produced by `audit/collectors/bitquery.py`, candidate/model profile, split policy, feature provenance |
| Exact Solana execution | Trade-level entry/exit reserve hashes, exact constant-product quotes, fee/impact/latency/fill-failure scenarios, invalid-quote counts | Locked walk-forward trades and event-level AMM reserve snapshots |
| Prospective paper stream | Pre-outcome signal records, later resolved records, open/skipped/failure reasons, immutable status transitions | Frozen model/candidate manifest, append-only venue snapshots, prospective policy |
| Transfer test | Separate Hyperliquid evaluation artifacts and execution assumptions | Solana candidate fingerprint and frozen Hyperliquid transfer population |

Non-overlapping one-position-per-token execution is an exploratory simplification.
When overlap is allowed, raw trade count cannot be used as effective independent
evidence; the effective-evidence manifest and `lab/` panel must disclose and
account for the overlap.

### 4.2 `factory/` — candidate invention and racing

**Responsibility**

Adapt the GEPA prompt optimizer, Three Gulfs discipline, feature extraction, and
VectorBT racing loop from `multi-agent-system`. It proposes and races variants;
it never assigns promotable status.

The historical Sharpe 3.8 failure is an architectural constraint: factory
scoring can rank research candidates but cannot define the business gate. Its
composite score, fallback engine, and any VBT execution simplification are
labeled exploratory and recorded as versioned trial axes.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| Candidate definition | Strategy family, prompt/module lineage, features, parameters, search space, execution assumptions, seed | Registered hypothesis, one-axis or owner-approved multi-axis exception, immutable training population |
| Race result | Variant ranking, score decomposition, signals, primitive trade/equity artifacts, engine identity/fallback disclosure | Declared bars/features, risk sizing profile, factory profile |
| Search accounting | Every attempted variant, evaluation count, changed axis, parent lineage, budget consumption | Ledger family entry and budget |

Factory code must remain import-isolated from the core environment. A primitive
race result is not judge evidence until the selected candidate fingerprint is
locked and passed to `judge/`.

Concretely, `factory/` is a separately locked `gauntlet-factory` project, not an
optional extra in the core lock. The core runtime uses
`numpy>=2.0,<3.0`; the factory runtime uses `numpy==1.23.5`. The core CLI
launches factory work only as a subprocess using that project's lock (for
example `uv --project factory run ...`) and receives content-hashed artifact
files. Neither project imports the other's numerical stack.
The root project must not map `factory` as a uv workspace/source dependency, and
the root lock must contain no factory or NumPy 1.23.5 resolution. CI verifies
the two lockfiles independently.

### 4.3 `lab/` — independent evidence mathematics

**Responsibility**

Provide deterministic, testable scoring kernels adapted from
`jev-dspy-lab/metrics.py` and the proven Scarlett calibration scripts. It owns
recomputation, calibration, uncertainty, multiplicity, effective evidence,
concentration, regime coverage, and claim-versus-realized reconciliation.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| Calibration panel | Brier, ECE, reliability bins, threshold sweep, coverage/selective-risk, gated-vs-ungated/abstain comparison | Decision/confidence records with immutable outcomes and confidence semantics |
| Effective-evidence panel | Raw count, overlap window, serial treatment, clustering keys, effective observation calculation and version | Row-level trades/labels, declared token/regime/cluster policy |
| Robustness panel | Bootstrap/equivalent uncertainty, PSR/DSR/PBO/FDR/equivalent diagnostics, declared omissions and reasons | Locked evaluation trades, trial lineage, statistical policy |
| Dominance panel | Contribution/removal effects for trade, token, cluster, regime, venue, variant, execution artifact | Row-level returns and complete lineage |
| Reconciliation report | Claim source, recomputation source, differences, tolerance, verdict | External or historical claims and independently recomputed metrics |

Lab functions are pure where practical. They do not fetch data, choose policy,
or mutate evidence.

### 4.4 `model/` — Kronos model and adaptation registry

**Responsibility**

Contain Kronos tokenizer/model inference and fine-tuning adapters derived from
`Kronos/model` and `Kronos/finetune`. The model is a versioned information
source, not an oracle: every probability, path share, confidence, or forecast
used in a decision must subsequently pass the same calibration panel as any
other decision signal.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| Model registry entry | Base/fine-tuned checkpoint hashes, architecture/config, training and domain window, license/provenance, hardware, seeds | Immutable source data and model profile |
| Inference artifact | Point-in-time context bounds, sampling parameters/sample count, generated paths, probabilities/path shares, model fingerprint | Frozen context, model registry entry, model profile |
| Adaptation run | Dataset manifests, normalization statistics, train/validation/test windows, checkpoint and logs | Frozen temporal splits and data descriptors |

Instance/window normalization must use only the lookback portion, as in the
Kronos dataset implementation. Checkpoint bytes and preprocessing code/config
hashes are required for replay.

### 4.5 `audit/` — collection, external claims, and role isolation

**Responsibility**

Own all outbound collection through `audit/collectors/`, plus external-claim
verification. `bitquery.py` owns Solana DEX discovery snapshots and their raw →
bars/events transformations; `hyperliquid.py` owns Hyperliquid transfer-population
market/order snapshots and their venue-derived tables; Scarlett collectors are
adapted from `scarlett_snapshot.py`, `scarlett_calibration.py`, and
`validate_anti_scarlett.py`. `audit/collectors/` is the only Phase 1 component
allowed to call external APIs; report/MCP/CLI consumers read local snapshots.

Scarlett can be benchmark, candidate/information source, or audit target, but
never two roles for the same decision without an explicit contamination analysis
and a replacement benchmark.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| Bitquery raw snapshot | Immutable request/response pages, cursors, watermark, retry/backoff map, API-cost event, content hash | Local owner-approved Bitquery credential, versioned collector policy, family/API budget |
| Bitquery derived data | `solana.bars` and `solana.events` descriptors + Parquet partitions, transformation manifest, quality/freshness/criticality declarations | Registered raw snapshot descriptors and versioned cleaning code/config |
| Hyperliquid raw snapshot | Immutable paginated market/order responses, cursors, watermark, retry/backoff map, API-cost event, content hash | Local credential if required, versioned collector policy, family/API budget |
| Hyperliquid derived data | `hyperliquid.bars`, `hyperliquid.order_book`, and other declared transfer tables/descriptors with transformation provenance | Registered raw snapshot descriptors and versioned transform code/config |
| Scarlett/external snapshot | Raw paginated response, request metadata (without credentials), collector/version, fetch time, content hash | Rate-limited external API and versioned collector policy |
| Collection health | Duplicate/deduplication report, partial-capture state, API-cost/budget state, failure/quarantine events | Collector policy, event ledger, descriptor registry |
| Claim decomposition | Claimed metric/capability, source, actual model/process identity, decision role, materiality tolerance | Immutable snapshots and historical artifacts |
| Audit reconciliation | Independent recalculation, outcome data, differences, verdict | Claim record and relevant lab kernel |
| Role declaration | Role enum, permitted uses, contamination constraints | Trial/family manifest |

Collector execution rules are mandatory:

- credentials are injected only into the collector process, never accepted as
  CLI/MCP arguments, and never copied into payloads, events, reports, exports,
  or hashes;
- pagination records every cursor, page hash, terminal condition, and source
  watermark;
- requests use bounded exponential backoff for transient failures and record
  429/Cloudflare/rate-limit behavior without retry storms;
- estimated and actual API cost append budget events before and after capture;
  an exhausted or unauthorized budget fails before additional spend;
- duplicate detection keys on collector identity, normalized request, cursor,
  source watermark, and payload hash; an exact redownload is retained as an
  immutable duplicate observation rather than silently replacing an older page;
- raw-to-derived registration is atomic enough to fail closed: a capture is not
  marked complete until every page and descriptor is present and verified;
- partial capture, truncation, malformed data, unexplained cursor regression, or
  checksum failure creates a new quarantined descriptor version for that capture
  scope and blocks dependent gates; it never overwrites the original snapshot;
- a failed request with no accepted payload appends a failure event and leaves
  prior descriptors unchanged.

`judge/` is not a collector. It consumes frozen `solana.bars` and
`solana.events` descriptors explicitly produced by `audit/collectors/bitquery.py`.

### 4.6 `risk/` — portfolio policy kernel

**Responsibility**

Own versioned portfolio sizing, exposure, drawdown, concentration, correlation,
circuit-breaker, and operating-boundary checks derived from the battle-tested
QTS limits. Risk can stop or constrain paper research, but it cannot convert an
evidence failure into promotion and positive research evidence cannot override a
risk boundary.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| Risk policy version | Canonical limits, semantics, venue applicability, lineage from imported QTS config | `policies/risk/qts.risk@vN.json` |
| Sizing/check result | Requested and approved size, checks, adjusted size, warnings, policy version | Candidate request, paper portfolio state, market context |
| Boundary event | Limit/breaker state, duration, reason, affected track | Append-only paper/portfolio ledger |

Portfolio risk is a separate policy domain. A risk breach may trigger a stop,
hold, or quarantine disposition, but it does not implement the evidence rules and
an evidence PASS does not authorize real-money exposure.

### 4.7 `scoreboard/` — non-authoritative projections

**Responsibility**

Build Scoreboard views, Evidence Cards, Forensic Views, deltas, and self-contained
audit exports from Decision Snapshots and registered artifacts. It never owns
decision state and cannot recompute a verdict with new policy while presenting it
as the historical result.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| Scoreboard projection | Action Required, Blocked/Quarantined, Killed, Archived, Recently Changed, budget/status states | Latest valid snapshots, policy enumerations, dependency state |
| Evidence Card projection | Every normative DESIGN field or labeled mandatory drill-down, gate arithmetic, delta, next action | Immutable snapshot and provenance graph |
| Forensic bundle | Source artifacts, transformation records, replay checks, diagnostics, hashes | Decision snapshot and run manifests |
| Static report | Markdown/HTML + JSON file with accessible textual states | Scoreboard/card projections |

All projections are deterministic for a snapshot ID and can be deleted and
regenerated without losing decisions.

## 5. Append-only experiment/trial ledger

### 5.1 Storage format

The live trial system of record is canonical JSONL:

```text
data/ledger/trials.jsonl
data/ledger/events.jsonl
data/ledger/trial-head.json       # regenerable compact head pointer
```

Every physical write opens the destination exclusively and refuses overwrite.
Output directories likewise refuse to replace a non-empty run. These checks are
detectable, not cryptographic denial-of-service protection; the ledger is also
periodically copied to durable backup/Git storage.

A trial entry has a stable envelope and a typed payload:

```json
{
  "schema_version": "1",
  "entry_type": "trial.registered",
  "trial_id": "trial_...",
  "family_id": "family_...",
  "venue_track": "solana_dex",
  "recorded_at_utc": "...",
  "actor": {"kind": "human|agent|collector", "identity": "..."},
  "payload_hash": "sha256:...",
  "previous_head_hash": "sha256:...",
  "entry_hash": "sha256:...",
  "payload": {}
}
```

`payload_hash` hashes canonical payload JSON. `entry_hash` hashes the canonical
envelope with `entry_hash` omitted and `previous_head_hash` included. A verifier
recomputes every hash and head chain. Rewriting or deleting an old line breaks
the chain and invalidates later decisions that cannot be reconstructed from an
independent durable backup.

Content-addressed payloads too large for JSONL live under
`data/evidence/sha256/<aa>/<full-sha>/`; the ledger stores only their hash and
storage-relative path. These files are write-once. Derived indexes, queues, and
other lookup projections use only Parquet partitions, canonical JSON/JSONL, or
in-memory structures loaded from those files. Phase 1 has **no database engine
dependency of any kind**, including SQLite; every projection is fully
regenerable from immutable source artifacts.

### 5.2 Required trial payload

Every `trial.registered` entry records the full BUSINESS contract before outcome
interpretation:

- hypothesis and success/failure interpretation;
- strategy family and parent/ancestor relationships;
- venue track and requested transfer hypothesis, if any;
- data window, split manifest hash, source descriptor hashes, and frozen status;
- feature manifest and preprocessing/version hashes;
- parameters and full search space, including variants intentionally attempted;
- execution assumptions and versioned adverse scenarios;
- benchmark identity and benchmark role;
- family trial/compute/data budgets and stop condition;
- one-axis declaration or owner-approved multi-axis exception and attribution plan;
- policy/risk/evaluation versions;
- resolved configuration hash;
- declared dependencies and gate criticality.

Outcome entries are appended separately (`trial.result`, `trial.rejected`,
`trial.promoted`, `family.stopped`, `owner.exception`, and so on). They never
modify the registration payload. Status transitions record actor, reason,
timestamp, from/to state, evidence version, and policy version.

### 5.3 Trial-history accounting in gates

The gate engine does not accept a candidate-selected metric as an isolated
number. It consumes a precomputed lineage summary derived only from immutable
ledger entries:

- total related trials and failed ancestors;
- parameter/threshold variants and search-space evaluations;
- changed experimental axes and owner-approved exceptions;
- family budget consumption and stop/renewal state;
- selection history across walk-forward folds;
- risk-parameter versions;
- multiplicity inputs and deflation/PBO/FDR accounting;
- venue/role contamination declarations.

Missing, broken, or unverifiable lineage is gate-critical and yields `BLOCKED`.
A valid lineage with insufficient effective observations yields
`INSUFFICIENT_EVIDENCE`; a valid lineage that disproves a threshold yields
`FAIL`. Exhausted family budget can produce a family policy disposition
independently of the candidate gate, but the recorded gate calculation remains
unchanged.

## 6. Decision Snapshot store and provenance

### 6.1 Immutable snapshot layout

Each consequential decision creates a content-addressed, write-once directory:

```text
data/decisions/<decision_id>/
  snapshot.json          # exact decision facts and artifact graph
  manifest.json          # file hashes and snapshot Merkle root
  evidence/              # or content-addressed references
  policy/
  projections/           # optional cached Evidence Card output
```

`snapshot.json` includes the separate DESIGN facts: evidence set/version,
inspectable gate calculation, gate state, policy disposition and version,
advisory recommendation and visibility state, owner decision slot, review mode,
ordered reveal log, artifact versions, delta from the prior snapshot, dependency
health, recommendation model/agent version, and relevant hashes. The snapshot is
the system of record; UI and reports are projections.

The snapshot manifest hashes every embedded file and records the content hash
and storage-relative path of every external artifact. A snapshot verification
failure blocks promotion, export approval, and later decisions that depend on it.

### 6.2 Provenance chain

Every displayed evidence claim reaches the following chain:

```text
ledger entry
  → source data/artifact content hash
    → resolved configuration + policy/model/code versions
      → deterministic transformation manifest
        → producing run manifest and output artifact
          → lab panel
            → gate input
              → Decision Snapshot
```

A transformation record names its implementation module and code version, input
hashes, output hashes, environment/dependency lock hash, seeds, venue/timezone,
and complete CLI/resolved configuration. Replay compares a new output hash or,
where nondeterministic model sampling is allowed, a declared deterministic seed
and tolerance.

Reconstruction starts only from the snapshot manifest, never from current mutable
UI state. Missing source bytes, configuration, model checkpoint, code version, or
dependency definition make the snapshot non-replayable and the affected gate
`BLOCKED`.

### 6.3 Evidence Cards and audit export

Evidence Cards render the normative DESIGN fields or a labeled one-action
drill-down. Missing mandatory evidence is visible and blocks; it is never
omitted. A card links the delta, next action and current distance, concentration
and robustness panels, dual temporal status, calibration, integrity/quarantine,
lineage/budgets, and gate arithmetic.

`export_audit_bundle` copies or content-addresses all referenced artifacts into a
self-contained directory with the snapshot, reveal log, policy versions, code
manifest, provenance graph, and verification report. The export itself is
append-only and receives a bundle manifest and Merkle root.

## 7. Dependency-aware, fail-closed data layer

### 7.1 Evidence descriptor

No dataset participates in a gate as a bare path. Each raw snapshot, derived
table, model output, external claim, benchmark, configuration, and policy is
registered with a versioned descriptor:

```json
{
  "descriptor_schema": "gauntlet.evidence.v1",
  "artifact_id": "...",
  "descriptor_id": "...",
  "descriptor_version": 2,
  "descriptor_hash": "sha256:...",
  "supersedes_descriptor_hash": "sha256:...",
  "effective_at_utc": "...",
  "superseded_at_utc": null,
  "kind": "bars|events|reserves|forecasts|trades|panel|claim|config|model",
  "venue_track": "solana_dex|hyperliquid|external|cross_venue_transfer",
  "content_hash": "sha256:...",
  "source": {"collector": "...", "request": "...", "uri_or_lineage": "..."},
  "observation_basis": "OBSERVED|MODELED",
  "coverage": {"start": "...", "end_exclusive": "...", "tokens": "policy-ref"},
  "freshness": {"watermark_at": "...", "max_age": "...", "as_of": "..."},
  "quality": {"checks": [], "state": "VALID|STALE|CORRUPT|INCOMPLETE|QUARANTINED"},
  "dependencies": [{"artifact_id": "...", "relation": "requires"}],
  "criticality": "GATE_CRITICAL|NON_CRITICAL|UNKNOWN",
  "downstream_metrics": ["expectancy", "calibration.ece"]
}
```

Descriptors are immutable, ledgered, and content-hashed. A correction, quality
transition, or quarantine never edits an existing descriptor: it creates a new
descriptor version whose `supersedes_descriptor_hash` names the original and
whose `effective_at_utc` is the ledger event time. The prior version records
only its later `superseded_at_utc` through an event-sourced index projection;
its bytes are never changed. A derived artifact must reference the exact
descriptor hashes used to create it.

### 7.2 Versioned dependency graph

The evaluator materializes a directed graph from descriptor dependencies and
computes closure for each gate input. It evaluates in this order:

1. content hash and schema validity;
2. source/provenance reachability;
3. freshness at the declared decision `as_of`;
4. declared quality checks;
5. dependency health, recursively;
6. `OBSERVED`/`MODELED` eligibility for the metric;
7. criticality classification.

Criticality is not inferred at review time. It comes from the versioned evidence
policy. `UNKNOWN` is fail-closed and equivalent to gate-critical until a policy
version explicitly classifies the input.

### 7.3 Blocking and quarantine

Gate-critical missing, stale, corrupt, incomplete, replay-failed, or
unknown-criticality evidence marks dependent metrics `INVALID` and the gate
`BLOCKED`. No owner exception can promote through `BLOCKED`; the dependency must
be repaired and the gate recomputed.

Explicitly noncritical evidence may be absent without invalidating unaffected
metrics, but the Evidence Card must prominently show reduced coverage and the
missing dependency. Silent forward-fill, interpolation, substitution, or
imputation is prohibited for gate inputs.

Quarantine is represented by append-only state, not destructive relocation:

1. collector or evaluator detects a defect;
2. a quarantine event records scope, reason, affected artifacts/trials/gates,
   and actor;
3. the quarantine event references the exact original descriptor hash and
   produces a new immutable descriptor version with
   `quality.state=QUARANTINED` and `supersedes_descriptor_hash` pointing to that
   original;
4. affected projections and candidates are visibly quarantined;
5. repair creates new descriptors and runs rather than mutating the defective
   payload;
6. owner `RELEASE` requires repaired dependencies, automatic forensics, and a
   recomputed gate.

Descriptor selection is time-bound. Gate evaluation and snapshot reconstruction
resolve the descriptor version active at the operation's recorded `as_of`:
`effective_at_utc <= as_of` and, when present,
`superseded_at_utc > as_of`. A run manifest that already binds an exact
descriptor hash always uses that hash. Historical snapshots therefore continue
to reconstruct the population and quality state they recorded, even after a
later quarantine, correction, or repair.

### 7.4 MODELED versus OBSERVED

`OBSERVED` means a value was collected from a venue, external system, source
artifact, or realized outcome without research-layer substitution. `MODELED`
means produced by GAUNTLET simulation, estimation, normalization, model
forecast, fill scenario, or imputation permitted only outside gate metrics.

Every row and aggregate carries this label. A `MODELED` value cannot populate a
rule whose contract requires observed outcomes, realized reserve/order-book
state, realized fills, external claims, or untouched prospective evidence.
Composite scenarios may combine labels only if each component label and formula
is inspectable.

## 8. Data governance and reproducibility

### 8.1 Temporal populations and leakage boundaries

Every trial declares one temporal split manifest:

- UTC timestamps, bars, horizon, feature lookback, normalization window, and
  target horizon;
- train, validation, test, prospective, and frozen windows;
- embargo/purge gap at each boundary;
- walk-forward fold order and expanding-window policy;
- selection locks and test interpretation policy.

A sample may train or tune only if both its feature observation time and target
completion time are before the boundary. Validation selects a variant; the
following test window remains untouched by that selection. Feature statistics
and model normalization use only information available at prediction time.
Checkpoint selection is governed by the training/validation boundary, not test
performance.

Frozen evaluation sets are content-addressed. Once registered for a trial, their
membership, source hashes, and split policy cannot change. Later corrections
create a new trial and preserve the invalid population.

### 8.2 Untouched prospective evidence

Before an outcome can be known, the prospective recorder appends:

- candidate/model/config/policy fingerprints;
- signal timestamp and all information available then;
- intended action, notional, horizon, and execution assumptions;
- confidence/path share and its semantics;
- dependency snapshot and status.

The record is hash-chained and immutable. Outcomes are appended later with the
venue state used to resolve them. Backfilling a signal after observing its label
is labeled historical, not prospective, and can never satisfy dual temporal
evidence.

### 8.3 Overlap, clustering, and regime handling

Raw resolved trades and effective independent observations are always reported
separately. The versioned effective-evidence policy declares:

- label/trade overlap window and overlap reduction algorithm;
- serial-dependence model or conservative treatment;
- token identity, correlated-token clustering method/threshold/window, and
  whether cluster definitions were frozen before outcomes;
- regime taxonomy, point-in-time features used for assignment, and required
  coverage;
- venue, strategy variant, family, and time-block grouping;
- how raw observations reduce to the effective count.

Clustering may not reuse post-outcome returns unless the method and freeze time
are explicit and included in replay. Effective evidence may be adaptive upward;
it can never turn a required regime gap or unresolved overlap into `PASS`.

### 8.4 Venue-specific execution state

Solana DEX fills require an event-level pool/reserve state at or before the
simulated order, exact constant-product quote math, explicit fee assumptions,
and a documented alignment rule. Missing or invalid reserve state is a failed
quote/evidence gap, not a fill. Price-only Solana results remain exploratory.

Hyperliquid transfer tests use Hyperliquid market/order-book mechanics, fees,
latency, failure modes, and benchmarks. A source fingerprint may transfer as a
hypothesis; Solana evidence and Hyperliquid evidence remain separate populations.

### 8.5 Replay contract

A replay run resolves the same code version, dependency lock, source hashes,
model checkpoints, feature/preprocessing version, seeds, sampler settings,
configuration, venue/timezone, and policy versions. It writes to a new run
directory and compares output hashes. Sampling-based models require fixed seeds
and sample counts or a pre-declared statistical tolerance. Replay reports are
retained; success/failure is a data-integrity input.

## 9. Deterministic gate and policy engine

### 9.1 Rule result semantics

Rules return one of:

- `PASS` — all required inputs valid and threshold satisfied;
- `FAIL` — inputs valid and threshold not satisfied;
- `BLOCKED` — required dependency missing/invalid, replay failed, lineage broken,
  or required evidence structurally unavailable;
- `PENDING` / `INSUFFICIENT_EVIDENCE` — inputs are valid but the declared window,
  sample, or effective observation requirement is not yet complete.

Aggregate precedence is fixed and independent of rule order:

```text
any BLOCKED                    → BLOCKED
else any FAIL                  → FAIL
else any PENDING or INSUFFICIENT→ INSUFFICIENT_EVIDENCE
else                            → PASS
```

The engine is a pure function of `(evidence_bundle, ruleset_manifest,
policy_manifest, dependency_state, as_of)`. It does not read wall-clock time,
query current data, call an LLM, or infer thresholds. Unknown rule outputs are
converted to `BLOCKED`.

### 9.2 Versioned immutable manifests

Gate and policy capabilities are independently versioned:

- `evidence-policy@vN` — required panels, input kinds, criticality, freshness;
- `gate-rules@vN` — rule IDs, formulas, operators, thresholds, and precedence;
- `disposition-policy@vN` — gate/state-to-owner-action mapping;
- `transitions@vN` — enumerated major transitions and forensic requirements;
- `effective-evidence@vN` — overlap/cluster/serial calculation;
- `alert-policy@vN` — materiality and interruption classifications;
- `risk-policy@vN` — portfolio limits, semantically separate.

Each manifest has a canonical JSON content hash, schema version, creator, created
time, changelog, and status. Once referenced by a trial or snapshot it is
immutable. Policy additions are new versions; old decisions are always
interpreted under their original manifest hashes.

### 9.3 Inspectable calculation

Every rule result records:

- rule ID, formula ID, and ruleset/policy versions;
- artifact ID and hash for each material input;
- numeric observed value, comparator, and threshold;
- effective-evidence calculation reference;
- `OBSERVED`/`MODELED` labels where material;
- per-rule state and reason;
- policy disposition derivation.

The aggregate exposes the exact precedence branch selected. An Evidence Card can
show the full arithmetic directly or one action deep, but cannot summarize away
rule identifiers, inputs, or failed checks.

### 9.4 Resolved configurations

Every run resolves defaults, profile, CLI/MCP overrides, environment-independent
research values, artifact versions, and hashes into one canonical configuration.
`--show-config` prints it; `--diff-config` compares it to a profile or prior run.
A hidden research-critical default is a defect. Runtime paths and secret names
may be redacted, but the redaction rule itself is versioned and never changes a
research threshold.

## 10. Venue separation and Scarlett role isolation

### 10.1 Isolated evidence tracks

`venue_track` is part of ledger, dataset, trial, candidate, execution, benchmark,
and snapshot identity.

| Track | Purpose | Evidence effect |
|---|---|---|
| `solana_dex` | Primary discovery population | Only Solana DEX trades/reserves contribute to discovery gates |
| `hyperliquid` | Mirror, benchmark, and transfer testing | Separate population, mechanics, and frozen evaluation sets |
| `cross_venue_transfer` | Explicit transfer hypothesis | Tests a frozen source fingerprint on Hyperliquid; neither population is pooled |
| `external` | Scarlett/audit snapshots | Claim evidence or benchmark under declared role, never silently mixed |

Track boundaries are enforced at descriptor, artifact, metric, and gate layers.
Aggregate venues may be shown only as side-by-side panels with separate counts
and assumptions; they cannot supply the effective observation count for a
single-venue candidate gate.

### 10.2 Transfer testing

A transfer trial records the exact Solana candidate fingerprint, why transfer is
plausible, frozen Hyperliquid window, adaptation permitted (none, recalibration,
or retraining), benchmark, and execution model. Any Hyperliquid adaptation is a
new trial with lineage to the source. Success establishes only the declared
transfer hypothesis; it does not retroactively strengthen the Solana discovery
population.

### 10.3 Scarlett recorder and role enforcement

The recorder snapshots profiles, markets, forecasts, and setups with pagination,
rate-limit/backoff metadata, collector version, and fetch time. It never merges
duplicate IDs by recency silently: snapshot provenance and merge policy are
recorded so calibration inputs remain reconstructible.

For each trial/family, audit emits a role declaration:

| Role | Permitted use | Conflict |
|---|---|---|
| Benchmark | Independent comparison only | Cannot contribute signal to candidate |
| Candidate/information source | Candidate feature/forecast with model lineage and calibration | Cannot be benchmark for that candidate |
| Audit target | Claim decomposition and reconciliation | Cannot become evidence of candidate edge without separate candidate trial |

A contamination check walks the provenance graph before major transitions and
blocks if the same Scarlett artifact serves incompatible roles without an
approved, explicit redesign and replacement benchmark.

## 11. Interface architecture

### 11.1 One core, thin wrappers

CLI and FastMCP import the same service functions. Neither wrapper owns policy,
state, storage formats, or evaluation logic. A Phase 1 invocation runs and exits;
FastMCP is spawned by an AI client and is not installed as a daemon.

| Surface | Phase 1 behavior |
|---|---|
| `gauntlet collect` | Runs approved collectors and appends local snapshots/events |
| `gauntlet audit` | Records/reconciles external claims from local snapshots |
| `gauntlet gate` | Materializes dependencies, evaluates deterministic rules, writes snapshot |
| `gauntlet factory` | Registers and runs isolated candidate search/races |
| `gauntlet tournament` | Runs registered candidates through judge/prospective tracks |
| `gauntlet scoreboard` | Regenerates current projections |
| `gauntlet report` | Writes static Markdown/HTML/JSON files under `data/reports` |
| `gauntlet review/forensic/decide/export` | Expose Decision Snapshot operations |
| FastMCP tools | Same verbs and JSON contracts, spawned on demand |

All wrappers accept `--json`, `--no-color`, and ASCII fallback. They read local
snapshots; only collectors make network calls.

### 11.2 Minimum core service API

CLI and FastMCP must call exactly these typed services. Wrappers do not write
ledger/storage directly and cannot bypass an error contract. Each call receives
a common envelope containing operation, structural capability context,
canonical arguments, requested `as_of`, and either an immutable resolved-config
hash or a profile-plus-explicit-overrides form to resolve first. Research- or
state-mutating services reject an incomplete or hidden-value configuration.

Every result carries `OK` or `ERROR`, service version, input hashes, output
hashes, event head, and a machine-readable error code/message. Error events are
appended even when no artifact is produced.

| Service | Required inputs | Required outputs / effects | Error states |
|---|---|---|---|
| `register_trial` | Hypothesis, family, venue track, strategy family, axes/exception state, source descriptor hashes, split/feature/execution/benchmark/risk references, budgets, profile + overrides | Canonical `ResolvedConfig` + hash; immutable `trial.registered` entry; trial/family IDs; descriptor bindings | `CONFIG_INVALID`, `SOURCE_DESCRIPTOR_MISSING`, `LINEAGE_INVALID`, `MULTI_AXIS_UNAUTHORIZED`, `BUDGET_EXHAUSTED`, `DUPLICATE_TRIAL`, `LEDGER_CONFLICT` |
| `evaluate_dependencies` | Descriptor IDs or evidence-set ID, `as_of`, evidence-policy hash, required metric/rule set | Selected descriptor-version hashes, graph hash, freshness/quality closure, criticality result, affected metrics, coverage, quarantine state | `POLICY_HASH_INVALID`, `DESCRIPTOR_UNVERIFIED`, `GRAPH_MALFORMED`; a resolvable but failed check returns `BLOCKED` in the evaluation result, not a command crash |
| `evaluate_gate` | Trial/candidate ID, dependency-evaluation hash, required panel artifact hashes, gate-rules/policy hashes, `as_of` | Per-rule inputs/results/reasons, aggregate state under fixed precedence, disposition, inspectable calculation artifact | `PANEL_CONTRACT_INVALID`, `ARTIFACT_HASH_MISMATCH`, `POLICY_INCOMPATIBLE`, `DEPENDENCY_EVALUATION_STALE`; structurally unavailable required evidence becomes rule `BLOCKED` |
| `write_decision_snapshot` | Valid gate result, evidence bundle refs, recommendation/review mode/ordered reveal log, capability context, current event head | Immutable Decision Snapshot ID/hash + manifest; no owner decision is implied | `ACTOR_CONTEXT_INVALID`, `GATE_RESULT_INVALID`, `REVEAL_LOG_INVALID`, `EVENT_CHAIN_INVALID`, `SNAPSHOT_EXISTS` |
| `record_owner_decision` | Locally signed owner action envelope, exact subject snapshot/gate hashes, decision vocabulary, reason, policy/reveal references, nonce | Write-once `owner-decisions/<action-id>.json` extension linked to original snapshot; original snapshot hash unchanged | `AUTHORIZATION_DENIED`, `SIGNATURE_INVALID`, `KEY_UNKNOWN`, `NONCE_REPLAY`, `SUBJECT_HASH_MISMATCH`, `DECISION_NOT_PERMITTED`, `FORENSICS_REQUIRED`, `POLICY_VERSION_MISMATCH` |
| `project_evidence_card` | Snapshot ID/hash, projection policy/version, output format, drill-down policy | Deterministic Evidence Card JSON/Markdown projection hash; all mandatory fields or explicit blocked/missing labels | `SNAPSHOT_VERIFICATION_FAILED`, `PROJECTION_POLICY_INVALID`, `FORMAT_UNSUPPORTED`; a valid snapshot with missing source coverage projects `BLOCKED`, not a synthetic metric |
| `export_audit_bundle` | Snapshot hash, bundle policy/version, artifact selection, destination policy | Self-contained immutable bundle path/ID, Merkle root, verification report | `ARTIFACT_MISSING`, `VERIFICATION_FAILED`, `DESTINATION_NOT_EMPTY`, `BUNDLE_POLICY_INVALID` |

`resolve_config` is the shared helper used before these services. It records
profile hash, defaults, explicit CLI/MCP overrides, artifact/policy versions,
and code/environment hashes; `--show-config` and `--diff-config` call it without
running research. Interface-parity tests compare CLI and MCP outputs and ledger
events for every successful and representative error path.

Successful service calls emit `trial.registered`, `dependency.evaluated`,
`gate.evaluated`, `snapshot.written`, `owner.decision.recorded`,
`evidence_card.projected`, and `audit_bundle.exported`, respectively. Failed
calls emit the same operation verb with `status=ERROR`, error code, subject, and
input/output hashes, without inventing an artifact.

### 11.3 Operation trace

Every autonomous or interface operation appends canonical JSONL to
`data/ledger/events.jsonl`. Like the trial ledger, the event stream is
hash-chained and append-only:

```json
{
  "event_id": "stable-random-or-ulid",
  "schema_version": "1",
  "timestamp_utc": "...",
  "actor": {"kind": "human|agent|collector", "identity": "..."},
  "verb": "gate.evaluate",
  "subject": "candidate/track/artifact id",
  "args_hash": "sha256:...",
  "output_hash": "sha256:...",
  "payload_hash": "sha256:...",
  "previous_head_hash": "sha256:...",
  "event_hash": "sha256:...",
  "status": "OK|ERROR",
  "error_class": null,
  "trace": {"run_id": "...", "span_id": "..."}
}
```

`payload_hash` covers the event body without integrity fields;
`previous_head_hash` names the prior event hash; `event_hash` covers the
canonical envelope with `event_hash` omitted. Appends are serialized under the
local ledger lock, and a regenerable `events-head.json` records the current
head and byte range.

Every consequential trial, dependency, gate, snapshot, collector, or owner
operation also anchors the current event head in its trial-ledger or snapshot
manifest entry. For an operation with no trial entry, the service appends a
periodic `events.anchor` entry referencing the event head. Verification recomputes
both chains and rejects any missing, reordered, rewritten, or unanchored head.

The trace is evidence of action, not a replacement for the trial ledger or
Decision Snapshot. It never contains secret values, full external payloads,
signatures, private owner material, or unredacted credentials. Authorization
failure events record only the verifier, key ID when supplied, failure class,
subject, and nonce/timestamp bounds.

### 11.4 Reports and Phase 2/3 boundaries

Phase 1 reports are files and stdout/stderr only. There is no web server,
daemon, GraphQL, gRPC, TUI, or inbound command channel.

Phase 2 alerting is an outbound Hunter Stack webhook with a local fallback event;
alerts follow `alert-policy@vN`, deduplication/grouping, cooldown, escalation,
acknowledgment, and direct Evidence Card linkage. Phase 3 Streamlit/Telegram
remain read-only projections. No phase adds order placement.

## 12. Risk policy lineage and separation

The initial portfolio limits derive from the QTS risk configuration extracted
from `multi-agent-system/config/risk.json` (referenced by the extraction manifest
as the QTS battle-tested limits). The canonical GAUNTLET artifact is
`policies/risk/qts.risk@v1.json`; later versions are appended, never overwritten.

Its lineage manifest records:

- source repository/file/content hash;
- import date and normalizing transformation;
- every parameter, unit, scope, and semantic explanation;
- venue applicability and required adaptation;
- owner authorization;
- mapping from original fields to GAUNTLET fields.

Portfolio policy enforces position size, leverage, concentration, correlation,
daily loss, drawdown, consecutive losses, timing, and circuit breakers for
paper/research portfolios. Research evidence gates enforce trades, effective
observations, execution realism, robustness, calibration, lineage, benchmark,
prospective performance, and regime coverage.

The domains intersect only through explicit state transitions:

- a risk-boundary violation can create `HOLD`, `QUARANTINE`, or a stop action;
- an evidence `FAIL` cannot be cured by a conservative risk policy;
- an evidence `PASS` cannot override a risk boundary or authorize exposure;
- changing sizing/stops/exposure during optimization creates a new trial and
  changes the trial-history input.

No GAUNTLET Phase 1 component submits an order. The portfolio state used by risk
checks is simulated/paper state and is labeled `MODELED`.

## 13. Technology decisions and trade-offs

| Decision | Choice | Rationale | Trade-off / mitigation |
|---|---|---|---|
| Language/runtime | Python managed by `uv`, portable pure-Python where practical | Matches extraction code, laptop/Mac mini portability, scientific ecosystem | Slower than Rust; heavy work isolated and profiled |
| Repository | One source monorepo with the core project and separately locked `gauntlet-factory` project | Shared contracts and end-to-end tests without incompatible dependency resolution | Needs subprocess boundary and lockfile tests |
| Storage | Parquet + canonical JSON/JSONL under `GAUNTLET_DATA_ROOT` | Local, inspectable, portable, no service, suits cadence work | No transactional DB; use exclusive writes, hash chains, indexes, durable backups |
| Content addressing | SHA-256 over canonical bytes | Provenance and deduplication | Verification cost; cache verified roots |
| Model stack | PyTorch/Kronos adapters behind `model/` | Reuse proven architecture and fine-tuning path | Heavy dependency; isolate from judge/factory import paths |
| Factory stack | `factory/pyproject.toml` + `factory/uv.lock` pinning `numpy==1.23.5`; separate subprocess runtime | Preserves VBT/GEPA behavior while core remains NumPy 2.x | Adds invocation boundary; core never imports factory |
| API/MCP | Typer-style CLI + FastMCP thin wrappers | Owner/AI operability without a daemon | Duplicate verbs must be contract-tested |
| Reports | Static files | Host can sleep; no server state | No live dashboard until Phase 3 |
| Database engines | No server **and no embedded engine** in Phase 1; JSON/Parquet/in-memory projections only | Cost/ops simplicity, portability, and fully regenerable local snapshots | Lookup/index work is manual; SQLite may be proposed only in Phase 2+ through an explicit requirements change |

The core project and lockfile resolve `numpy>=2.0,<3.0`. The separate factory
project and lockfile resolve `numpy==1.23.5`. Core commands never install or
import the factory project; the launcher uses the factory lock in a subprocess.
Factory emits artifact files rather than passing live objects across the boundary.

## 14. Security and access model

- Local single-owner operation; no multi-tenant authentication in Phase 1.
- FastMCP binds localhost by default and exposes only approved tools; remote
  access, if later enabled, traverses the existing authenticated tunnel.
- Secrets remain in local `.env`/process environment. They are not persisted in
  snapshots, reports, events, exports, manifests, or hashes.
- Collector requests record method/path/query and sanitized headers, never
  bearer tokens.
- No wrapper, MCP tool, report, or automation exposes an order-placement verb.
- Actors are identified in ledger/events; agent recommendations are advisory.
- Audit exports can include sensitive research data and remain local unless the
  owner explicitly chooses another channel.
- Raw external payloads are treated as untrusted data. Parsing is strict, and
  prompt-like text in a market snapshot cannot alter policy.

### 14.1 Owner identity and authorization boundary

GAUNTLET distinguishes structural caller identity from claimed identity. There
are exactly two Phase 1 authority contexts:

| Context | Established by | Allowed `actor.kind` |
|---|---|---|
| Owner CLI | Ed25519 signature made by the local owner private key | `human` |
| Agent/MCP/service automation | Wrapper-generated untrusted-but-labeled capability context | `agent` |

The owner key ceremony is local-only. The private key lives outside
`GAUNTLET_DATA_ROOT`, normally under `~/.gauntlet/owner-key.pem`, with mode
`0600`; the corresponding public key and key ID live in an immutable local
trust manifest. The initial trust manifest is created by a local bootstrap
command before the first owner action; if that manifest or usable private key is
absent, every owner-only operation fails closed. Rotating or adding a key creates
a new manifest version and ledger entry; it never rewrites historical
verification metadata. No token or private key is accepted as an MCP argument,
environment value passed through an agent, report field, or event payload.

An owner-only request is a canonical action envelope containing subject IDs,
decision vocabulary, reason, policy version, prior snapshot hash where
applicable, timestamp, nonce, review mode, and reveal-log hash. The owner CLI
signs that envelope locally. Core services verify the signature, key ID, nonce,
timestamp window, decision vocabulary, policy disposition, and subject hash
before reading the action as authorized.

Agent/MCP callers receive a process-generated capability context that
structurally sets `actor.kind=agent` and an installation/tool identity. The
service ignores any client-supplied `actor.kind=human`, owner key ID, or
signature claim from that path. There is no allowlist that can promote an MCP
tool to human authority in Phase 1.

Owner-only operations are:

- recording any owner decision vocabulary entry (`CONTINUE`, `HOLD`,
  `QUARANTINE`, `RELEASE`, `KILL`, `RENEW`, `PROMOTE`, `OVERRIDE`);
- overriding `FAIL` through a permitted documented exception class;
- authorizing a multi-axis experiment or sub-200 Verified exception;
- renewing or changing an experiment-family budget;
- releasing quarantine after repaired dependencies and forensics;
- changing active risk, evidence, transition, or alert policy;
- approving material data-cost escalation;
- declaring or changing live eligibility. Phase 1 exposes no live-activation
  command, and the RED real-money boundary remains unchanged.

Invalid, missing, expired, replayed, wrong-subject, wrong-key, or otherwise
unverifiable owner authorization fails closed: the action is not applied, the
snapshot/gate state is unchanged, and a non-sensitive authorization-failure event
is appended. Agents may prepare a recommendation or unsigned draft, but cannot
write an owner decision.

Owner decisions do not mutate the original Decision Snapshot. `record_owner_decision`
writes a new immutable `owner-decisions/<action-id>.json` in the snapshot
directory, linked by the exact prior `snapshot_hash`, signed-action hash, and
decision fields. The audit-bundle manifest includes all such extensions; the
original snapshot bytes remain byte-for-byte unchanged.

Integrity controls include canonical schemas, SHA-256, hash chaining, exclusive
creation, replay verification, and durable backups. They detect accidental or
ordinary tampering; they do not by themselves defeat a fully privileged local
attacker.

## 15. Operational concerns

### 15.1 Observability

Every command emits a run ID and records events. Operational checks cover:

- ledger head/hash validity and byte counts;
- event-chain head/hash validity and trial/snapshot anchor consistency;
- artifact descriptor/quality/freshness summary;
- dependency graph blockers;
- collector success/backoff/API cost;
- trial and family budget consumption;
- replay verification status;
- gate/snapshot verification;
- report generation and output hashes.

Failures return nonzero status and machine-readable JSON where applicable. They
never print a fabricated score or silently continue with substituted data.

### 15.2 Failure modes and response

| Failure | Phase 1 response |
|---|---|
| Host sleeps/reboots | Commands are rerunnable; unfinished runs remain incomplete and write-once outputs are not overwritten |
| API 429/Cloudflare/rate limit | Collector backs off, records attempts, leaves existing snapshots unchanged |
| Corrupt/stale source | Descriptor becomes invalid; dependent gates `BLOCKED`; quarantine event records scope |
| Duplicate collector snapshot | New immutable snapshot; merge policy is explicit and provenance-preserving |
| Nonempty output directory | Run refuses overwrite; operator chooses a new run ID |
| Model sampling nondeterminism | Fixed seed/sample count or declared tolerance; otherwise replay fails |
| Factory/core dependency conflict | Launcher refuses if the expected separate lock/NumPy version is absent; core never installs factory |
| Ledger verification failure | Stop decisions, surface integrity failure, restore from durable backup |
| Disk full | Run fails before partial evidence is interpreted; write-ahead staging and verification prevent partial promotion |

### 15.3 Deployment

Phase 1 runs from a Git checkout on macOS with `uv`; data stays under
`GAUNTLET_DATA_ROOT`, with `SOLANA_DEX_DATA_ROOT` accepted only as a migration
fallback. A later Linux/Docker deployment uses the same code and storage layout.
Backups treat ledger, descriptors, policies, source snapshots, checkpoints, and
Decision Snapshots as required; generated reports/indexes are rebuildable.

## 16. Testing and acceptance strategy

Architecture-level tests are contract tests, not only unit tests:

1. **Ledger immutability:** append succeeds, rewrite/delete verification fails,
   old snapshots still resolve their original entry.
   **Event integrity:** append succeeds, rewrite/delete/reorder fails, every
   consequential operation records the event head, and forged
   `actor.kind=human` agent traffic is rejected without state change.
2. **Provenance round trip:** build a synthetic trial → source → config →
   transformation → run → panel → snapshot chain; delete one artifact and prove
   reconstruction blocks.
3. **Dependency fail-closed:** stale/corrupt/missing/unknown inputs produce
   `INVALID` dependent metrics and `BLOCKED`, while noncritical gaps visibly
   reduce coverage.
   **Append-only quarantine:** original descriptor bytes/hash remain unchanged;
   quarantine creates a superseding version; an old `as_of` selects the original
   while a later `as_of` selects the quarantine state.
   **Collection contracts:** pagination truncation, rate-limit exhaustion,
   budget exhaustion, duplicate payload, malformed response, and partial capture
   each fail closed or register the declared duplicate/quarantine state.
4. **Precedence table:** exhaustive combinations prove
   `BLOCKED > FAIL > INSUFFICIENT_EVIDENCE > PASS`.
5. **Policy historical interpretation:** upgrade a ruleset and prove an old
   snapshot still evaluates under its recorded manifest.
6. **Temporal leakage:** target crossing train boundary, future normalization,
   and post-outcome split mutation all fail.
7. **Prospective recording:** outcomes cannot alter pre-outcome signals; late
   signals are labeled historical.
8. **Effective evidence:** overlapping labels, correlated tokens, repeated
   regimes, and adaptive counts reduce/report effective observations.
9. **Venue isolation:** cross-venue artifact cannot enter a single-venue gate
   without the explicit transfer type.
10. **Role isolation:** Scarlett benchmark/candidate conflict is blocked.
11. **Exact quote:** missing reserve yields failed evidence, never a fill;
     constant-product math matches a vectorized oracle.
12. **Risk separation:** risk breach changes disposition, never gate arithmetic;
     evidence pass does not authorize an order.
13. **Interface parity:** CLI and FastMCP verbs produce identical resolved
    configuration/output/error contracts for every minimum core service and
    append equivalent events; neither wrapper writes storage directly.
14. **Factory isolation:** core import graph contains no factory dependency;
     root `uv.lock` resolves only core NumPy 2.x, `factory/uv.lock` resolves
     only NumPy 1.23.5, and a wrong-version lock fails CI before execution.
15. **Export self-containment:** an audit bundle verifies after the original
    data root is unavailable.
16. **No Phase 1 database engine:** dependency metadata and import scan prove
    neither core nor factory depends on SQLite or another DB engine; deleting
    all generated JSON/Parquet index projections allows full regeneration.

Additional authorization and integrity scenarios must prove:

- a valid local owner signature records `actor.kind=human` and extends the exact
  snapshot hash;
- invalid, expired, replayed, wrong-key, wrong-subject, or MCP-submitted owner
  actions fail closed;
- MCP/agent capability context cannot claim human identity;
- events.jsonl hash-chain verification detects mutation and missing anchors.

Golden JSON artifacts exercise schema stability. Statistical kernels use
property-based tests and published small-vector oracles. End-to-end tests use a
synthetic market dataset small enough for CI.

## 17. Architecture-to-story constraints

Implementation stories must embed these non-negotiables:

- no candidate run without prior `trial.registered` lineage and resolved config;
- no gate without descriptor closure, quality/freshness checks, and criticality;
- no promotion path around `BLOCKED`;
- no report field synthesized to hide a mandatory gap;
- no venue/role mixing or post-hoc threshold selection;
- no deletion/update path for trials, source snapshots, policies, or snapshots;
- no factory import from core; factory uses only its separate
  `numpy==1.23.5` lock while core uses only its NumPy 2.x lock;
- no SQLite or other database engine dependency in Phase 1;
- no collector calls from report/MCP read paths;
- no order-placement interface.

Required early wiring stories are:

1. canonical contracts + hash/manifest verifier;
2. append-only ledger and event writer/verifier;
3. evidence descriptors + dependency graph evaluator;
4. resolved-config profile CLI;
5. judge walk-forward and exact-reserve adapters;
6. lab metrics + effective-evidence kernel;
7. policy manifests + deterministic precedence engine;
8. Decision Snapshot writer/reconstructor;
9. scoreboard/report projection;
10. risk policy import/versioning;
11. interface parity and event tracing;
12. end-to-end synthetic integrity drill.

The highest-risk integration points are judge→lab panel contracts, dependency
graph→gate inputs, ledger lineage→multiplicity accounting, and snapshot→report
reconstruction. Each needs a dedicated integration story rather than incidental
unit coverage.
