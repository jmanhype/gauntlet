# GAUNTLET Interface Design (v1)

Reflexion-refined design under explicit constraints. Governing rule:
**one core, thin wrappers, ephemeral by default, every action leaves a trace.**

## Constraint analysis

| Constraint | Bound | Design response |
|---|---|---|
| Host reliability | Primary host is a laptop (sleeps, reboots) | Phase 1 runs **zero long-running servers**; CLI runs and exits, MCP spawns on demand, reports are static files |
| Dependency conflict | Factory requires NumPy 1.23.5; core uses 2.x | uv-managed project + lockfile; factory deps isolated in an optional extra |
| Traceability | Every autonomous action auditable | Append-only `events.jsonl` logging every operation (actor, verb, args-hash, output-hash, timestamp) |
| API rate limits | Bitquery 429s; Scarlett behind Cloudflare UA rules | All interfaces read **local snapshots only**; live API calls happen exclusively inside collectors |
| Hunter Stack | Runs on a separate Mac mini behind a Cloudflare tunnel | Alerts are **outbound-only HTTP POST** with auth secret; local fallback log when unreachable; never an inbound command channel |
| Secrets | Tokens must never leak through wrappers | `.env` stays local; no token in any MCP response, REST payload, log line, or report |
| Exposure | No public surfaces needed | REST/MCP bind localhost by default; remote access only via the existing tunnel with auth |
| Business rule (RED) | No trading execution anywhere | Read/report: any surface. Run experiments: local CLI/MCP only. Order placement: absent by design |
| Compatibility | macOS now, Mac mini (Linux/Docker) later | Portable Python only; `GAUNTLET_DATA_ROOT` env with `SOLANA_DEX_DATA_ROOT` fallback during migration |
| Performance | Cadence-driven (2h/24h), not request-driven | No latency-sensitive infra justified; simplicity beats machinery |

## Phases

### Phase 1 — with judge extraction
- `gauntlet` CLI (subcommands: collect, audit, gate, factory, tournament, scoreboard, report)
- FastMCP server exposing the same verbs as tools (spawned by AI clients, not a daemon)
- Static `gauntlet report` output (Markdown/HTML file; no web server)
- `events.jsonl` append-only trace

### Phase 2 — alerting
- Outbound SMS kill-criteria/promotion pages via Hunter Stack webhook
- Localhost REST (uvicorn) **only when a concrete consumer exists**, supervised on the Mac mini Docker host

### Phase 3 — interactive (after weeks of data + stable host decision)
- Streamlit scoreboard reading local snapshots
- Telegram bot: alerts + whitelisted read-only status commands; never order entry

## Explicitly rejected

- TUI (Streamlit covers the use case), GraphQL and gRPC (no client complexity to justify)
- SMS/Telegram as command channels (spoofable)
- Any trading execution interface, at any phase, until a track survives its verdict gate — and even then: proposed, not exposed

## Origin

Produced by reflexion over the initial CLI/MCP/REST/SMS/Streamlit/Telegram
proposal; six flaws found and folded back into this design. See repo history.
