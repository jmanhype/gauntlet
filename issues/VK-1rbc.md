---
id: VK-1rbc
title: "Make deterministic decisions from immutable evidence"
status: open
priority: 0
type: epic
labels: [phase-1]
created_at: 2026-09-18T23:15:40Z
created_by: speed
updated_at: 2026-09-19T01:51:01Z
content_hash: "sha256:502b73533eb815a138f68c289e7cf2cc6ed67f689a63b34af7c8657cfaf0f415"
---

## Description
## Context (Embedded)
GAUNTLET Phase 1 is a local, cadence-driven Python/uv research system. Its governing quality is prospective defensibility: every decision must be reconstructible from immutable local evidence and every failed trial must remain attributable. Phase 1 excludes order placement, real-money exposure, public APIs, long-running servers, multi-tenant access, and social claims. Paper and simulated orders are evidence records, not executions.

This epic connects governance and independent evidence to the DESIGN decision model: a pure gate/policy engine with fixed precedence, immutable Decision Snapshots, local Ed25519 owner authorization, and self-contained audit export. Evidence, gate arithmetic, gate state, policy disposition, advisory recommendation, and owner decision remain separate facts.

## Epic Outcomes
- Aggregate precedence is always BLOCKED, then FAIL, then PENDING or INSUFFICIENT_EVIDENCE, then PASS.\n- A Decision Snapshot is the system of record; scoreboard and cards are reproducible projections.\n- Owner preference never converts FAIL or BLOCKED into promotion, and no exception can promote through BLOCKED.

## OUT OF SCOPE
- Rendering the scoreboard or Evidence Card: lands in the shared-surfaces epic.\n- Collector repair or new evidence creation: lands in the relevant upstream module epic.\n- Live eligibility or order placement: no Phase 1 command exists.

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
