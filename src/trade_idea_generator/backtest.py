from __future__ import annotations

import pandas as pd

from .config import Settings
from .features import compute_index_features
from .models import BacktestResult
from .ranking import setup_masks
from .utils import safe_float


def _simulate_trades(index_features: pd.DataFrame, entries: pd.Series, direction: str, holding_period: int, minimum_gap_days: int, transaction_cost_bps: float, slippage_bps: float) -> list[dict[str, float | str]]:
    close = index_features["close"]
    atr = index_features["atr14"].fillna(close * 0.03)
    trades: list[dict[str, float | str]] = []
    next_allowed = 0
    total_cost = (transaction_cost_bps + slippage_bps) / 10000.0
    for idx, dt in enumerate(close.index):
        if idx < next_allowed or not bool(entries.iloc[idx]):
            continue
        if idx + 1 >= len(close):
            break
        entry_idx = idx + 1
        entry_price = safe_float(close.iloc[entry_idx])
        current_atr = safe_float(atr.iloc[entry_idx], entry_price * 0.03)
        if direction == "LONG":
            stop = entry_price - 2 * current_atr
            target = entry_price + 2.5 * current_atr
        else:
            stop = entry_price + 2 * current_atr
            target = entry_price - 2.5 * current_atr
        exit_idx = min(entry_idx + holding_period, len(close) - 1)
        exit_price = safe_float(close.iloc[exit_idx])
        outcome = "time_exit"
        for scan_idx in range(entry_idx + 1, min(entry_idx + holding_period + 1, len(close))):
            scan_price = safe_float(close.iloc[scan_idx])
            if direction == "LONG" and scan_price <= stop:
                exit_idx, exit_price, outcome = scan_idx, stop, "stop"
                break
            if direction == "LONG" and scan_price >= target:
                exit_idx, exit_price, outcome = scan_idx, target, "target"
                break
            if direction == "SHORT" and scan_price >= stop:
                exit_idx, exit_price, outcome = scan_idx, stop, "stop"
                break
            if direction == "SHORT" and scan_price <= target:
                exit_idx, exit_price, outcome = scan_idx, target, "target"
                break
        gross_return = (exit_price / entry_price - 1.0) if direction == "LONG" else (entry_price / exit_price - 1.0)
        trades.append({"signal_date": str(dt.date()), "entry_date": str(close.index[entry_idx].date()), "exit_date": str(close.index[exit_idx].date()), "direction": direction, "entry_price": round(entry_price, 4), "exit_price": round(exit_price, 4), "gross_return": round(gross_return, 6), "net_return": round(gross_return - total_cost, 6), "outcome": outcome, "holding_days": int(exit_idx - entry_idx)})
        next_allowed = exit_idx + minimum_gap_days
    return trades


def _summarize_trades(trades: list[dict[str, float | str]]) -> dict[str, float]:
    if not trades:
        return {"trades": 0.0, "win_rate": 0.0, "average_return": 0.0, "median_return": 0.0, "cumulative_return": 0.0, "max_drawdown": 0.0}
    returns = pd.Series([float(trade["net_return"]) for trade in trades])
    curve = (1 + returns).cumprod()
    drawdown = curve / curve.cummax() - 1.0
    return {"trades": float(len(trades)), "win_rate": float((returns > 0).mean()), "average_return": float(returns.mean()), "median_return": float(returns.median()), "cumulative_return": float(curve.iloc[-1] - 1.0), "max_drawdown": float(drawdown.min())}


def run_backtest(close: pd.Series, settings: Settings, market_name: str) -> BacktestResult:
    index_features = compute_index_features(close, settings)
    masks = setup_masks(index_features, settings)
    holding_period = int(settings.backtest["holding_period_days"])
    minimum_gap_days = int(settings.backtest["minimum_gap_days"])
    transaction_cost_bps = float(settings.backtest["transaction_cost_bps"])
    slippage_bps = float(settings.backtest["slippage_bps"])
    setup_definitions = [("trend_pullback_long", "LONG"), ("breakout_continuation_long", "LONG"), ("oversold_bounce_long", "LONG"), ("trend_failure_short", "SHORT")]
    breakdowns = []
    all_trades: list[dict[str, float | str]] = []
    for setup_key, direction in setup_definitions:
        trades = _simulate_trades(index_features, masks[setup_key].fillna(False), direction, holding_period, minimum_gap_days, transaction_cost_bps, slippage_bps)
        summary = _summarize_trades(trades)
        breakdowns.append({"setup_key": setup_key, "direction": direction, "summary_metrics": {key: round(value, 6) for key, value in summary.items()}, "trades": trades[:25]})
        all_trades.extend(trades)
    summary_metrics = {key: round(value, 6) for key, value in _summarize_trades(all_trades).items()}
    return BacktestResult(market=market_name, strategy_version=settings.strategy_version, config_version=settings.config_version, test_window={"start": str(index_features.index.min().date()) if not index_features.empty else "", "end": str(index_features.index.max().date()) if not index_features.empty else ""}, entry_rule="Enter next session after a setup fires using the standardized setup definitions.", exit_rule=f"Exit on target, stop, or after {holding_period} trading days, whichever comes first.", cost_assumptions={"transaction_cost_bps": transaction_cost_bps, "slippage_bps": slippage_bps}, summary_metrics=summary_metrics, setup_breakdowns=breakdowns, metadata={"minimum_gap_days": minimum_gap_days, "setup_count": len(setup_definitions)})
