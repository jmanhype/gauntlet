---
id: VK-0auj
title: "Deliver judge evaluation and independent evidence panels"
status: open
priority: 1
type: epic
labels: [phase-1]
created_at: 2026-09-18T23:15:39Z
created_by: speed
updated_at: 2026-09-19T01:51:01Z
content_hash: "sha256:161d9150c3b6b40b8eb1f99e8cf09c6c81887dc3252674e7dd3d8dbd6362660f"
---

## Description
## Context (Embedded)
GAUNTLET Phase 1 is a local, cadence-driven Python/uv research system. Its governing quality is prospective defensibility: every decision must be reconstructible from immutable local evidence and every failed trial must remain attributable. Phase 1 excludes order placement, real-money exposure, public APIs, long-running servers, multi-tenant access, and social claims. Paper and simulated orders are evidence records, not executions.

This epic implements the hostile evaluation path: walk-forward discipline, exact Solana AMM reserve pricing, untouched prospective recording, and independent lab panels for effective evidence, dominance, calibration, robustness, and reconciliation. Factory scoring can rank research candidates but can never define the business gate.

## Epic Outcomes
- Train before validation, select on validation, lock the variant, and test only the following window.\n- Solana fills quote against contemporaneous reserve state; missing reserve state is a failed quote or evidence gap, never a fill.\n- Raw trades and effective independent observations are reported separately under a versioned policy.

## OUT OF SCOPE
- Collecting new venue or Scarlett data: lands in the isolated-inputs epic.\n- Deciding PASS, FAIL, BLOCKED, or INSUFFICIENT_EVIDENCE: lands in the deterministic-decisions epic.\n- Hyperliquid pooling with Solana evidence: prohibited; transfer is a separate cross_venue_transfer hypothesis.

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
