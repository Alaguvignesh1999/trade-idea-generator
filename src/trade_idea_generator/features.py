from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Settings


def rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    rs = up.ewm(alpha=1 / period, adjust=False).mean() / down.ewm(alpha=1 / period, adjust=False).mean().replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def realized_vol(returns: pd.Series, window: int) -> pd.Series:
    return returns.rolling(window, min_periods=window).std() * np.sqrt(252)


def atr_proxy(close: pd.Series, window: int) -> pd.Series:
    return close.pct_change().abs().rolling(window, min_periods=window).mean() * close


def rate_of_change(close: pd.Series, periods: list[int]) -> dict[str, pd.Series]:
    return {f"roc_{period}d": close.pct_change(period) for period in periods}


def rolling_percentile(series: pd.Series, window: int) -> pd.Series:
    values = []
    for idx in range(len(series)):
        start = max(0, idx - window + 1)
        sample = series.iloc[start : idx + 1].dropna()
        if len(sample) < 5:
            values.append(np.nan)
            continue
        values.append(float((sample <= series.iloc[idx]).mean()))
    return pd.Series(values, index=series.index)


def ma_slope(close: pd.Series, window: int, slope_period: int = 10) -> pd.Series:
    return close.rolling(window, min_periods=window).mean().pct_change(slope_period)


def efficiency_ratio(close: pd.Series, window: int) -> pd.Series:
    net_change = close.diff(window).abs()
    path_length = close.diff().abs().rolling(window, min_periods=window).sum()
    return net_change / path_length.replace(0, np.nan)


def compute_index_features(close: pd.Series, settings: Settings) -> pd.DataFrame:
    close = close.dropna().copy()
    if close.empty:
        return pd.DataFrame()
    thresholds = settings.thresholds
    returns = close.pct_change()
    drawdown = close / close.cummax() - 1.0
    rv_short = realized_vol(returns, int(thresholds["rv_window"]))
    rv_long = realized_vol(returns, int(thresholds["rv_long_window"]))
    result = pd.DataFrame(
        {
            "close": close,
            "ret1d": returns,
            "drawdown": drawdown,
            "rv20_ann": rv_short,
            "rv60_ann": rv_long,
            "vol_term_structure": rv_short / rv_long.replace(0, np.nan),
            "rsi14": rsi(close, int(thresholds["rsi_period"])),
            "atr14": atr_proxy(close, int(thresholds["atr_window"])),
            "efficiency_20d": efficiency_ratio(close, 20),
        }
    )
    for window in thresholds["ma_windows"]:
        ma = close.rolling(window, min_periods=window).mean()
        result[f"ma{window}"] = ma
        result[f"dist_ma{window}"] = close / ma - 1.0
        result[f"slope_ma{window}"] = ma_slope(close, window)
    range_window = int(thresholds["range_window"])
    high = close.rolling(range_window, min_periods=range_window).max()
    low = close.rolling(range_window, min_periods=range_window).min()
    result["range_pos"] = (close - low) / (high - low).replace(0, np.nan)
    result["dist_52w_high"] = close / high - 1.0
    result["dist_52w_low"] = close / low - 1.0
    for key, series in rate_of_change(close, [5, 20, 60]).items():
        result[key] = series
    result["rv20_pct"] = rolling_percentile(result["rv20_ann"], 252 * 2)
    result["dd_pct"] = rolling_percentile(result["drawdown"], 252 * 2)
    result["range_pos_pct"] = rolling_percentile(result["range_pos"], 252 * 2)
    return result


def compute_universe_breadth(member_prices: pd.DataFrame, settings: Settings) -> dict[str, pd.Series]:
    if member_prices.empty:
        return {}
    thresholds = settings.thresholds
    ma50 = member_prices.rolling(50, min_periods=50).mean()
    ma200 = member_prices.rolling(200, min_periods=200).mean()
    valid50 = ma50.notna()
    valid200 = ma200.notna()
    pct_above_50 = ((member_prices > ma50) & valid50).sum(axis=1) / valid50.sum(axis=1).replace(0, np.nan)
    pct_above_200 = ((member_prices > ma200) & valid200).sum(axis=1) / valid200.sum(axis=1).replace(0, np.nan)
    breadth_mom_200 = pct_above_200 - pct_above_200.shift(int(thresholds["breadth_mom_window"]))
    return {
        "pct_above_50": pct_above_50,
        "pct_above_200": pct_above_200,
        "breadth_mom_200": breadth_mom_200,
        "pct_above_200_pct": rolling_percentile(pct_above_200, 252 * 2),
        "breadth_mom_pct": rolling_percentile(breadth_mom_200, 252 * 2),
    }


def compute_relative_strength_features(close: pd.Series, benchmark_close: pd.Series) -> pd.DataFrame:
    aligned = pd.concat([close.rename("close"), benchmark_close.rename("benchmark")], axis=1).dropna()
    if aligned.empty:
        return pd.DataFrame()
    ratio = aligned["close"] / aligned["benchmark"].replace(0, np.nan)
    rs_ma50 = ratio.rolling(50, min_periods=50).mean()
    rs_ma200 = ratio.rolling(200, min_periods=200).mean()
    market_roc20 = aligned["close"].pct_change(20)
    benchmark_roc20 = aligned["benchmark"].pct_change(20)
    market_roc60 = aligned["close"].pct_change(60)
    benchmark_roc60 = aligned["benchmark"].pct_change(60)
    relative = pd.DataFrame(
        {
            "rs_ratio": ratio,
            "rs_vs_ma50": ratio / rs_ma50.replace(0, np.nan) - 1.0,
            "rs_vs_ma200": ratio / rs_ma200.replace(0, np.nan) - 1.0,
            "rs_gap_20d": market_roc20 - benchmark_roc20,
            "rs_gap_60d": market_roc60 - benchmark_roc60,
        }
    )
    return relative


def trend_stack(df: pd.DataFrame, settings: Settings) -> int:
    last = df.iloc[-1]
    return int(sum(1 for window in settings.thresholds["ma_windows"] if last.get(f"dist_ma{window}", -1.0) > 0))


def historical_edge(close: pd.Series, mask: pd.Series, horizon: int) -> dict[str, float]:
    aligned = close.dropna()
    mask = mask.reindex(aligned.index).fillna(False)
    fwd = aligned.shift(-horizon) / aligned - 1.0
    conditional = fwd[mask].dropna()
    baseline = fwd.dropna()
    if conditional.empty:
        return {"sample_size": 0.0, "mean_return": 0.0, "win_rate": 0.0, "edge_mean": 0.0}
    return {
        "sample_size": float(len(conditional)),
        "mean_return": float(conditional.mean()),
        "win_rate": float((conditional > 0).mean()),
        "edge_mean": float(conditional.mean() - baseline.mean()) if not baseline.empty else 0.0,
    }
