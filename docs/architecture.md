# Architecture

The implementation is split into three layers:

1. Python engine
   - `data.py` fetches and caches market and constituent data.
   - `features.py` computes index and breadth features.
   - `signals.py` converts features into regime and risk signals.
   - `ranking.py` produces explainable trade ideas, action boards, and entry plans.
   - `backtest.py` evaluates the same setup definitions historically.
   - `snapshots.py` serializes versioned artifacts and validates them.

2. Artifact layer
   - `artifacts/runs/<date>/...` holds immutable dated outputs.
   - `artifacts/latest/...` holds the latest app-facing copy.
   - `artifacts/latest.json` is the latest pointer manifest for the app.

3. Vercel app
   - `web/` reads the artifact contracts only.
   - The app does not compute analytics client-side.
   - The Python package remains the only source of truth for strategy logic.
