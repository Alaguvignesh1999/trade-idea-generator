from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import Settings
from .features import historical_edge, trend_stack
from .models import ActionBoardItem, EntryPlan, TradeIdea
from .utils import clamp, risk_reward, safe_float


def setup_catalog() -> list[tuple[str, str]]:
    return [
        ("trend_pullback_long", "LONG"),
        ("breakout_continuation_long", "LONG"),
        ("breadth_thrust_long", "LONG"),
        ("volatility_compression_long", "LONG"),
        ("oversold_bounce_long", "LONG"),
        ("trend_failure_short", "SHORT"),
        ("breadth_weakness_short", "SHORT"),
        ("exhaustion_reversal_short", "SHORT"),
    ]


def setup_masks(index_features: pd.DataFrame, settings: Settings, breadth: dict[str, pd.Series] | None = None) -> dict[str, pd.Series]:
    if index_features.empty:
        return {setup_key: pd.Series(dtype=bool) for setup_key, _ in setup_catalog()}
    stack_series = pd.Series(
        [
            sum(1 for window in settings.thresholds["ma_windows"] if safe_float(row.get(f"dist_ma{window}"), -1.0) > 0)
            for _, row in index_features.iterrows()
        ],
        index=index_features.index,
    )
    breadth = breadth or {}
    breadth_50 = breadth.get("pct_above_50", pd.Series(index=index_features.index, dtype=float)).reindex(index_features.index)
    breadth_200 = breadth.get("pct_above_200", pd.Series(index=index_features.index, dtype=float)).reindex(index_features.index)
    breadth_mom = breadth.get("breadth_mom_200", pd.Series(index=index_features.index, dtype=float)).reindex(index_features.index)
    return {
        "trend_pullback_long": (stack_series >= settings.thresholds["trend_stack_bullish"]) & (index_features["range_pos"] >= 0.45) & (index_features["close"] <= index_features["ma20"] * 1.02),
        "breakout_continuation_long": (index_features["range_pos"] >= settings.thresholds["range_pos_breakout"]) & (index_features["rv20_pct"] <= 0.45) & (index_features["close"] >= index_features["ma20"]),
        "breadth_thrust_long": (breadth_50 >= 0.55) & (breadth_mom >= 0.04) & (index_features["close"] >= index_features["ma20"]) & (index_features["roc_20d"] >= 0.0),
        "volatility_compression_long": (index_features["rv20_pct"] <= 0.20) & (index_features["range_pos"] >= 0.60) & (index_features["close"] >= index_features["ma20"]) & (index_features["slope_ma20"] > 0),
        "oversold_bounce_long": (index_features["rsi14"] <= 40) & (index_features["drawdown"] >= -0.12) & (index_features["drawdown"] <= -0.02),
        "trend_failure_short": (stack_series <= settings.thresholds["trend_stack_bearish"]) & (index_features["close"] < index_features["ma20"]) & (index_features["close"] < index_features["ma50"]),
        "breadth_weakness_short": (breadth_200 <= 0.45) & (breadth_mom <= -0.05) & (index_features["close"] < index_features["ma20"]) & (index_features["roc_20d"] <= 0.0),
        "exhaustion_reversal_short": (index_features["rsi14"] >= 68) & (index_features["range_pos"] >= 0.85) & (index_features["roc_5d"] <= 0.0) & (index_features["close"] <= index_features["close"].rolling(5, min_periods=5).max()),
    }


def generate_trade_ideas(
    index_features: pd.DataFrame,
    breadth: dict[str, pd.Series],
    regime: dict[str, object],
    settings: Settings,
    relative_strength: pd.DataFrame | None = None,
) -> list[TradeIdea]:
    if index_features.empty:
        return []
    masks = setup_masks(index_features, settings, breadth=breadth)
    last = index_features.iloc[-1]
    price = safe_float(last.get("close"))
    atr = safe_float(last.get("atr14"), price * 0.03)
    ma20 = safe_float(last.get("ma20"), price)
    ma50 = safe_float(last.get("ma50"), price)
    high20 = safe_float(index_features["close"].rolling(20).max().iloc[-1], price)
    low20 = safe_float(index_features["close"].rolling(20).min().iloc[-1], price)
    high60 = safe_float(index_features["close"].rolling(60).max().iloc[-1], price)
    low60 = safe_float(index_features["close"].rolling(60).min().iloc[-1], price)
    range_pos = safe_float(last.get("range_pos"), 0.5)
    rv_pct = safe_float(last.get("rv20_pct"), 0.5)
    rsi14 = safe_float(last.get("rsi14"), 50.0)
    drawdown = safe_float(last.get("drawdown"), 0.0)
    roc5d = safe_float(last.get("roc_5d"), 0.0)
    roc20d = safe_float(last.get("roc_20d"), 0.0)
    slope_ma20 = safe_float(last.get("slope_ma20"), 0.0)
    efficiency20 = safe_float(last.get("efficiency_20d"), 0.3)
    stack = trend_stack(index_features, settings)
    breadth_50_now = safe_float(breadth.get("pct_above_50").iloc[-1]) if breadth.get("pct_above_50") is not None and len(breadth.get("pct_above_50").dropna()) else math.nan
    breadth_now = safe_float(breadth.get("pct_above_200").iloc[-1]) if breadth.get("pct_above_200") is not None and len(breadth.get("pct_above_200").dropna()) else math.nan
    breadth_mom = safe_float(breadth.get("breadth_mom_200").iloc[-1]) if breadth.get("breadth_mom_200") is not None and len(breadth.get("breadth_mom_200").dropna()) else 0.0
    relative_strength = relative_strength if relative_strength is not None else pd.DataFrame()
    relative_strength = relative_strength.dropna(how="all")
    rs_gap_20d = safe_float(relative_strength.iloc[-1].get("rs_gap_20d"), 0.0) if not relative_strength.empty else 0.0
    rs_gap_60d = safe_float(relative_strength.iloc[-1].get("rs_gap_60d"), 0.0) if not relative_strength.empty else 0.0
    rs_vs_ma50 = safe_float(relative_strength.iloc[-1].get("rs_vs_ma50"), 0.0) if not relative_strength.empty else 0.0
    relative_strength_long = clamp(
        0.45 * clamp((rs_gap_20d + 0.01) / 0.05)
        + 0.35 * clamp((rs_gap_60d + 0.02) / 0.08)
        + 0.20 * clamp((rs_vs_ma50 + 0.01) / 0.04)
    )
    relative_strength_short = clamp(
        0.45 * clamp((-rs_gap_20d + 0.01) / 0.05)
        + 0.35 * clamp((-rs_gap_60d + 0.02) / 0.08)
        + 0.20 * clamp((-rs_vs_ma50 + 0.01) / 0.04)
    )
    trend_quality = clamp((efficiency20 - 0.18) / 0.32)
    reversal_quality = clamp((0.45 - efficiency20) / 0.30)
    holding_period = int(settings.backtest["holding_period_days"])
    ideas: list[TradeIdea] = []

    def make_idea(setup_key: str, name: str, direction: str, suitability: float, entry: float, stop: float, target: float, stretch: float, thesis: str, reasons: list[str], invalidation: str) -> TradeIdea:
        edge = historical_edge(index_features["close"], masks[setup_key], holding_period)
        rr = risk_reward(entry, stop, target, direction)
        sample_score = clamp(edge["sample_size"] / 120.0)
        edge_score = clamp((edge["edge_mean"] + 0.04) / 0.08)
        win_score = clamp((edge["win_rate"] - 0.40) / 0.25)
        rr_score = clamp(rr / 3.0) if not np.isnan(rr) else 0.35
        conviction = 100 * (0.45 * clamp(suitability) + 0.20 * edge_score + 0.15 * win_score + 0.10 * rr_score + 0.10 * sample_score)
        return TradeIdea(
            setup_key=setup_key,
            name=name,
            direction=direction,
            conviction=round(conviction, 1),
            suitability=round(clamp(suitability), 3),
            thesis=thesis,
            signal_reasons=reasons,
            entry=round(entry, 4),
            stop=round(stop, 4),
            target=round(target, 4),
            stretch_target=round(stretch, 4),
            time_horizon_days=holding_period,
            invalidation=invalidation,
            confidence_inputs={
                "sample_score": round(sample_score, 4),
                "edge_score": round(edge_score, 4),
                "win_score": round(win_score, 4),
                "reward_risk_score": round(rr_score, 4),
            },
            historical_context={key: round(value, 6) for key, value in edge.items()},
            backtest_rule=setup_key,
            status="ACTIVE" if conviction >= 60 else "WATCHLIST" if conviction >= 42 else "LOW_PRIORITY",
        )

    ideas.append(make_idea("trend_pullback_long", "Trend Pullback Long", "LONG", 0.30 * (stack / max(len(settings.thresholds["ma_windows"]), 1)) + 0.20 * clamp((range_pos - 0.45) / 0.35) + 0.15 * clamp((safe_float(regime.get("composite")) + 4) / 8) + 0.15 * clamp((0.02 - abs(price - ma20) / max(price, 1.0)) / 0.02 + 0.5) + 0.10 * trend_quality + 0.10 * relative_strength_long, max(ma20, price - 0.5 * atr), min(ma50, price - 2.0 * atr), max(high20, price + 1.8 * atr), max(high60, price + 3.5 * atr), "Use pullbacks inside an intact uptrend when price remains in the upper half of its long range.", ["Trend stack remains constructive.", "Price is close enough to support for a defined stop.", f"Composite backdrop is {safe_float(regime.get('composite')):+.1f}/10.", f"Relative strength backdrop is {rs_gap_20d:+.2%} over 20d."], "Price loses the 50 day moving average or medium-term momentum worsens."))
    ideas.append(make_idea("breakout_continuation_long", "Breakout Continuation Long", "LONG", 0.25 * clamp((range_pos - 0.70) / 0.25) + 0.20 * clamp((0.45 - rv_pct) / 0.25) + 0.20 * clamp((safe_float(regime.get("composite")) + 3) / 8) + 0.20 * trend_quality + 0.15 * relative_strength_long, max(high20, price * 1.002), max(ma20, price - 1.5 * atr), max(high60, price + 2.5 * atr), price + max(4.5 * atr, high20 - low20), "Lean into compression near highs when volatility is still subdued and a breakout can expand.", ["Price is near highs.", "Volatility is not yet stretched.", "Trend efficiency says the tape is moving directionally.", "Relative strength is helping rather than fighting the move."], "Breakout fails back below the trigger zone and 20 day support."))
    ideas.append(make_idea("breadth_thrust_long", "Breadth Thrust Long", "LONG", 0.30 * clamp((safe_float(breadth_50_now, 0.5) - 0.50) / 0.25) + 0.25 * clamp((breadth_mom + 0.02) / 0.10) + 0.10 * clamp((roc20d + 0.03) / 0.08) + 0.10 * clamp((safe_float(regime.get("composite")) + 2) / 8) + 0.10 * trend_quality + 0.15 * relative_strength_long, max(price, high20 * 0.998), max(ma20, price - 1.2 * atr), max(high60, price + 2.0 * atr), price + max(4.0 * atr, high60 - high20), "Press bullish exposure when participation broadens at the same time price is holding trend support.", ["Participation is improving across the universe.", "Breadth momentum is positive rather than merely less bad.", "Price is not fighting the short-term trend.", "Relative strength is confirming the thrust."], "Breadth momentum rolls back over and price slips back below the 20 day moving average."))
    ideas.append(make_idea("volatility_compression_long", "Volatility Compression Long", "LONG", 0.25 * clamp((0.25 - rv_pct) / 0.20 + 0.4) + 0.20 * clamp((range_pos - 0.60) / 0.25) + 0.15 * clamp((slope_ma20 + 0.01) / 0.03) + 0.10 * clamp((roc20d + 0.02) / 0.06) + 0.15 * trend_quality + 0.15 * relative_strength_long, max(high20, price * 1.001), max(ma20, price - 1.3 * atr), max(high60, price + 2.2 * atr), price + max(4.0 * atr, high20 - low20), "Use quiet, tightening conditions near the upper half of the range to prepare for expansion trades.", ["Volatility has compressed.", "The 20 day average is still sloping higher.", "Price is already leaning against the upper half of its range.", "Relative strength says the market can lead if expansion arrives."], "Volatility expands lower first and price breaks back under the 20 day moving average."))
    ideas.append(make_idea("oversold_bounce_long", "Oversold Bounce Long", "LONG", 0.25 * clamp((45 - rsi14) / 20) + 0.20 * clamp((rv_pct - 0.45) / 0.35) + 0.15 * clamp((0.12 - abs(drawdown)) / 0.12 + 0.5) + 0.15 * clamp((breadth_mom + 0.08) / 0.16) + 0.15 * reversal_quality + 0.10 * relative_strength_long, price, min(ma50, price - 2.0 * atr), max(ma20, price + 1.5 * atr), max(ma50, price + 3.0 * atr), "Capture tactical mean reversion after a controlled pullback rather than a full regime break.", ["RSI is stretched lower.", "Drawdown is moderate rather than catastrophic.", "Breadth momentum has room to stabilize.", "Tape quality is choppy enough for reversal trades to matter."], "Fresh lows keep printing and breadth fails to stabilize."))
    ideas.append(make_idea("trend_failure_short", "Trend Failure Short", "SHORT", 0.25 * clamp((2 - stack) / 2) + 0.20 * clamp((-safe_float(regime.get("composite")) - 1) / 6) + 0.15 * clamp((0.55 - range_pos) / 0.35) + 0.15 * clamp(((price < ma20) + (price < ma50)) / 2) + 0.10 * trend_quality + 0.15 * relative_strength_short, min(ma20, price + 0.5 * atr), max(ma50, price + 2.0 * atr), min(low20, price - 1.8 * atr), min(low60, price - 3.5 * atr), "Short failed rallies when price is trapped below declining moving averages and range position is weak.", ["Trend stack is weak.", "Price is below key moving averages.", "Composite conditions do not support aggressive risk-taking.", "Relative strength is lagging rather than leading."], "Price reclaims the 20 and 50 day moving averages with improving momentum."))
    ideas.append(make_idea("breadth_weakness_short", "Breadth Weakness Short", "SHORT", 0.30 * clamp((0.55 - safe_float(breadth_now, 0.5)) / 0.20) + 0.25 * clamp((-breadth_mom) / 0.10) + 0.10 * clamp((2 - stack) / 2) + 0.10 * clamp((-roc20d + 0.01) / 0.06) + 0.05 * trend_quality + 0.20 * relative_strength_short, min(ma20, price + 0.25 * atr), max(ma50, price + 1.5 * atr), min(low20, price - 1.0 * atr), min(low60, price - 2.0 * atr), "Use tactical short exposure when the index is masking internal weakness and participation keeps deteriorating.", ["Participation is narrow.", "Breadth momentum is deteriorating.", "Defensive setups fit the current backdrop.", "Relative strength is rolling over versus the benchmark."], "Breadth expands back above trend-confirming levels."))
    ideas.append(make_idea("exhaustion_reversal_short", "Exhaustion Reversal Short", "SHORT", 0.25 * clamp((rsi14 - 65) / 15) + 0.20 * clamp((range_pos - 0.80) / 0.20) + 0.15 * clamp((-roc5d + 0.01) / 0.05) + 0.10 * clamp((rv_pct - 0.30) / 0.30) + 0.15 * reversal_quality + 0.15 * relative_strength_short, min(price, ma20 * 0.998), max(high20, price + 1.7 * atr), min(ma50, price - 1.8 * atr), min(low20, price - 3.0 * atr), "Fade stretched, stalling tape when momentum stops confirming new highs.", ["RSI is elevated.", "Short-term momentum has rolled over.", "Price is extended toward the top of its range.", "Relative strength is no longer confirming the headline move."], "Momentum re-accelerates higher and price breaks out cleanly to fresh highs."))
    ideas = sorted(ideas, key=lambda item: (item.conviction, item.historical_context["sample_size"]), reverse=True)
    return ideas[: int(settings.trade_idea["idea_limit"])]


def generate_member_trade_ideas(member_prices: pd.DataFrame, constituents: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    if member_prices.empty or constituents.empty:
        return pd.DataFrame()
    close = member_prices.ffill()
    latest = pd.DataFrame({"Symbol": close.columns, "Close": close.iloc[-1].values, "MA20": close.rolling(20, min_periods=20).mean().iloc[-1].values, "MA50": close.rolling(50, min_periods=50).mean().iloc[-1].values, "MA200": close.rolling(200, min_periods=200).mean().iloc[-1].values, "ROC20": close.pct_change(20).iloc[-1].values, "RangePos": ((close - close.rolling(252, min_periods=252).min()) / (close.rolling(252, min_periods=252).max() - close.rolling(252, min_periods=252).min()).replace(0, np.nan)).iloc[-1].values, "Drawdown": (close / close.cummax() - 1.0).iloc[-1].values, "ATRProxy": (close.pct_change().abs().rolling(14, min_periods=14).mean() * close).iloc[-1].values})
    latest["RSI14"] = close.apply(lambda col: col.diff().pipe(lambda delta: 100 - (100 / (1 + delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean() / (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean().replace(0, np.nan))))).iloc[-1].values
    latest["TrendStack"] = (latest["Close"] > latest["MA20"]).astype(int) + (latest["Close"] > latest["MA50"]).astype(int) + (latest["Close"] > latest["MA200"]).astype(int)
    latest = latest.merge(constituents, on="Symbol", how="left")
    latest["LongScore"] = 0.35 * (latest["TrendStack"] / 3.0) + 0.20 * latest["RangePos"].clip(0, 1) + 0.20 * ((latest["ROC20"] + 0.10) / 0.20).clip(0, 1) + 0.15 * ((latest["Close"] / latest["MA200"] - 1.0 + 0.10) / 0.20).clip(0, 1) + 0.10 * (1 - ((latest["RSI14"] - 55).abs() / 45).clip(0, 1))
    latest["ShortScore"] = 0.35 * ((3 - latest["TrendStack"]) / 3.0) + 0.20 * (1 - latest["RangePos"].clip(0, 1)) + 0.20 * ((-latest["ROC20"] + 0.10) / 0.20).clip(0, 1) + 0.15 * ((-(latest["Close"] / latest["MA200"] - 1.0) + 0.10) / 0.20).clip(0, 1) + 0.10 * ((latest["RSI14"] - 35).clip(0, 65) / 65)

    def build_rows(direction: str, score_column: str, setup_key: str, limit: int) -> list[dict[str, object]]:
        rows = []
        ranked = latest.sort_values(score_column, ascending=False).head(limit)
        for _, row in ranked.iterrows():
            atr = safe_float(row["ATRProxy"], safe_float(row["Close"]) * 0.03)
            if direction == "LONG":
                stop = safe_float(row["Close"]) - 2 * atr
                target = max(safe_float(row["MA20"], safe_float(row["Close"]) + 1.5 * atr), safe_float(row["Close"]) + 2 * atr)
            else:
                stop = safe_float(row["Close"]) + 2 * atr
                target = min(safe_float(row["MA20"], safe_float(row["Close"]) - 1.5 * atr), safe_float(row["Close"]) - 2 * atr)
            rows.append({"symbol": str(row["Symbol"]), "name": str(row.get("Name", row["Symbol"])), "sector": str(row.get("Sector", "Unknown") or "Unknown"), "direction": direction, "conviction": round(clamp(safe_float(row[score_column])) * 100, 1), "setup_key": setup_key, "rationale": f"{direction.title()} score {safe_float(row[score_column]):.2f} with ROC20 {safe_float(row['ROC20']):+.2%}.", "entry": round(safe_float(row["Close"]), 4), "stop": round(stop, 4), "target": round(target, 4)})
        return rows

    rows = build_rows("LONG", "LongScore", "constituent_trend_long", 8) + build_rows("SHORT", "ShortScore", "constituent_weak_short", 4)
    ideas = pd.DataFrame(rows)
    if ideas.empty:
        return ideas
    ideas = ideas.sort_values(["conviction", "direction"], ascending=[False, True]).drop_duplicates(subset=["symbol", "setup_key"]).reset_index(drop=True)
    return ideas.head(int(settings.trade_idea["member_idea_limit"]))


def build_action_board(member_ideas: pd.DataFrame, settings: Settings) -> list[ActionBoardItem]:
    if member_ideas.empty:
        return []
    board = member_ideas.copy()
    board["sector_rank"] = board.groupby(["direction", "sector"]).cumcount()
    board["bucket_rank"] = board.groupby(["direction", "setup_key"]).cumcount()
    board["diversified_score"] = board["conviction"] - board["sector_rank"] * 8.0 - board["bucket_rank"] * 3.0
    selected: list[ActionBoardItem] = []
    sector_caps = {"LONG": 2, "SHORT": 1}
    sector_counts: dict[tuple[str, str], int] = {}
    for _, row in board.sort_values(["diversified_score", "conviction"], ascending=[False, False]).iterrows():
        key = (str(row["direction"]), str(row["sector"]))
        if sector_counts.get(key, 0) >= sector_caps.get(str(row["direction"]), 1):
            continue
        sector_counts[key] = sector_counts.get(key, 0) + 1
        selected.append(ActionBoardItem(symbol=str(row["symbol"]), name=str(row["name"]), sector=str(row["sector"]), direction=str(row["direction"]), conviction=round(safe_float(row["conviction"]), 1), diversified_score=round(safe_float(row["diversified_score"]), 1), setup_key=str(row["setup_key"]), rationale=str(row["rationale"]), entry=round(safe_float(row["entry"]), 4), stop=round(safe_float(row["stop"]), 4), target=round(safe_float(row["target"]), 4)))
        if len(selected) >= int(settings.trade_idea["action_board_limit"]):
            break
    return selected


def build_entry_plans(trade_ideas: list[TradeIdea], action_board: list[ActionBoardItem]) -> list[EntryPlan]:
    plans: list[EntryPlan] = []
    for idea in trade_ideas[:4]:
        risk_gap = abs(idea.entry - idea.stop)
        plans.append(EntryPlan(layer="index", item=idea.name, direction=idea.direction, trigger_entry=round(idea.entry, 4), pullback_entry=round(max(idea.stop, idea.entry - 0.33 * risk_gap) if idea.direction == "LONG" else min(idea.stop, idea.entry + 0.33 * risk_gap), 4), failure_level=round(idea.stop, 4), target=round(idea.target, 4), execution_note="Use breakout trigger" if "breakout" in idea.setup_key else "Prefer pullback fill" if "pullback" in idea.setup_key else "Scale only if tape confirms"))
    for item in action_board[:6]:
        risk_gap = abs(item.entry - item.stop)
        plans.append(EntryPlan(layer="constituent", item=item.symbol, direction=item.direction, trigger_entry=round(item.entry, 4), pullback_entry=round(max(item.stop, item.entry - 0.33 * risk_gap) if item.direction == "LONG" else min(item.stop, item.entry + 0.33 * risk_gap), 4), failure_level=round(item.stop, 4), target=round(item.target, 4), execution_note="Best in sector" if item.diversified_score >= 85 else "Add selectively" if item.diversified_score >= 70 else "Treat as hedge"))
    return plans
