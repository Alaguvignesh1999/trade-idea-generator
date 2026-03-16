# Configuration

The runtime config lives in `configs/default.json`.

Key sections:

- `config_version` and `strategy_version`
- `indices`
- `thresholds`
- `score_weights`
- `trade_idea`
- `backtest`
- `universes`

Rules:

- Update `config_version` when runtime defaults change.
- Update `strategy_version` when setup logic or signal semantics change.
- Prefer config edits over hardcoding new thresholds into Python modules.
