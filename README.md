# Trade Idea Generator

This repository now has a production-shaped baseline next to the original notebook:

- `src/trade_idea_generator/` contains the Python source of truth for data loading, features, signals, ranking, backtests, snapshots, schemas, and CLI commands.
- `configs/default.json` holds versioned runtime configuration.
- `schemas/` contains JSON contracts for market snapshots, action boards, trade idea lists, backtest results, and run manifests.
- `web/` contains a Vercel-ready Next.js app that reads generated JSON artifacts only.
- `Global Signal Dashboard v25.ipynb` is retained as an exploratory notebook, not the production source of truth.

## Quickstart

```bash
python -m pip install -e .
trade-idea-generator generate-snapshot --market "S&P 500"
trade-idea-generator validate-snapshots --path artifacts
```

The pipeline writes versioned outputs under `artifacts/runs/<as-of>/...` and refreshes app-facing pointers under `artifacts/latest/...`.

## Operator Commands

```bash
trade-idea-generator generate-snapshot --market "S&P 500"
trade-idea-generator generate-all-snapshots
trade-idea-generator run-backtest --market "NASDAQ 100"
trade-idea-generator validate-snapshots --path artifacts
```

## Web App

The app lives in `web/`. It reads JSON from:

- `NEXT_PUBLIC_DATA_BASE_URL`, if set to a published artifact branch or static host
- local sample files under `web/public/data/`, otherwise

For local development:

```bash
cd web
npm install
npm run dev
```

## Docs

- `docs/architecture.md`
- `docs/configuration.md`
- `docs/data-sources.md`
- `docs/runbook.md`
