# GAUNTLET Design Definition

Status: confirmed by the owner on 2026-09-18

Implements the approved `BUSINESS.md` evidence requirements as concrete
surfaces. The rendered UI is never the system of record; every decision fact
is persisted and reconstructible.

## 1. Three-layer review model

| Layer | Purpose | Authority |
|---|---|---|
| **Decision Snapshot** (persisted artifact) | Immutable record of a decision | **Authoritative — the system of record** |
| **Scoreboard** | Monitoring and triage | Projection only |
| **Evidence Card** | Per-candidate decision surface | Projection of snapshot + evidence |
| **Forensic View** | Full diagnostics, provenance, lineage, replay | Projection only |

Scoreboard answers, in order: what changed, what requires owner attention,
what is blocked or quarantined, and which stage every candidate occupies.
Selecting a candidate opens its Evidence Card. Comparative P&L, Sharpe, or
model confidence are never the dominant landing experience. The immutable
persisted Decision Snapshot is the single system of record; every surface is
a non-authoritative projection reconstructible from persisted artifacts.

## 2. Decision framing — six separate facts

Every decision surface renders these as distinct facts, never collapsed into
one "verdict":

1. **Evidence** — the measured inputs.
2. **Gate calculation** — the arithmetic, inspectable.
3. **Computed gate state** — `PASS` | `FAIL` | `BLOCKED` |
   `INSUFFICIENT_EVIDENCE`.
4. **Policy disposition** — derived from the applicable policy version:
   `CONTINUE_RESEARCH` | `ELIGIBLE_FOR_PROMOTION` | `HOLD` | `QUARANTINE` |
   `KILL`.
5. **Optional agent recommendation** — advisory commentary, visually and
   structurally distinct. A deterministic gate/policy consequence is never
   presented as AI opinion.
6. **Owner decision** — recorded with reason and timestamp.

Three review modes are supported for critical decisions:
`recommendation-visible`, `evidence-gate-first`, and
`owner-judgment-first`. The chosen mode and what information had been
revealed at decision time are logged. Owner overrides never rewrite the
computed gate or policy result.

Every decision stores, as separate facts: computed result, policy
disposition, recommendation, owner decision, reason, timestamp, evidence
version, policy version, and recommendation model version.

## 3. Evidence Card — normative field contract

Every decision surface must contain, or directly expose via a labeled
mandatory drill-down, **each** required business decision input. A review is
invalid if any required input is missing (rendered `BLOCKED`, never omitted).

| Group | Required fields |
|---|---|
| **Decision facts** | Evidence set + version; gate calculation (§3a); gate state; policy disposition + policy version; advisory recommendation (optional); owner decision slot |
| **Evidence quantity** | Raw count, effective count, effective-evidence calculation policy + version, and the full calculation disclosure: overlap window, clustering keys, serial-dependence treatment, regime handling, and the explicit reduction from raw trades to effective observations |
| **Reconciliation** | Claimed metric values, independently recomputed values, per-metric differences, tolerance band, provenance of both claim and recomputation, policy version, verdict |
| **Performance** | After-cost expectancy; execution assumptions with versions — fee model, slippage model, reserve-depth/market-impact model (venue-specific reserve or order-book state), fill-failure handling, latency — plus all four mandated adverse-scenario classes (fee stress, slippage/impact stress, fill-failure stress, latency stress), each labeled PASS/FAIL with inputs |
| **Benchmarks** | Benchmark identity + window; comparison result; losing-condition status |
| **Concentration panel** | Contribution and removal effects (top-contributor removal rerun) across: trade, token, cluster, regime, **venue, strategy variant, and execution artifact**; dominance verdict per axis |
| **Robustness panel** | Mandatory: bootstrap or equivalent uncertainty evidence + explicit multiplicity accounting (PSR/DSR/PBO or documented equivalent) — each named, versioned, labeled PASS/FAIL/NOT_RUN with reason; "where applicable" requires a recorded justification when a diagnostic is omitted |
| **Calibration panel** | Reliability by confidence bin, Brier score, expected calibration error, selective-risk-versus-coverage curve, gated-vs-ungated comparison; each with version and verdict |
| **Dual temporal status** | Walk-forward status AND prospective/untouched status, each with window and PASS/FAIL/PENDING |
| **Integrity** | Claim-vs-realized reconciliation verdict + tolerance band + policy version; data-quality/quarantine state; dependency-graph health |
| **Lineage & budgets** | Complete lineage: every related trial, parameter-search record, risk-parameter version, and failed ancestor reachable from the card; trial/compute/data budget state |
| **Next action** | The explicit next kill/downgrade/renewal/promotion condition and its current distance |
| **Delta** | Material changes since previous Decision Snapshot (§B) |

### 3a. Gate calculation — inspectable by contract

The card renders (or links one action deep to) the full calculation:

```
GATE: candidate-verified   POLICY v12   RULESET: verified-gates@v7
  rule evidence_min        input eff_obs=143 vs >=200          FAIL
  rule expectancy_pos      input +4.1bps vs >0                 PASS
  rule dominance           top_token 41% > 40% cap             FAIL
  rule regimes_covered     2/4 vs >=3                          FAIL
  rule reconciliation      verdict PASS tol ±5%                PASS
  rule prospective         PENDING (window open)               BLOCKED
AGGREGATE (deterministic precedence):
  any rule BLOCKED           → BLOCKED   (fail-closed dominates)
  else any rule FAIL         → FAIL
  else any rule PENDING/INSUF→ INSUFFICIENT_EVIDENCE
  else                       → PASS
```

Formula/rule identifiers, policy version, every material input and
threshold, per-rule results, and the aggregate derivation are all exposed.

Forensic diagnostics run automatically before major evidence transitions.
When clean, the owner sees no raw diagnostics — only failed checks, material
warnings, anomalous diagnostics, changed assumptions, and unresolved
counterevidence. Full forensic drill-down is always available.

### 3b. Major transitions and critical overrides — versioned enumeration

"Major transition" and "critical override" are defined by a versioned
enumeration (policy artifact `transitions@vN`), including at minimum:

- Candidate → Verified, and any future live-eligibility transition.
- Verified-status downgrade; integrity-driven invalidation.
- Quarantine release; Candidate kill; Verified kill.
- Experiment-family stop and renewal.
- Policy or evidence-version transitions affecting an active candidate.
- Any owner override of a FAIL/BLOCKED gate (critical override class).

Additions to the enumeration are policy changes, versioned and ledgered. A
soft, reversible exploratory kill requires no full forensic review.

## 3c. Owner decision model

Owner decision vocabulary: `CONTINUE`, `HOLD`, `QUARANTINE`, `RELEASE`,
`KILL`, `RENEW`, `PROMOTE`, `OVERRIDE`.

| Gate state | Permitted owner decisions |
|---|---|
| `PASS` | CONTINUE, HOLD, QUARANTINE, KILL, PROMOTE (if disposition ELIGIBLE_FOR_PROMOTION and forensics complete) |
| `FAIL` | CONTINUE (research only), HOLD, QUARANTINE, KILL, OVERRIDE-exception class only |
| `BLOCKED` | HOLD, QUARANTINE, KILL — never PROMOTE; unblocking requires dependency repair, not owner will |
| `INSUFFICIENT_EVIDENCE` | CONTINUE (accumulate), HOLD, QUARANTINE, KILL |

**Override/exception classes (fail-closed):**

- Owner preference never converts FAIL/BLOCKED into promotion. Overrides may
  only authorize a *documented exception* (e.g., sub-200 Verified minimum),
  recorded as a separate ledgered exception with: authorization identity,
  reason, the unchanged computed results, required forensic result, and the
  policy version under which the exception is granted.
- `BLOCKED` is hard fail-closed: no exception class may promote; only
  repairing the dependency and recomputing can unblock.
- Every OVERRIDE requires completed forensics (§3b) and a Decision Snapshot
  recording the exception separately from the computed gate.

### 3d. Experiment-family action matrix

Family-level decisions apply to an experiment family (not one candidate) and
are recorded against the family's ledger entry:

| Family state | Permitted owner decisions | Forensics |
|---|---|---|
| Active within budget | CONTINUE | Automatic summary |
| Budget exhausted / stop condition hit | KILL (family stop), RENEW (owner-authorized extension with new budget + reason) | Mandatory before RENEW |
| Integrity-invalidated | KILL; RENEW only after integrity repair | Mandatory |

Quarantine release is a candidate-level decision: from `QUARANTINED`, the
owner may `RELEASE` back to the prior stage only after the blocking condition
is repaired and automatic forensics pass; `RELEASE` never bypasses a
recomputed gate.

## 4. Agent / CLI — explicit reproducibility

No flag-typing theater; the requirement is a complete resolved
configuration for every run:

- No hidden research-critical values.
- Reusable configuration lives in versioned manifests/profiles, immutable
  once referenced by an experiment.
- Every run records the fully resolved configuration with a content hash.
- CLI flags are explicit overrides, included in the resulting configuration
  and audit record.
- Commands print and diff the fully resolved configuration
  (`gauntlet <cmd> --show-config`, `--diff-config`).
- Defaults are allowed only when versioned, visible, and captured in the
  resolved configuration.
- A concise invocation is acceptable exactly when it points at an immutable
  complete configuration.

```
$ gauntlet gate candidate-42 --profile profiles/sol-momentum-v3.toml
resolved config: sha256:9f31…  (2 overrides: fee_bps=25, horizon=12)
```

## 5. Missing / stale data — dependency-aware fail-closed

Every evidence input declares: provenance, freshness policy, quality state,
dependency relationships, gate criticality, and downstream metrics.

| Dependency state | Effect |
|---|---|
| Gate-critical missing/stale/corrupt | Dependent metrics `INVALID`; gates `BLOCKED`; promotion impossible |
| Explicitly noncritical | Unaffected metrics continue; evidence coverage visibly decreases; missingness prominently reported |
| Criticality unknown | Fail closed — block the dependent gate |

Never silently impute, estimate, forward-fill, or substitute evidence used
by a gate. Modeled values are labeled `MODELED` and can never masquerade as
observed evidence. The dependency graph and criticality classifications are
themselves versioned and auditable.

## 6. Interruptive alerts (SMS / Phase 2)

Interrupts fire only for: owner action required, major gate/policy
transition, material kill/downgrade, evidence/data-integrity failure,
risk-boundary violation, or system failure capable of invalidating research.

Every alert carries: deduplication and grouping, cooldown/rate limiting,
acknowledgment state, escalation rules, a stable event ID, and a direct
link to the affected Evidence Card. Routine summaries remain reports, never
pages. Alert volume and acknowledgment behavior are tracked so alert fatigue
is itself measurable.

"Major," "material," and "research-invalidating" are **versioned policy
classifications** (`alert-policy@vN`), not free-text judgments. Every alert
records measurable audit fields: severity class + policy version, stable
event ID, group key, cooldown state, acknowledgment identity and latency,
escalation path and outcome, and post-cooldown repeat count. Alert-fatigue
metrics are computed from these fields (alert rate per day, unacknowledged
actionable alerts, median ack latency, repeats after cooldown, escalation
rate) and reported on the Scoreboard.

## 7. Scoreboard navigation

Primary lifecycle axis: **Exploratory → Candidate → Verified**.

First-class views: `Action Required`, `Blocked / Quarantined`, `Killed`,
`Archived`, `Recently Changed`.

In-stage sort priority: owner-action-required > integrity/blocking condition
> recent material transition > age/staleness. The scoreboard never
default-sorts by P&L, Sharpe, model confidence, or recommendation strength.

## 8. Accessibility constraints

- State is never encoded by color alone; every state has a textual,
  machine-readable representation: `PASS`, `FAIL`, `BLOCKED`,
  `INSUFFICIENT_EVIDENCE`, `STALE`, `QUARANTINED`.
- Terminal-first operation; color-blind-safe palette; mobile-readable
  reports; no mandatory font; graceful no-color mode; ASCII fallback.
- All CLI/MCP output is machine-readable (JSON available behind a flag).

## Mandatory concepts A–H

**A. Decision snapshots.** Every consequential owner decision creates an
immutable snapshot containing the exact evidence, gate calculation, policy
disposition, recommendation (with visibility state), review mode, the
**ordered reveal log** (what information was displayed, in what order, before
the decision), and artifact versions used at decision time.

**B. Decision delta.** Every Evidence Card identifies what materially
changed since the previous decision snapshot.

**C. Provenance.** Every displayed evidence claim exposes provenance
sufficient to reach: experiment-ledger entry → source data/artifact →
configuration → transformation → producing run.

**D. Reproducibility.** Evidence Cards and decision snapshots are
reconstructible from persisted artifacts. UI state is never authoritative.

**E. Policy versioning.** Gate definitions and policy actions are
independently versioned. Historical decisions are always interpreted under
the versions active when the decision occurred.

**F. Recommendation versioning.** Agent recommendations are
replaceable/recomputable and record model/agent identity, version,
prompt/policy context where relevant, and input evidence snapshot.
Recomputing a recommendation never mutates historical recommendations.

**G. Review-mode experimentation.** GAUNTLET eventually supports controlled
evaluation of recommendation-first, evidence-first, and
independent-judgment-first review flows — measuring which produces the best
owner decisions rather than assuming one ordering is optimal.

**H. Audit export.** Any decision or candidate exports as a self-contained
audit bundle: evidence snapshot, provenance, gate results, policy
disposition, configuration, experiment lineage, recommendation, owner
decision, review mode, complete mode/reveal log, recommendation visibility,
and relevant hashes and versions.

## Surface mapping

| Concept | CLI | MCP tool | Report/Scorecard |
|---|---|---|---|
| Scoreboard | `gauntlet scoreboard` | `get_scoreboard` | Phase 3 app, static HTML now |
| Evidence Card | `gauntlet review <id>` | `get_evidence_card` | Card section in report |
| Forensic drill | `gauntlet forensic <id>` | `get_forensics` | Appendix |
| Decision | `gauntlet decide <id> --decision … --reason …` | `record_decision` | Decision log |
| Audit export | `gauntlet export <id>` | `export_audit_bundle` | File artifact |
| Config diff | `--show-config` / `--diff-config` | `resolve_config` | Run header |
