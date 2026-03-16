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


def compute_signal_scores(index_features: pd.DataFrame, breadth: dict[str, pd.Series], settings: Settings, relative_strength: pd.DataFrame | None = None) -> tuple[list[dict[str, object]], float]:
    if index_features.empty:
        return [], 0.0
    thresholds = settings.thresholds
    weights = settings.score_weights
    last = index_features.iloc[-1]
    stack_count = trend_stack(index_features, settings)
    stack_series = pd.Series(
        [
            sum(1 for window in settings.thresholds["ma_windows"] if safe_float(row.get(f"dist_ma{window}"), -1.0) > 0)
            for _, row in index_features.iterrows()
        ],
        index=index_features.index,
    )
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
    slope20 = safe_float(last.get("slope_ma20")) * 100
    slope50 = safe_float(last.get("slope_ma50")) * 100
    trend_slope = (slope20 + slope50) / 2
    add(
        "trend_slope",
        f"{trend_slope:+.2f}%",
        score_signal(trend_slope, 0.2, -0.2, 1.0, -1.0),
        "RISING" if trend_slope > 0.2 else "FALLING" if trend_slope < -0.2 else "FLAT",
        "Average slope of the 20 and 50 day moving averages.",
    )
    efficiency20 = safe_float(last.get("efficiency_20d"), 0.3)
    add(
        "trend_efficiency",
        f"{efficiency20:.2f}",
        score_signal(efficiency20, 0.38, 0.18, 0.8, 0.0),
        "DIRECTED" if efficiency20 >= 0.38 else "CHOPPY" if efficiency20 <= 0.18 else "BALANCED",
        "How efficiently price has moved over the last 20 sessions versus noisy back-and-fill.",
    )
    range_pos = safe_float(last.get("range_pos"), 0.5)
    add("range_position", f"{range_pos:.2f}", score_signal(range_pos, 0.7, 0.3, 1.0, 0.0), "BREAKOUT" if range_pos >= thresholds["range_pos_breakout"] else "BREAKDOWN" if range_pos <= thresholds["range_pos_breakdown"] else "MID", "52 week range position.")
    dist_high = safe_float(last.get("dist_52w_high")) * 100
    add(
        "distance_52w_high",
        f"{dist_high:+.2f}%",
        score_signal(dist_high, -2.0, -12.0, 0.0, -20.0),
        "PRESSING HIGHS" if dist_high >= -2 else "OFF HIGHS" if dist_high <= -12 else "NEAR HIGHS",
        "Distance from the rolling 52 week high.",
    )
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
    vol_term = safe_float(last.get("vol_term_structure"), 1.0)
    add(
        "vol_term_structure",
        f"{vol_term:.2f}x",
        score_signal_inverted(vol_term, 0.9, 1.15, 0.6, 1.5),
        "CALMING" if vol_term <= 0.9 else "STRESSED" if vol_term >= 1.15 else "BALANCED",
        "20 day volatility divided by 60 day volatility.",
    )
    drawdown = safe_float(last.get("drawdown")) * 100
    add("drawdown", f"{drawdown:+.2f}%", score_signal(drawdown, -1.0, -10.0, 0.0, -25.0), "SHALLOW" if drawdown > -5 else "MODERATE" if drawdown > -10 else "SEVERE", "Drawdown from prior peak.")
    roc5 = safe_float(last.get("roc_5d")) * 100
    add("momentum_5d", f"{roc5:+.2f}%", score_signal(roc5, 1.0, -1.0, 4.0, -4.0), "STRONG" if roc5 > 1.5 else "WEAK" if roc5 < -1.5 else "FLAT", "5 day rate of change.")
    roc20 = safe_float(last.get("roc_20d")) * 100
    add("momentum_20d", f"{roc20:+.2f}%", score_signal(roc20, 2.0, -2.0, 8.0, -8.0), "STRONG" if roc20 > 3 else "WEAK" if roc20 < -3 else "FLAT", "20 day rate of change.")
    roc60 = safe_float(last.get("roc_60d")) * 100
    add("momentum_60d", f"{roc60:+.2f}%", score_signal(roc60, 4.0, -4.0, 15.0, -15.0), "STRONG" if roc60 > 5 else "WEAK" if roc60 < -5 else "FLAT", "60 day rate of change.")
    pct_above_50 = breadth.get("pct_above_50")
    if pct_above_50 is not None and len(pct_above_50.dropna()):
        value = safe_float(pct_above_50.iloc[-1])
        add(
            "breadth_short_term",
            f"{value:.0%}",
            score_signal(value, 0.65, 0.45, 0.85, 0.20),
            "BROAD" if value >= 0.65 else "NARROW" if value <= 0.45 else "MIXED",
            "Percent of members above the 50 day moving average.",
        )
    pct_above_200 = breadth.get("pct_above_200")
    if pct_above_200 is not None and len(pct_above_200.dropna()):
        value = safe_float(pct_above_200.iloc[-1])
        add("breadth", f"{value:.0%}", score_signal(value, thresholds["breadth_strong"], thresholds["breadth_weak"], 0.9, 0.2), "STRONG" if value >= thresholds["breadth_strong"] else "WEAK" if value <= thresholds["breadth_weak"] else "MIXED", "Percent of members above the 200 day moving average.")
    breadth_mom = breadth.get("breadth_mom_200")
    if breadth_mom is not None and len(breadth_mom.dropna()):
        value = safe_float(breadth_mom.iloc[-1]) * 100
        add("breadth_momentum", f"{value:+.1f}pp", score_signal(value, 3.0, -3.0, 10.0, -10.0), "IMPROVING" if value > 3 else "DETERIORATING" if value < -3 else "STABLE", "20 day change in percent above the 200 day moving average.")
    stack_delta = safe_float(stack_series.iloc[-1] - stack_series.shift(20).iloc[-1], 0.0)
    breadth_mom_value = safe_float(breadth_mom.iloc[-1], 0.0) if breadth_mom is not None and len(breadth_mom.dropna()) else 0.0
    regime_shift_score = max(
        -1.0,
        min(
            1.0,
            0.45 * score_signal(stack_delta, 1.0, -1.0, 3.0, -3.0)
            + 0.35 * score_signal(roc20, 2.0, -2.0, 8.0, -8.0)
            + 0.20 * score_signal(breadth_mom_value * 100, 3.0, -3.0, 10.0, -10.0),
        ),
    )
    add(
        "regime_shift",
        f"stack Δ20 {stack_delta:+.1f}",
        regime_shift_score,
        "RECOVERY" if regime_shift_score >= 0.35 else "BREAKDOWN" if regime_shift_score <= -0.35 else "STABLE",
        "Change in trend structure, medium-term momentum, and breadth over the last month.",
    )
    breadth_50_value = safe_float(pct_above_50.iloc[-1], 0.0) if pct_above_50 is not None and len(pct_above_50.dropna()) else 0.0
    breadth_200_value = safe_float(pct_above_200.iloc[-1], 0.0) if pct_above_200 is not None and len(pct_above_200.dropna()) else 0.0
    if breadth_50_value <= 0.35 and breadth_mom_value >= 0.04:
        breadth_event_score = 0.35 + 0.45 * clamp((0.35 - breadth_50_value) / 0.20) + 0.20 * clamp((breadth_mom_value - 0.04) / 0.08)
        breadth_event_label = "WASHOUT REVERSAL"
    elif breadth_50_value >= 0.65 and breadth_mom_value >= 0.03:
        breadth_event_score = 0.40 + 0.35 * clamp((breadth_50_value - 0.65) / 0.20) + 0.25 * clamp((breadth_mom_value - 0.03) / 0.07)
        breadth_event_label = "BREADTH THRUST"
    elif breadth_50_value <= 0.25 and breadth_mom_value < 0:
        breadth_event_score = -(0.45 + 0.30 * clamp((0.25 - breadth_50_value) / 0.20) + 0.25 * clamp((-breadth_mom_value) / 0.08))
        breadth_event_label = "BREADTH DAMAGE"
    elif breadth_200_value <= 0.35 and breadth_mom_value < 0:
        breadth_event_score = -(0.35 + 0.35 * clamp((0.35 - breadth_200_value) / 0.20) + 0.30 * clamp((-breadth_mom_value) / 0.08))
        breadth_event_label = "INTERNAL BREAKDOWN"
    else:
        breadth_event_score = 0.25 * score_signal(breadth_50_value, 0.65, 0.45, 0.85, 0.20) + 0.25 * score_signal(breadth_mom_value * 100, 3.0, -3.0, 10.0, -10.0)
        breadth_event_label = "NEUTRAL"
    add(
        "breadth_event",
        f"{breadth_50_value:.0%} / {breadth_mom_value * 100:+.1f}pp",
        max(-1.0, min(1.0, breadth_event_score)),
        breadth_event_label,
        "Breadth thrusts, washout reversals, and internal breakdowns across the member universe.",
    )
    if rv_pct <= 0.25 and roc5 >= 1.0 and range_pos >= 0.60:
        volatility_release_score = 0.45 + 0.25 * clamp((0.25 - rv_pct) / 0.15) + 0.30 * clamp((roc5 - 1.0) / 3.0)
        volatility_release_label = "UPSIDE RELEASE"
    elif rv_pct >= 0.75 and roc5 <= -1.0:
        volatility_release_score = -(0.45 + 0.25 * clamp((rv_pct - 0.75) / 0.20) + 0.30 * clamp((abs(roc5) - 1.0) / 3.0))
        volatility_release_label = "DOWNSIDE EXPANSION"
    elif rv_pct <= 0.25:
        volatility_release_score = 0.20 + 0.30 * clamp((0.25 - rv_pct) / 0.15)
        volatility_release_label = "COILED"
    else:
        volatility_release_score = 0.35 * score_signal_inverted(rv_pct, 0.25, 0.75, 0.0, 1.0) + 0.35 * score_signal_inverted(vol_term, 0.9, 1.15, 0.6, 1.5) + 0.30 * score_signal(roc5, 1.0, -1.0, 4.0, -4.0)
        volatility_release_label = "BALANCED"
    add(
        "volatility_release",
        f"{rv_pct:.0%} / {roc5:+.2f}%",
        max(-1.0, min(1.0, volatility_release_score)),
        volatility_release_label,
        "Whether compression is releasing higher or volatility is expanding lower.",
    )
    relative_strength = relative_strength if relative_strength is not None else pd.DataFrame()
    if not relative_strength.empty and len(relative_strength.dropna(how="all")):
        rs_last = relative_strength.dropna(how="all").iloc[-1]
        rs_gap_20 = safe_float(rs_last.get("rs_gap_20d")) * 100
        rs_gap_60 = safe_float(rs_last.get("rs_gap_60d")) * 100
        rs_vs_ma50 = safe_float(rs_last.get("rs_vs_ma50")) * 100
        rs_score = max(
            -1.0,
            min(
                1.0,
                0.40 * score_signal(rs_gap_20, 1.0, -1.0, 4.0, -4.0)
                + 0.35 * score_signal(rs_gap_60, 2.0, -2.0, 8.0, -8.0)
                + 0.25 * score_signal(rs_vs_ma50, 1.0, -1.0, 5.0, -5.0),
            ),
        )
        add(
            "relative_strength_market",
            f"20d {rs_gap_20:+.2f}pp / 60d {rs_gap_60:+.2f}pp",
            rs_score,
            "LEADING" if rs_score >= 0.35 else "LAGGING" if rs_score <= -0.35 else "INLINE",
            "Relative performance of this market versus its benchmark basket.",
        )
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
