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
  pyproject.toml                 # core lock excludes factory pins
  uv.lock
  src/gauntlet/
    cli.py                       # Phase 1 CLI; thin wrapper over core services
    mcp.py                       # FastMCP spawned on demand; same verbs
    contracts/                   # schemas, canonical JSON, hashes, manifests
    ledger/                      # append-only ledger and events.jsonl
    data/                        # descriptors, dependency graph, quarantine
    policy/                      # deterministic gates and policy manifests
    judge/
    factory/
    lab/
    model/
    audit/
    risk/
    scoreboard/
  policies/                      # immutable policy and transition manifests
  profiles/                      # immutable run profiles
  data/                          # GAUNTLET_DATA_ROOT default/local artifacts
    raw/                         # append-only venue and external snapshots
    evidence/                    # content-addressed derived artifacts
    decisions/                   # immutable Decision Snapshots
    reports/                     # regenerable static projections
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
| Walk-forward run | `fold_manifest.json`, train/validation/test membership, locked selection, row-level test predictions and trades, run report | Frozen source bars/events, candidate/model profile, split policy, feature provenance |
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

### 4.5 `audit/` — external claims, recorder, and role isolation

**Responsibility**

Own all Scarlett recording and external-claim verification, adapted from
`scarlett_snapshot.py`, `scarlett_calibration.py`, and
`validate_anti_scarlett.py`. It is the only Phase 1 interface layer allowed to
call external APIs; report/MCP/CLI consumers read local snapshots.

Scarlett can be benchmark, candidate/information source, or audit target, but
never two roles for the same decision without an explicit contamination analysis
and a replacement benchmark.

| Contract | PRODUCES | CONSUMES |
|---|---|---|
| External snapshot | Raw paginated response, request metadata (without credentials), collector/version, fetch time, content hash | Rate-limited external API and versioned collector policy |
| Claim decomposition | Claimed metric/capability, source, actual model/process identity, decision role, materiality tolerance | Immutable snapshots and historical artifacts |
| Audit reconciliation | Independent recalculation, outcome data, differences, verdict | Claim record and relevant lab kernel |
| Role declaration | Role enum, permitted uses, contamination constraints | Trial/family manifest |

Collector secrets remain in the process environment and are never copied into
payloads, events, reports, exports, or hashes.

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
