from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Settings
from .features import trend_stack
from .models import Tripwire
from .utils import clamp, safe_float


def score_signal(value: float, bullish_above: float, bearish_below: float, max_bull: float | None = None, max_bear: float | None = None) -> float:
    if np.isnan(value):
        return 0.0
    if value >= bullish_above:
        if max_bull is None or max_bull == bullish_above:
            return 1.0
        return min(1.0, 0.5 + 0.5 * (value - bullish_above) / (max_bull - bullish_above))
    if value <= bearish_below:
        if max_bear is None or max_bear == bearish_below:
            return -1.0
        return max(-1.0, -0.5 - 0.5 * (bearish_below - value) / (bearish_below - max_bear))
    mid = (bullish_above + bearish_below) / 2
    span = max((bullish_above - bearish_below) / 2, 1e-9)
    return (value - mid) / span * 0.5


def score_signal_inverted(value: float, bullish_below: float, bearish_above: float, floor_value: float | None = None, ceiling_value: float | None = None) -> float:
    return -score_signal(value, bearish_above, bullish_below, ceiling_value, floor_value)


def compute_signal_scores(index_features: pd.DataFrame, breadth: dict[str, pd.Series], settings: Settings) -> tuple[list[dict[str, object]], float]:
    if index_features.empty:
        return [], 0.0
    thresholds = settings.thresholds
    weights = settings.score_weights
    last = index_features.iloc[-1]
    stack_count = trend_stack(index_features, settings)
    signals: list[dict[str, object]] = []

    def add(key: str, raw: str, score: float, label: str, detail: str) -> None:
        signals.append(
            {
                "key": key,
                "raw": raw,
                "score": round(float(score), 4),
                "label": label,
                "detail": detail,
                "weight": float(weights.get(key, 1.0)),
            }
        )

    add(
        "trend_stack",
        f"{stack_count}/{len(thresholds['ma_windows'])}",
        score_signal(stack_count, thresholds["trend_stack_bullish"], thresholds["trend_stack_bearish"], len(thresholds["ma_windows"]), 0),
        "BULLISH" if stack_count >= thresholds["trend_stack_bullish"] else "BEARISH" if stack_count <= thresholds["trend_stack_bearish"] else "MIXED",
        "Price above configured moving averages.",
    )
    dist200 = safe_float(last.get("dist_ma200")) * 100
    add("ma200_position", f"{dist200:+.2f}%", score_signal(dist200, 2.0, -2.0, 10.0, -10.0), "ABOVE" if dist200 > 2 else "BELOW" if dist200 < -2 else "AT", "Distance from 200 day moving average.")
    range_pos = safe_float(last.get("range_pos"), 0.5)
    add("range_position", f"{range_pos:.2f}", score_signal(range_pos, 0.7, 0.3, 1.0, 0.0), "BREAKOUT" if range_pos >= thresholds["range_pos_breakout"] else "BREAKDOWN" if range_pos <= thresholds["range_pos_breakdown"] else "MID", "52 week range position.")
    rsi14 = safe_float(last.get("rsi14"), 50.0)
    if rsi14 >= thresholds["rsi_overbought"]:
        rsi_score = -0.5 * min(1.0, (rsi14 - thresholds["rsi_overbought"]) / 15)
        label = "OVERBOUGHT"
    elif rsi14 <= thresholds["rsi_oversold"]:
        rsi_score = 0.5 * min(1.0, (thresholds["rsi_oversold"] - rsi14) / 15)
        label = "OVERSOLD"
    else:
        rsi_score = score_signal(rsi14, 55.0, 45.0, 70.0, 30.0) * 0.3
        label = "NEUTRAL"
    add("rsi_signal", f"{rsi14:.1f}", rsi_score, label, "RSI14 signal state.")
    rv_pct = safe_float(last.get("rv20_pct"), 0.5)
    add("vol_regime", f"{rv_pct:.0%}", score_signal_inverted(rv_pct, 0.2, 0.8, 0.0, 1.0), "ELEVATED" if rv_pct >= 0.8 else "COMPRESSED" if rv_pct <= 0.2 else "NORMAL", "20 day realized volatility percentile.")
    drawdown = safe_float(last.get("drawdown")) * 100
    add("drawdown", f"{drawdown:+.2f}%", score_signal(drawdown, -1.0, -10.0, 0.0, -25.0), "SHALLOW" if drawdown > -5 else "MODERATE" if drawdown > -10 else "SEVERE", "Drawdown from prior peak.")
    roc20 = safe_float(last.get("roc_20d")) * 100
    add("momentum_20d", f"{roc20:+.2f}%", score_signal(roc20, 2.0, -2.0, 8.0, -8.0), "STRONG" if roc20 > 3 else "WEAK" if roc20 < -3 else "FLAT", "20 day rate of change.")
    pct_above_200 = breadth.get("pct_above_200")
    if pct_above_200 is not None and len(pct_above_200.dropna()):
        value = safe_float(pct_above_200.iloc[-1])
        add("breadth", f"{value:.0%}", score_signal(value, thresholds["breadth_strong"], thresholds["breadth_weak"], 0.9, 0.2), "STRONG" if value >= thresholds["breadth_strong"] else "WEAK" if value <= thresholds["breadth_weak"] else "MIXED", "Percent of members above the 200 day moving average.")
    breadth_mom = breadth.get("breadth_mom_200")
    if breadth_mom is not None and len(breadth_mom.dropna()):
        value = safe_float(breadth_mom.iloc[-1]) * 100
        add("breadth_momentum", f"{value:+.1f}pp", score_signal(value, 3.0, -3.0, 10.0, -10.0), "IMPROVING" if value > 3 else "DETERIORATING" if value < -3 else "STABLE", "20 day change in percent above the 200 day moving average.")
    weighted_score = sum(float(row["score"]) * float(row["weight"]) for row in signals)
    max_score = sum(abs(float(row["weight"])) for row in signals) or 1.0
    composite = weighted_score / max_score * 10
    return signals, round(float(composite), 3)


def build_market_regime(index_features: pd.DataFrame, breadth: dict[str, pd.Series], composite: float, settings: Settings) -> dict[str, object]:
    if index_features.empty:
        return {}
    last = index_features.iloc[-1]
    stack = trend_stack(index_features, settings)
    breadth_now = safe_float(breadth.get("pct_above_200").iloc[-1]) if breadth.get("pct_above_200") is not None and len(breadth.get("pct_above_200").dropna()) else np.nan
    drawdown = safe_float(last.get("drawdown"))
    rv_pct = safe_float(last.get("rv20_pct"), 0.5)
    if composite >= 4:
        bias = "Risk-on bullish"
    elif composite <= -4:
        bias = "Risk-off bearish"
    else:
        bias = "Mixed tactical"
    posture = "Add on pullbacks" if composite >= 3 else "Trade selectively" if composite > -3 else "Favor defense"
    return {
        "bias": bias,
        "posture": posture,
        "composite": composite,
        "trend_stack": f"{stack}/{len(settings.thresholds['ma_windows'])}",
        "vol_bucket": "High volatility" if rv_pct >= 0.8 else "Compressed volatility" if rv_pct <= 0.2 else "Normal volatility",
        "tape": "Near highs / stable" if drawdown > -0.05 else "Pullback" if drawdown > -0.1 else "Correction" if drawdown > -0.2 else "Deep drawdown",
        "participation": "Broad participation" if not np.isnan(breadth_now) and breadth_now >= 0.7 else "Narrow participation" if not np.isnan(breadth_now) and breadth_now <= 0.4 else "Mixed participation",
        "bull_probability": round(clamp((composite + 8) / 16) * 100, 1),
        "bear_probability": round(clamp((8 - composite) / 16) * 100, 1)
    }


def build_tripwires(index_features: pd.DataFrame, breadth: dict[str, pd.Series], regime: dict[str, object]) -> list[Tripwire]:
    if index_features.empty:
        return []
    last = index_features.iloc[-1]
    close = safe_float(last.get("close"))
    ma20 = safe_float(last.get("ma20"), close)
    ma50 = safe_float(last.get("ma50"), close)
    ma200 = safe_float(last.get("ma200"), close)
    rv_pct = safe_float(last.get("rv20_pct"), 0.5)
    drawdown = safe_float(last.get("drawdown"), 0.0)
    breadth_now = safe_float(breadth.get("pct_above_200").iloc[-1]) if breadth.get("pct_above_200") is not None and len(breadth.get("pct_above_200").dropna()) else np.nan

    def status(triggered: bool, near: bool) -> str:
        if triggered:
            return "TRIGGERED"
        if near:
            return "NEAR"
        return "CLEAR"

    tripwires = [
        Tripwire("Lose 20DMA", f"{close:.2f}", f"{ma20:.2f}", status(close < ma20, close < ma20 * 1.01), "Short-term trend damage", "Reduce chase risk and demand cleaner entries."),
        Tripwire("Lose 50DMA", f"{close:.2f}", f"{ma50:.2f}", status(close < ma50, close < ma50 * 1.01), "Intermediate trend failure", "Cut gross exposure and raise hedges."),
        Tripwire("Lose 200DMA", f"{close:.2f}", f"{ma200:.2f}", status(close < ma200, close < ma200 * 1.01), "Long-term regime deterioration", "Shift from pro-risk to defense."),
        Tripwire("Volatility shock", f"{rv_pct:.0%}", ">= 80%", status(rv_pct >= 0.8, rv_pct >= 0.7), "Unstable tape", "Trade smaller and raise selectivity."),
        Tripwire("Composite collapse", f"{safe_float(regime.get('composite')):+.1f}", "<= -4.0", status(safe_float(regime.get("composite")) <= -4.0, safe_float(regime.get("composite")) <= -2.5), "Broad bearish alignment", "Treat longs as tactical only."),
        Tripwire("Deep drawdown", f"{drawdown:.1%}", "<= -10%", status(drawdown <= -0.10, drawdown <= -0.07), "Correction behavior", "Favor shorter holding periods and more cash.")
    ]
    if not np.isnan(breadth_now):
        tripwires.append(Tripwire("Breadth breakdown", f"{breadth_now:.0%}", "<= 40%", status(breadth_now <= 0.40, breadth_now <= 0.45), "Internal weakness", "Trust fewer longs and keep hedges active."))
    return sorted(tripwires, key=lambda wire: {"TRIGGERED": 0, "NEAR": 1, "CLEAR": 2}[wire.status])


def build_risk_budget(regime: dict[str, object], tripwires: list[Tripwire], action_board_count: int) -> dict[str, float | str]:
    composite = safe_float(regime.get("composite"), 0.0)
    triggered = sum(1 for wire in tripwires if wire.status == "TRIGGERED")
    near = sum(1 for wire in tripwires if wire.status == "NEAR")
    gross = clamp((95 + composite * 2 - triggered * 8 - near * 3) / 110, 0.35, 1.0) * 100
    net = max(-40.0, min(70.0, composite * 6 - triggered * 5))
    long_target = max(0.0, min(100.0, (gross + net) / 2))
    short_target = max(0.0, min(100.0, gross - long_target))
    cash_target = max(0.0, 100.0 - min(gross, 100.0))
    return {
        "gross_target": round(gross, 1),
        "net_target": round(net, 1),
        "long_target": round(long_target, 1),
        "short_target": round(short_target, 1),
        "cash_target": round(cash_target, 1),
        "hedge_target": round(max(short_target, triggered * 5.0), 1),
        "action_board_depth": action_board_count,
        "posture": str(regime.get("posture", "Trade selectively"))
    }
