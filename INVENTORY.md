# Seven-Repo Extraction Manifest

Full inventory of what exists, what GAUNTLET takes from each, and why.

## 1. solana-dex-forecasting (this lineage) — THE JUDGE

**What it is:** the working pipeline: classifier training, walk-forward
validation, exact AMM reserve-quote execution, paper harness, Bitquery live
collection, Scarlett recorders, calibration scorer, falsification harness.

**Take (all proven, in daily use):**

| Module | Files | Role |
---|---|---|
| Validation | `walk_forward_validate.py`, `prepare_forecasting_splits.py` | The quality gate |
| Execution | `exact_quote_backtest.py`, `paper_trade_harness.py` | Real-cost referee (Solana AMM) |
| Models | `train_direction_classifier.py`, `tune_and_backtest.py`, `run_backtest.py` | Baseline candidates |
| Live data | `bitquery_daily_collector.py`, `bitquery_realtime_ingest.py` | Fresh OOS stream |
| Audit | `scarlett_snapshot.py`, `scarlett_calibration.py`, `validate_anti_scarlett.py`, `backtest_dex_winner.py` | External-claim verification |
| Cleaning | `clean_big_optimize_1016.py` | Raw → bars/events |

## 2. multi-agent-system — THE FACTORY

**What it is:** GEPA prompt-evolution strategy generator + VectorBT racer +
Three Gulfs evaluation + risk manager. Produced one fake winner
(Sharpe 3.8); its gate was the broken part.

**Take:**

| Item | Path | Why |
|---|---|---|
| GEPA optimizer | `gepa_optimizer.py`, `gepa_three_gulfs.py` | Candidate invention |
| VBT backtester | `lib/research/backtester_vbt.py`, `backtest_wrapper.py` | Fast variant racing |
| Risk manager | `lib/risk/manager.py` | Position sizing / caps kernel |
| Features | `lib/features/extractor.py` | 20+ indicator extraction |
| Three Gulfs | `lib/evaluation/` | Evaluation discipline |
| Risk config | `config/qts.risk.json` | Battle-tested limits |
| Evolved prompts | `config/prompts/*.yaml` (18) | Historical candidates (suspect; re-gate) |
| Falsified winner | `artifacts/winner.json`, `config/dex_winner.json` | Kept as cautionary reference |

## 3. jev-dspy-lab — THE LIE DETECTOR

**What it is:** offline-reproducible calibration lab for decision models.
Selective risk, coverage gates, Brier, ECE, bootstrap CIs, threshold sweeps.

**Take:**

| Item | Path | Why |
|---|---|---|
| Metrics | `src/jev_dspy_lab/metrics.py` | Core calibration math |
| Benchmark harness | `benchmark.py`, `replay.py`, `cli.py` | Reproducible scoring runs |
| Evidence patterns | `evidence/` layout | Hashed, auditable outputs |

## 4. Kronos (shiyu-coder) — THE MODEL

**What it is:** the open-source K-line foundation model Scarlett itself runs
(24.7M params, 512 context, 12B-record pretraining, MIT).

**Take:**

| Item | Path | Why |
|---|---|---|
| Model code | `model/` | Inference |
| Fine-tuning | `finetune/`, `finetune_csv/` | Domain adaptation to Solana |
| Backtest example | `examples/run_backtest_kronos.py` | Reference integration |

## 5. claude-code-plugin-marketplace — THE ORCHESTRATION PATTERNS

**What it is:** 23 Claude Code plugins built from the multi-agent system.

**Take (4 of 23):**

| Plugin | Why |
|---|---|
| `tournament-runner` | Multi-variant paper tournaments with promotion gates — the verdict-gate engine |
| `quant-trading-system` | Execution/risk agent patterns |
| `market-intelligence` | Regime/correlation analysis patterns |
| `research-execution-pipeline` | Research loop discipline |

## 6. ATLAS — THE ARCHIVE

**What it is:** oldest market-making agent system (single main + self-improve
CI workflow). Superseded.

**Take:** the self-improvement CI pattern only. Everything else is
historical reference.

## 7. gists-multi-agent-systems — THE PATTERN LIBRARY

**What it is:** agent orchestration research (VSM, wreckit, jido, letta,
cybernetic-aMCP).

**Take:** none for core trading. Indexed in `archive/` for the future
orchestration layer.

## Also referenced, not extracted

- **wangp-dspy:** main DSPy project; `gates/`, `metrics/`, `evaluate/`
  concepts inform GAUNTLET discipline but live in another lane.
- **Scarlett API:** external benchmark; recorded via judge-layer collectors.

## Extraction order

1. `judge/` — copy proven pipeline (highest value, zero risk)
2. `lab/` — calibration metrics (small, clean)
3. `factory/` — GEPA + VBT (needs the walk-forward gate wired in)
4. `model/` — Kronos code (fine-tune comes after data accumulation)
5. `risk/` + `scoreboard/` — assemble from qts.risk.json + kill criteria +
   tournament-runner patterns
6. `archive/` — index only
