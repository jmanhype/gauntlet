# GAUNTLET

**Every claimed edge runs the gauntlet until it breaks — or proves itself.**

GAUNTLET is a self-falsifying alpha research system assembled from seven
predecessor repositories. It invents candidate trading strategies, races them,
judges them against realistic execution costs on live out-of-sample data,
audits every external claim independently, scores every confidence signal,
and automatically retires anything that stops working — including our own
ideas.

## The assembly line

```
      FACTORY                    JUDGE                     SCOREBOARD
┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
│ GEPA invents     │    │ Walk-forward gate    │    │ Live paper P&L   │
│ VectorBT races   │───▶│ Exact-cost execution │───▶│ vs. Scarlett     │
│ Kronos forecasts │    │ Out-of-sample only   │    │ Kill criteria    │
└──────────────────┘    └──────────────────────┘    └──────────────────┘
                              │
                              ▼
                    Only survivors get promoted.
```

## Provenance

Built from a full inventory of seven repositories — see `INVENTORY.md`.
The two founding falsifications that define its philosophy:

1. **The Sharpe 3.8 "winner"** (dex_winner, GEPA-evolved) collapsed to five
   trades under honest re-testing. Lesson: no quality gate, no strategy.
2. **Scarlett's "12B datapoint" forecaster** is the open-source Kronos-small
   (24.7M params), with confidence anti-calibrated at short horizons.
   Lesson: audit every claim against ground truth.

## Status

Assembly phase. The judge layer is proven in daily live use; the factory,
lab, and scoreboard modules are being wired. See `INVENTORY.md` for the
extraction manifest and `ROADMAP.md` (to come) for the phase plan.
