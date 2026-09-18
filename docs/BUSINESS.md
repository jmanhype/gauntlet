# GAUNTLET Business Definition

Status: confirmed by the owner on 2026-09-18

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

This ranking governs trade-offs. If a result appears profitable but cannot be
defended prospectively, replicated on untouched data, or executed under explicit
costs, it does not satisfy the primary objective.

## Goals

1. Discover and validate crypto trading candidates with positive after-cost expectancy.
2. Maintain a transparent evidence ladder from exploratory signal to candidate to verified track.
3. Separate Solana DEX discovery from Hyperliquid transfer testing so evidence is never pooled across materially different execution environments by default.
4. Preserve every trial, including failures, in an append-only experiment history.
5. Keep portfolio risk policy distinct from research evidence gates.
6. Produce internal reports sufficient for the owner to make an informed live-trading authorization decision.

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

### Exploratory

At least 50 resolved trades may justify additional research allocation, but only
when all of the following are true:

- Positive after-cost expectancy.
- No obvious single-trade, token, cluster, or execution artifact dominance.
- The result is treated as a research lead, not a promotable track.

### Candidate

A candidate may enter review after at least 100 resolved trades, provided it also
demonstrates:

- Positive after-cost expectancy.
- Frozen out-of-sample or prospective evidence.
- Explicit fee, slippage, market-impact, and execution assumptions.
- Benchmark comparison.
- No single trade, token, cluster, or regime dominating results.
- Trial-history accounting for strategy and parameter searches.
- Sufficient effective evidence to justify continued verification.

### Verified

Verification normally requires at least 200 resolved trades, but 200 is a
minimum checkpoint rather than proof. Verification must additionally account for:

- Effective independent observations rather than raw overlapping trade count.
- Strategy-selection and multiple-testing history.
- Non-normality and serial dependence where applicable.
- Bootstrap, probability of false discovery, deflated Sharpe ratio, probability
  of backtest overfitting, or equivalent robustness diagnostics where appropriate.
- Performance across multiple regimes.
- Benchmark performance.
- Reasonable adverse cost and slippage assumptions.
- Untouched prospective evidence.

The evidence requirement may exceed 200 trades. It is adaptive, not mechanical.

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

Failed experiments are evidence. They may not disappear from the statistical
history.

## Evidence-integrity requirements

Before implementation, the business definition requires explicit rules for:

- Data leakage prevention.
- Frozen or untouched evaluation data.
- Temporal split policy.
- Overlapping label and trade handling.
- Token and regime clustering.
- Data provenance.
- Replay reproducibility.

These rules protect the business outcome: no candidate may be promoted on
evidence that was available during selection or optimization.

## Risk policy

- Use the existing `qts.risk.json` limits as the initial portfolio-risk policy.
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

## Budget and operations

- Target operating cost is no more than $100 per month.
- Local snapshots remain the default operational evidence store.
- Budget pressure must not silently force lossy data collection that makes
  execution or falsification impossible.
- Any data-cost escalation that would materially improve or protect evidence
  quality requires explicit owner approval rather than automatic degradation.

## Failure policy

If no edge appears, preserve the null result. Broaden one major experimental axis
at a time whenever practical — market, strategy family, horizon, execution model,
or equivalent — so failures remain attributable.

Unlimited search across all axes until something becomes profitable is prohibited.

## Compliance and presentation

GAUNTLET is personal research only. It does not provide financial advice, does
not manage third-party assets, and must not make public performance claims without
future legal and compliance review.

## Acceptance signals

The business owner will consider the discovery phase successful when GAUNTLET can
demonstrate:

1. An append-only ledger of attempted hypotheses and rejected candidates.
2. Evidence reports that distinguish raw trade count from effective evidence.
3. After-cost, benchmark-relative, regime-aware, and prospective results for any
   surviving track.
4. Explicit cost, slippage, impact, and execution assumptions.
5. Controlled experiments where only one major axis changes at a time.
6. Preserved null results with attributable reasons.
7. Real-money exposure that remains $0 unless the owner explicitly changes the
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

## Open business questions

None blocking the initial business definition. Future owner decisions may include:

- When a verified track justifies a live-capital proposal.
- Whether GAUNTLET should ever become a product, fund tool, or public audit platform.
- Whether equities should enter scope after crypto validation.
