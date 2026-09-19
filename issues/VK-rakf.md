---
id: VK-rakf
title: "Expose shared read-only GAUNTLET surfaces"
status: open
priority: 3
type: epic
labels: [phase-1]
created_at: 2026-09-18T23:15:40Z
created_by: speed
updated_at: 2026-09-19T01:51:01Z
content_hash: "sha256:5ba1833119ece6d752f9380a1e7d840dbc78d74f4950743c19758f3dd3d98f90"
---

## Description
## Context (Embedded)
GAUNTLET Phase 1 is a local, cadence-driven Python/uv research system. Its governing quality is prospective defensibility: every decision must be reconstructible from immutable local evidence and every failed trial must remain attributable. Phase 1 excludes order placement, real-money exposure, public APIs, long-running servers, multi-tenant access, and social claims. Paper and simulated orders are evidence records, not executions.

This epic provides the operator-facing Phase 1 surfaces after the governance and decision contracts exist: deterministic scoreboard, Evidence Card, forensic, static report, and shared CLI/FastMCP service parity with event tracing. Interfaces are thin wrappers over typed core services and never own policy, state, storage formats, or evaluation logic.

## Epic Outcomes
- CLI and FastMCP expose the same verbs and JSON contracts, accept --json, --no-color, and ASCII fallback, and append equivalent events.\n- Read paths consume local snapshots; only audit/collectors may make network calls.\n- Reports make mandatory gaps visible as BLOCKED and never synthesize a field to hide missing evidence.

## OUT OF SCOPE
- A web server, daemon, GraphQL, gRPC, TUI, inbound command channel, or Phase 2 alerting: out of Phase 1.\n- New evaluation semantics: lands upstream in judge, lab, data, policy, or decision stories.\n- Any order-placement verb: prohibited.

## MANDATORY SKILLS
- None identified at epic level; story bodies name any required skills.

## nd_contract
status: new

### evidence
- Created from owner-confirmed BUSINESS.md, DESIGN.md, and ARCHITECTURE.md at repository commit d77b4032e7ab1c90b435908a1a6d104007feff9e.

### proof
- [ ] Epic outcome demonstrated by its final E2e capstone.

## Acceptance Criteria


## Design


## Notes
## ANCHOR REVIEW (backlog_review, round 2)
REVIEW_RESULT: APPROVED

### Improvements verified
1. VK-4qfy now derives and registers GATE_CRITICAL event-level Solana ReserveSeries and blocks VK-2g0f and VK-ldg1.
2. VK-rkdr now produces authoritative after-cost, benchmark-relative, adverse-scenario, and per-regime performance panels and blocks the gate, projections, and judge/lab capstone.
3. VK-aej2 establishes the P0 synthetic precedence walking skeleton after VK-1vhm only, before real evidence integration.
4. VK-3v14 adds durable required-class backup/restore verification and blocks the governance capstone.
5. VK-0c4c no longer depends on VK-pg9j and uses synthetic no-network wiring.
6. Relevant capstones include the added siblings; no live-trading/public-surface leakage was found.

### Evidence
- `pvg lint --backlog`: scanned 44 issues, 0 errors, 0 review findings.
- `pvg nd doctor`: all 44 issues passed validation.
- `pvg nd dep cycles`: no dependency cycles.
- Dependency inspection confirmed the repair edges above and ready front VK-1vhm -> VK-aej2.

### Advisory notes
- During implementation, ensure VK-rkdr's BenchmarkSeries input resolves from a concrete registered artifact/loader and records its provenance hash.

## History


## Links


## Comments
