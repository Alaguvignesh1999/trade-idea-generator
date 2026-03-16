# Data Sources

Current production baseline sources:

- Index price history: Yahoo Finance via `yfinance`
- S&P 500 constituents: `datasets/s-and-p-500-companies` public CSV
- NASDAQ 100 constituents: `datasets/nasdaq-100-companies` public CSV

Operational notes:

- Price data is cached under `cache/`.
- Snapshot metadata includes stale-data warnings when the latest price date does not match the snapshot date.
- If a constituent source is unavailable, the pipeline still produces index-level outputs for markets without supported member universes.
