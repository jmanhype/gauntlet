---
id: VK-u40v
title: "Collect and isolate GAUNTLET research inputs"
status: open
priority: 2
type: epic
labels: [phase-1]
created_at: 2026-09-18T23:15:39Z
created_by: speed
updated_at: 2026-09-19T01:51:01Z
content_hash: "sha256:c91627c755fb8d8bd1a2e45c2482bda7827b25a8229690dc48ac96eaf775f798"
---

## Description
## Context (Embedded)
GAUNTLET Phase 1 is a local, cadence-driven Python/uv research system. Its governing quality is prospective defensibility: every decision must be reconstructible from immutable local evidence and every failed trial must remain attributable. Phase 1 excludes order placement, real-money exposure, public APIs, long-running servers, multi-tenant access, and social claims. Paper and simulated orders are evidence records, not executions.

This epic owns the only Phase 1 network boundary: audit/collectors. It adds Bitquery Solana snapshots, Hyperliquid transfer snapshots, Scarlett role-isolated snapshots, Kronos model lineage, isolated factory races, and the separate portfolio risk policy. Business priority places judge wiring ahead of collectors, and collectors ahead of factory work.

## Epic Outcomes
- Every collector capture is immutable, paginated, budgeted, deduplicated by explicit keys, and fails closed on partial capture or checksum failure.\n- Scarlett never serves incompatible benchmark, candidate/information-source, and audit-target roles for one decision without explicit redesign and a replacement benchmark.\n- Factory remains a separately locked subprocess with NumPy 1.23.5 while core remains NumPy 2.x.

## OUT OF SCOPE
- Public API exposure, multi-tenant access, social publishing, and live orders: never in Phase 1.\n- Evidence verdicts and owner actions: land in the deterministic-decisions epic.\n- Owner-facing projections: land in the shared-surfaces epic.

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
