---
id: VK-dblr
title: "Share CLI with FastMCP service parity"
status: open
priority: 3
type: feature
labels: [integration, phase-1]
parent: VK-rakf
created_at: 2026-09-18T23:31:35Z
created_by: speed
updated_at: 2026-09-18T23:31:35Z
content_hash: "sha256:2c266c02a55161fff6b91dcb5838c92f4b499f5e392130f23c157da68b28e27b"
blocked_by: [VK-0c4c, VK-si5s, VK-2e0k, VK-bns7, VK-52g6, VK-ealt]
blocks: [VK-hiuk]
was_blocked_by: [VK-jkkn]
---

## Description
## USER INTENT
The owner and AI agents can use equivalent local interfaces without either wrapper gaining hidden policy or storage authority.

Observable outcome: the owner can run the declared command, inspect or display its output, and verify that the implementation returns the declared result, stores its immutable artifact, and emits the corresponding hash-verified event.

## Context (Embedded)
Implement thin Typer-style CLI and FastMCP wrappers over exactly the typed minimum core services. Both use `resolve_config`; support `--json`, `--no-color`, and ASCII fallback; return OK/ERROR envelopes with service version, input/output hashes, event head, and machine-readable errors; and append equivalent events. Phase 1 commands cover collect, audit, gate, factory, tournament, scoreboard, report, review, forensic, decide, and export as local run-and-exit operations. FastMCP binds localhost and spawns on demand. Wrappers do not write ledger/storage directly. Read paths make no network call; only collector services access their approved remote sources. Failed service calls append error events.

Phase 1 global constraints:
- Local single-owner operation only; no public API, multi-tenant access, daemon, social publishing, or order placement.
- Immutable local evidence and replayability govern implementation choices.
- Unknown or unregistered inputs are gate-critical failures.
- Failures return machine-readable errors and never fabricate a score or silently substitute data.
- No SQLite or other database engine dependency is permitted; canonical JSON/JSONL and Parquet projections are fully regenerable.

## OUT OF SCOPE
- Long-running daemon, GraphQL, gRPC, TUI, web server, or inbound remote command: out of Phase 1.
- New evaluation semantics: upstream service stories.
- Live order placement or real-money exposure: Phase 1 remains RED with zero real-money exposure.
- Public API access or public performance claims: explicit business non-goals.

## DIFF BUDGET
~10 files, under 800 changed LOC.

## Boundary Map
PRODUCES:
- src/gauntlet/cli.py -> run_cli(args: Sequence[str]) -> ServiceEnvelope
- src/gauntlet/mcp.py -> register_mcp_tools(server: FastMCP) -> None
- src/gauntlet/services/__init__.py -> dispatch_service(operation: ServiceOperation, envelope: ServiceEnvelope) -> ServiceEnvelope

CONSUMES:
- VK-jkkn: src/gauntlet/config/resolver.py -> resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
  spec: resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig
- VK-0c4c: src/gauntlet/judge/walk_forward.py -> evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
  spec: evaluate_walk_forward(request: WalkForwardRequest) -> WalkForwardRun
- VK-si5s: src/gauntlet/factory/launcher.py -> launch_factory_race(command: FactoryCommand) -> FactoryArtifact
  spec: launch_factory_race(command: FactoryCommand) -> FactoryArtifact
- VK-2e0k: src/gauntlet/policy/engine.py -> evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
  spec: evaluate_gate(trial_id: str, dependency_evaluation_hash: str, panel_hashes: PanelHashes, ruleset_hash: str, policy_hash: str, as_of: datetime) -> GateResult
- VK-bns7: src/gauntlet/decisions/writer.py -> write_decision_snapshot(request: SnapshotRequest) -> DecisionSnapshot
  spec: write_decision_snapshot(request: SnapshotRequest) -> DecisionSnapshot
- VK-52g6: src/gauntlet/auth/owner.py -> verify_owner_action(action: SignedOwnerAction, context: CapabilityContext) -> AuthorizationResult
  spec: verify_owner_action(action: SignedOwnerAction, context: CapabilityContext) -> AuthorizationResult
- VK-ealt: src/gauntlet/scoreboard/report.py -> write_report(scope: ReportScope, formats: set[ReportFormat]) -> StaticReport
  spec: write_report(scope: ReportScope, formats: set[ReportFormat]) -> StaticReport

### Acceptance Criteria (story contract)
1. Every successful and representative failed minimum service operation has matching CLI and FastMCP output contracts and equivalent event records.
2. Both wrappers invoke typed services and never write ledger/storage directly or bypass the error contract.
3. Results carry OK/ERROR, service version, input hashes, output hashes, event head, and machine-readable error code/message.
4. Every operation appends a canonical event; failed calls emit status ERROR without inventing artifacts.
5. `--show-config` and `--diff-config` expose the exact resolved configuration through both surfaces.
6. Read/report/MCP operations make no collector network call; collect is the only collector-access verb and only through collector services.
7. Agent capability context is structurally actor.kind=agent and cannot claim human authority.
8. FastMCP binds localhost, is spawned on demand, exposes only approved tools, and offers no order-placement verb.

## Testing Requirements
- Unit: Test command parsing, JSON/no-color/ASCII behavior, service dispatch, and forbidden wrapper writes.
- Integration tests: MANDATORY (no mocks). Invoke each core service success and error path through real CLI and local FastMCP transports; compare canonical outputs, hashes, and event chains with no mocks.
- Commands to run: `uv run pytest tests/interfaces/test_cli_mcp_parity.py`.

## MANDATORY SKILLS
None identified.

## Delivery Requirements
- Developer must paste test or CI output snippets into story notes.
- Developer must include an AC verification table.
- Developer must append a delivered nd_contract block and add the delivered label; PM acceptance remains separate.

## nd_contract
status: new

### evidence
- Created 2026-09-18 by sr_pm from the owner-confirmed Phase 1 contracts at repository commit d77b4032e7ab1c90b435908a1a6d104007feff9e.
- Epic containment: VK-rakf.

### proof
- [ ] AC #1: Every successful and representative failed minimum service operation has matching CLI and FastMCP output contracts and equivalent event records.
- [ ] AC #2: Both wrappers invoke typed services and never write ledger/storage directly or bypass the error contract.
- [ ] AC #3: Results carry OK/ERROR, service version, input hashes, output hashes, event head, and machine-readable error code/message.
- [ ] AC #4: Every operation appends a canonical event; failed calls emit status ERROR without inventing artifacts.
- [ ] AC #5: `--show-config` and `--diff-config` expose the exact resolved configuration through both surfaces.
- [ ] AC #6: Read/report/MCP operations make no collector network call; collect is the only collector-access verb and only through collector services.
- [ ] AC #7: Agent capability context is structurally actor.kind=agent and cannot claim human authority.
- [ ] AC #8: FastMCP binds localhost, is spawned on demand, exposes only approved tools, and offers no order-placement verb.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-18T23:31:36Z dep_added: blocked_by VK-jkkn
- 2026-09-18T23:31:36Z dep_added: blocked_by VK-0c4c
- 2026-09-18T23:31:36Z dep_added: blocked_by VK-si5s
- 2026-09-18T23:31:36Z dep_added: blocked_by VK-2e0k
- 2026-09-18T23:31:37Z dep_added: blocked_by VK-bns7
- 2026-09-18T23:31:37Z dep_added: blocked_by VK-52g6
- 2026-09-18T23:31:37Z dep_added: blocked_by VK-ealt
- 2026-09-18T23:31:47Z dep_added: blocks VK-hiuk
- 2026-09-19T04:41:26Z dep_removed: was_blocked_by VK-jkkn

## Links
- Parent: [[VK-rakf]]
- Blocks: [[VK-hiuk]]
- Blocked by: [[VK-0c4c]], [[VK-si5s]], [[VK-2e0k]], [[VK-bns7]], [[VK-52g6]], [[VK-ealt]]
- Was blocked by: [[VK-jkkn]]

## Comments
