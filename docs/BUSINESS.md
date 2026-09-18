# GAUNTLET Business Definition

Status: owner-confirmed 2026-09-18; revised after adversarial business review

## Problem statement

Trading-system claims are cheap, but defensible edges are rare. GAUNTLET exists to
prospectively discover, test, and retain only executable crypto-market edges that
survive realistic costs, honest out-of-sample evidence, multiplicity accounting,
and regime analysis. A negative result is not a failure if it is preserved and
attributable: knowing that an edge does not survive is valuable research output.

GAUNTLET is not being optimized merely to show positive paper P&L. Its higher
purpose is to produce an edge that can be defended prospectively and executed
under explicit assumptions.

## Identity and stakeholders

GAUNTLET is initially a personal research system with future optionality. It is
not committed to becoming a product, fund, or public platform.

| Stakeholder | Need |
|---|---|
| Owner | Clear go/no-go evidence before any real-money activation; preserved research history; attributable failures |
| AI research agents | Unambiguous evidence rules, experiment isolation, and immutable trial history so work cannot silently overwrite or reuse data |
| Future reviewers / collaborators (optional) | Reproducible provenance and an audit trail explaining why a candidate passed or failed |

No customer, investor, or public user is in the initial scope.

## Success hierarchy

The owner ranked the outcomes as follows:

1. **Prospectively defensible, executable edge**
2. **Positive after-cost paper performance**
3. **Evidence that survives falsification, multiplicity, and regime testing**
4. **Reusable research factory**
5. **External auditability**

Outcome ① is the governing objective. Outcomes ② and ③ are **jointly necessary
and non-substitutable**: a profitable but fragile result cannot be promoted on ②
alone, and statistical robustness without executable after-cost performance
cannot be promoted on ③ alone. The ranking guides emphasis and resource
allocation; it never overrides an evidence gate.

## Goals

1. Discover and validate crypto trading candidates with positive after-cost expectancy.
2. Maintain a transparent evidence ladder from exploratory signal to candidate to verified track.
3. Separate Solana DEX discovery from Hyperliquid transfer testing so evidence is never pooled across materially different execution environments by default.
4. Preserve every trial, including failures, in an append-only experiment history.
5. Keep portfolio risk policy distinct from research evidence gates.
6. Produce complete internal reports the owner can use to make an informed
   live-trading authorization decision.
7. Give the owner a continuously visible scoreboard of candidate status, evidence
   quality, experiment-family budgets, and explicit stop/downgrade conditions.

## Non-goals

The following are explicit near-term non-goals:

- Live order placement or real-money deployment.
- Customer onboarding or multi-tenant access.
- Public API access.
- Social publishing or public claims.
- Providing financial advice or operating as an investment service.
- Markets outside crypto during the initial scope.
- Unrestricted parameter search until something appears profitable.

Live orders remain RED. Real-money exposure remains $0 until the owner
explicitly authorizes activation after a track passes its evidence gate.

## Market and venue scope

- **Solana DEX** is the primary discovery market.
- **Hyperliquid** is a benchmark, mirror, and transfer venue.
- Evidence from Solana and Hyperliquid must not be pooled into one statistical
  population by default. Execution mechanics, fees, liquidity, market structure,
  and failure modes differ.
- Cross-venue transferability is a separate hypothesis and must be tested on
  its own evidence.

## Evidence model

Trade count is an operational checkpoint, not proof of edge.

### Required decision inputs at every stage

Every evidence review must report the following before a status can change:

- **Raw and effective sample evidence:** raw resolved trades; effective
  independent observations after overlapping-horizon, serial-dependence, token,
  cluster, and regime handling; the calculation policy and its version.
  The effective-evidence policy must disclose its overlap window, clustering
  keys, serial-dependence treatment, and the calculation that reduces raw trades
  to effective observations.
- **Claim-versus-realized reconciliation:** claimed metrics, recomputed metrics,
  source provenance, differences, and a pass/fail result against the
  materiality tolerance declared before reconciliation.
- **Execution realism:** fees, slippage, market impact, fill/latency/failure
  assumptions, and venue-specific reserve or order-book state used for pricing.
  Adverse scenarios must cover fee stress, slippage stress, reserve-depth or
  market-impact stress, and at least one fill-failure/latency stress case; their
  numeric values and versions must be declared before review.
- **Benchmark comparison:** named benchmark, comparison window, after-cost
  excess performance, and conditions under which the benchmark wins.
- **Dominance panel:** percentage contribution and contribution-after-removal
  for the largest single trade, token, correlated token cluster, regime, venue,
  strategy variant, and execution artifact.
- **Robustness panel:** the pre-declared bootstrap and multiplicity-aware
  diagnostics used, their assumptions, and pass/fail results.
- **Calibration panel:** reliability by confidence bin, Brier score, expected
  calibration error, selective-risk-versus-coverage result, and whether
  confidence-gated selection outperforms ungated or abstaining behavior.
- **Experiment lineage:** every related trial, parameter search, risk-parameter
  version, and failed ancestor that contributed to the result.

The specific numeric thresholds and scenario values must be declared in advance
and versioned. A review is invalid if any required decision input is missing or
was selected after seeing the outcome.

### Exploratory

At least 50 resolved trades may justify additional research allocation, but only
when all of the following are true:

- Positive after-cost expectancy.
- The dominance panel is present and no single trade, token, correlated token
  cluster, regime, or execution artifact contributes more than half of positive
  expectancy or reverses the result when removed.
- The result is treated as a research lead, not a promotable track.

### Candidate

A candidate may enter review after at least 100 resolved trades, provided it also
demonstrates:

- Positive after-cost expectancy.
- Walk-forward out-of-sample evidence generated under frozen assumptions and
  untouched prospective paper evidence recorded before outcomes were known.
- Explicit fee, slippage, market-impact, fill-failure, and latency assumptions.
- Benchmark comparison.
- A dominance panel showing that no single trade, token, correlated cluster,
  regime, or execution artifact contributes more than half of positive
  expectancy or reverses the result when removed.
- Trial-history accounting for strategy and parameter searches.
- A pre-declared effective-evidence calculation showing enough independent
  information to support the claimed result.
- Positive expectancy under the versioned adverse execution-cost scenario.
- A complete robustness panel with bootstrap confidence or an equivalent
  uncertainty estimate and explicit multiple-testing accounting.

### Verified

Verification requires **at least 200 resolved trades**; adaptivity may increase
the requirement but never reduce it below 200 without a documented
owner-authorized exception. Verification must additionally account for:

- Effective independent observations rather than raw overlapping trade count.
- Strategy-selection and multiple-testing history.
- Non-normality and serial dependence where applicable.
- Bootstrap plus at least one probability-of-false-discovery, deflated
  Sharpe ratio, probability-of-backtest-overfitting, or equivalent
  multiplicity-aware diagnostic.
- Positive expectancy under the pre-declared worst-case adverse cost, slippage,
  fill-failure, and latency scenarios.
- Performance across the pre-declared regime taxonomy. Verification fails if a
  required regime was not tested or if performance in any a-priori adverse regime
  reverses the claimed edge without a disclosed explanation and continued
  prospective confirmation.
- Benchmark performance.
- Untouched prospective evidence.

The evidence requirement may exceed 200 trades. It is adaptive upward, never
mechanically satisfied by count alone.

## Experiment governance

GAUNTLET must preserve an append-only experiment/trial ledger containing:

- Hypothesis.
- Strategy family.
- Data window.
- Features.
- Parameters and search space.
- Execution assumptions.
- Benchmark.
- Variants attempted.
- Result.
- Rejection or promotion reason.
- Relationship to prior experiments.
- Status transition, actor, timestamp, experiment-family budget, and the exact
  experimental axes changed.

Failed experiments are evidence. They may not disappear from the statistical
history.

### One-axis rule and exceptions

By default, broaden or change one major experimental axis at a time — market,
strategy family, horizon, execution model, data window, or equivalent — so a
failure or improvement remains attributable.

The owner decides whether to authorize a multi-axis exception. An AI agent may
recommend one, but cannot authorize continued multi-axis searching on its own.
Every exception must be recorded in the ledger before the result is interpreted
and must state:

- Why a single-axis experiment cannot answer the business question.
- Every axis being changed.
- The attribution question the exception is allowed to explore.
- The controlled decomposition, isolation test, or follow-up single-axis plan
  that will preserve causal interpretation.

A multi-axis result may generate exploratory evidence, but cannot alone promote
a candidate unless the contributing effect survives isolated testing.

## Evidence-integrity requirements

Before implementation, the business definition requires explicit rules for:

- Data leakage prevention.
- Frozen or untouched evaluation data.
- Temporal split policy.
- Overlapping label and trade handling.
- Token and regime clustering.
- Data provenance.
- Replay reproducibility.
- Walk-forward evaluation windows.
- Untouched prospective signal recording.
- Solana AMM reserve-state pricing.

These rules protect the business outcome: no candidate may be promoted on
evidence that was available during selection or optimization.

## Mandatory evidence and audit acceptance requirements

The following are business-level acceptance requirements, not optional report
features:

1. **Dual temporal evidence:** every candidate must have walk-forward
   out-of-sample evidence and untouched prospective paper evidence. A result
   based on only one of the two cannot pass Candidate review.
2. **Reserve-state execution pricing:** Solana AMM candidates must price fills
   against venue-specific pool-reserve state contemporaneous with the simulated
   order. Price-only execution is exploratory evidence and cannot support
   promotion. Missing reserve state must be reported as an execution failure or
   evidence gap, never silently treated as a fill.
3. **Immutable experiment and audit recording:** hypotheses, trials, outcomes,
   claim reconciliations, status transitions, and owner exceptions must be
   retained in the append-only research history.
4. **Confidence-calibration evaluation:** any probability, confidence, strength,
   or path-share signal used in a decision must be scored on untouched outcomes.
   A confidence gate fails when its selective performance is worse than
   abstaining or an ungated policy under the pre-declared tolerance. External
   confidence claims must be reported as calibration evidence, not accepted as
   capability claims.
5. **Claimed-versus-realized reconciliation:** no historical or external claim
   may enter an evidence report without source provenance, independent
   recalculation where source data permits, materiality tolerance, and a
   pass/fail verdict. Unverifiable claims cannot support promotion.
6. **Owner-visible scoreboard:** the owner must be able to see, for every track
   and experiment family, current status, effective evidence, after-cost
   performance, benchmark comparison, execution assumptions, calibration result,
   trial budget consumption, and the next explicit kill, downgrade, renewal, or
   promotion condition.

## Kill, downgrade, and stop criteria

### Candidate kill

Kill or return a candidate to Exploratory when any of the following is true:

- It fails the minimum resolved-trade requirement for its requested stage.
- Base or pre-declared adverse-scenario after-cost expectancy is not positive.
- Required walk-forward, prospective, benchmark, dominance, calibration,
  robustness, execution, or lineage evidence is missing.
- A single trade, token, correlated cluster, regime, venue, or execution
  artifact contributes more than half of positive expectancy or reverses the
  result when removed.
- Claimed metrics cannot be reconciled within the pre-declared materiality band.
- An execution assumption cannot be evaluated with the evidence retained.

### Prospective paper-tracking stop or downgrade

Stop paper tracking, or downgrade status, when any of the following occurs on the
pre-declared rolling prospective evaluation window with its minimum effective
observation count:

- After-cost expectancy is zero or negative.
- Performance is below the pre-declared benchmark condition.
- Risk limits are breached or execution assumptions diverge materially from
  realized fills.
- Calibration or concentration failure invalidates the selection mechanism.
- Evidence-integrity or replay checks fail.

### Verified-status downgrade

A Verified track must be downgraded when any of the following occurs:

- Untouched prospective evidence fails the rolling after-cost or benchmark
  condition.
- Robustness, multiplicity, regime, calibration, or reconciliation evidence is
  later found invalid.
- A data, execution, provenance, or replay defect impairs the evidence.
- A versioned execution or risk assumption changes enough to require a new
  research trial and the prior verification no longer applies.

Downgrading returns the track to Candidate or Exploratory according to the
remaining valid evidence; it never preserves Verified status by default.

### Experiment-family stop

Every experiment family begins with an owner-visible trial budget, compute/API
cost budget, data window, and success condition. The family must halt when any
limit is reached without producing the declared success condition.

Continuation requires an explicit owner-approved renewal recorded in the ledger
with the reason, changed axis, revised budget, and what prior failure makes the
renewal plausible. Unlimited continuation on weak evidence is prohibited.

## Risk policy

- Use the existing `qts.risk.json` limits as the initial portfolio-risk policy
  (Owner-confirmed 2026-09-18, accepted defaults).
- Portfolio risk limits are separate from research-evidence gates.
- Risk parameters must be versioned.
- A change to risk sizing, stops, or exposure limits during optimization counts
  as another research trial.
- No real-money exposure is authorized during discovery, framing, or validation.

## External system policy

Scarlett may serve three roles:

1. Benchmark.
2. Strategy candidate or information source.
3. Audit target.

These roles must remain isolated. If Scarlett-derived information contributes to
a candidate strategy, Scarlett cannot simultaneously serve as the uncontaminated
benchmark for that candidate.

## Founding falsification controls

GAUNTLET's business rules are anchored to two canonical exposures:

1. **The dex_winner Sharpe 3.8 collapse:** a claimed evolved winner collapsed to
   five honest trades under retesting. Therefore, no claimed metric may be
   accepted without independent recalculation, source provenance, execution
   replay, and reconciliation against realized evidence.
2. **The Scarlett capability exposure:** a marketed “12B datapoint” system was
   found to use the open-source Kronos-small model, with confidence signals
   requiring calibration rather than trust. Therefore, every confidence or
   capability claim must be decomposed into its actual source, model or process,
   decision role, and measured calibration.

These controls are mandatory because both founding cases demonstrated that a
compelling claim without reconciliation can otherwise outrun the evidence.

## Budget and operations

- Target operating cost is no more than $100 per month (Owner-confirmed
  2026-09-18, accepted defaults).
- Local snapshots remain the default operational evidence store
  (Owner-confirmed 2026-09-18, accepted defaults).
- Budget pressure must not silently force lossy data collection that makes
  execution or falsification impossible.
- Any data-cost escalation that would materially improve or protect evidence
  quality requires explicit owner approval rather than automatic degradation.

## Failure policy

If no edge appears, preserve the null result. Broaden one major experimental axis
at a time under the one-axis rule and exception process above.

Unlimited search across all axes until something becomes profitable is prohibited.

## Compliance and presentation

GAUNTLET is personal research only. It does not provide financial advice, does
not manage third-party assets, and must not make public performance claims without
future legal and compliance review.

## Acceptance signals

The business owner will consider the discovery phase successful when GAUNTLET can
demonstrate:

1. An append-only ledger containing attempted hypotheses, trial history,
   rejected candidates, audit results, owner exceptions, and family budgets.
2. Evidence reports that separately report raw trades and effective independent
   observations, including the overlap and clustering policy used.
3. Walk-forward and untouched prospective paper evidence for every promoted
   track.
4. Solana AMM execution priced against contemporaneous reserve state, with
   explicit fees, impact, slippage, latency, and fill-failure assumptions.
5. Confidence-calibration reports for every decision signal and external
   confidence claim.
6. Claimed-versus-realized reconciliation for historical or external metrics.
7. After-cost, benchmark-relative, regime-aware, multiplicity-aware, and
   prospective results for any surviving track.
8. An owner-visible scoreboard with explicit kill, downgrade, stop, renewal, and
   promotion conditions.
9. Controlled experiments where one axis changes at a time or an owner-approved
   multi-axis exception with a recorded attribution plan.
10. Preserved null results with attributable reasons.
11. Real-money exposure that remains $0 unless the owner explicitly changes the
    RED authorization.

## Key risks

| Risk | Business consequence | Mitigation |
|---|---|---|
| False positive from repeated experimentation | Premature live-loss authorization | Immutable trial history and adaptive evidence gates |
| Concentration disguised as diversification | One token/regime creates illusion of edge | Cluster and regime dominance checks |
| Venue contamination | Transfer claimed without evidence | Separate Solana and Hyperliquid populations |
| Data loss or unreproducible results | Evidence cannot be defended | Provenance, local snapshots, replay rules |
| Cost pressure degrades data | Execution or falsification becomes impossible | Explicit approval for material data-cost escalation |
| Impatience with statistical power | Promotion based on noise | Evidence ladder and untouched prospective data |
| Profitable but fragile result | False confidence in an unexecutable edge | Joint necessity of after-cost performance and falsification evidence |
| Unbounded experiment-family continuation | Cost and false-positive risk grow without evidence | Pre-declared budgets and owner-approved ledgered renewals |

## Open business questions

None blocking the initial business definition. Future owner decisions may include:

- When a verified track justifies a live-capital proposal.
- Whether GAUNTLET should ever become a product, fund tool, or public audit platform.
- Whether equities should enter scope after crypto validation; equities are
  later-phase optionality only (Owner-confirmed 2026-09-18, accepted defaults).
