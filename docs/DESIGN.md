# GAUNTLET Design Definition

Status: confirmed by the owner on 2026-09-18

Implements the approved `BUSINESS.md` evidence requirements as concrete
surfaces. The rendered UI is never the system of record; every decision fact
is persisted and reconstructible.

## 1. Three-layer review model

| Layer | Purpose | Authoritative for |
|---|---|---|
| **Scoreboard** | Monitoring and triage | Nothing — it points at Evidence Cards |
| **Evidence Card** | Per-candidate decision surface | The decision record it snapshots |
| **Forensic View** | Full diagnostics, provenance, lineage, replay | Nothing — inspection only |

Scoreboard answers, in order: what changed, what requires owner attention,
what is blocked or quarantined, and which stage every candidate occupies.
Selecting a candidate opens its Evidence Card. Comparative P&L, Sharpe, or
model confidence are never the dominant landing experience.

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

## 3. Evidence Card — standard view (default)

```
CANDIDATE <id>                    STAGE: Candidate            POLICY v12
───────────────────────────────────────────────────────────────────────
GATE STATE:            INSUFFICIENT_EVIDENCE   (not color-coded alone)
POLICY DISPOSITION:    HOLD
EFFECTIVE EVIDENCE:    87 effective obs (143 raw; overlap-adjusted)
EXPECTANCY:            +4.1 bps/trade after costs
BENCHMARK:             vs SOL-DEX basket +9.3 bps/trade
CONCENTRATION:         top token 41% contribution; flagged
REGIME COVERAGE:       2 of 4 declared regimes; insufficient
EXECUTION ASSUMPTIONS: fee 25bps RT, impact k=1.2, latency 250ms
DATA QUALITY:          3 quarantined inputs (see Forensic)
SEARCH HISTORY:        14 prior trials in family; ledger-linked
COUNTEREVIDENCE:       1 unresolved regime failure (2026-09 window)
DELTA SINCE LAST SNAPSHOT: +31 trades, concentration warning NEW
───────────────────────────────────────────────────────────────────────
RECOMMENDATION (advisory): continue research; resolve regime gap
OWNER DECISION:        [ pending ]
```

Forensic diagnostics run automatically before major evidence transitions.
When clean, the owner sees no raw diagnostics — only failed checks, material
warnings, anomalous diagnostics, changed assumptions, and unresolved
counterevidence. Full forensic drill-down is always available.

**Mandatory forensic execution before:** Candidate → Verified, any
live-eligibility transition, critical owner override. A soft, reversible
exploratory kill requires no full forensic review.

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

```$ gauntlet gate candidate-42 --profile profiles/sol-momentum-v3.toml
```resolved config: sha256:9f31…  (2 overrides: fee_bps=25, horizon=12)
``````

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
disposition, recommendation, review mode, and artifact versions used at
decision time.

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
decision, and relevant hashes and versions.

## Surface mapping

| Concept | CLI | MCP tool | Report/Scorecard |
|---|---|---|---|
| Scoreboard | `gauntlet scoreboard` | `get_scoreboard` | Phase 3 app, static HTML now |
| Evidence Card | `gauntlet review <id>` | `get_evidence_card` | Card section in report |
| Forensic drill | `gauntlet forensic <id>` | `get_forensics` | Appendix |
| Decision | `gauntlet decide <id> --decision … --reason …` | `record_decision` | Decision log |
| Audit export | `gauntlet export <id>` | `export_audit_bundle` | File artifact |
| Config diff | `--show-config` / `--diff-config` | `resolve_config` | Run header |
