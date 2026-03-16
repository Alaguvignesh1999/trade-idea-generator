# Runbook

## Generate one market

```bash
trade-idea-generator generate-snapshot --market "S&P 500"
```

## Generate all scheduled outputs

```bash
trade-idea-generator generate-all-snapshots
```

## Validate artifacts

```bash
trade-idea-generator validate-snapshots --path artifacts
```

## Typical failure checks

1. Confirm internet access and upstream data-source availability.
2. Check `cache/` for partial or stale downloads if a market fails repeatedly.
3. Re-run with a single market before retrying all markets.
4. Validate the resulting JSON before publishing.

## Safe change workflow

1. Edit config or Python logic.
2. Run `pytest`.
3. Generate one snapshot and backtest.
4. Validate artifacts.
5. Only then update scheduled publishing behavior.
