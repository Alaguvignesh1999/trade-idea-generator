from __future__ import annotations

import json
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .backtest import run_backtest
from .config import Settings
from .data import health_summary, load_index_close, load_member_universe_close
from .features import compute_index_features, compute_relative_strength_features, compute_universe_breadth
from .models import BacktestResult, Snapshot
from .ranking import build_action_board, build_entry_plans, generate_member_trade_ideas, generate_trade_ideas
from .schemas import validate_payload
from .signals import build_market_regime, build_risk_budget, build_tripwires, compute_signal_scores
from .utils import clamp, slugify


def build_benchmark_close(settings: Settings, market_name: str) -> tuple[str, pd.Series]:
    benchmark_market = "S&P 500"
    if market_name != benchmark_market and benchmark_market in settings.indices:
        return benchmark_market, load_index_close(settings, benchmark_market)

    peer_markets = [name for name in settings.indices if name != market_name]
    peer_series = [load_index_close(settings, name).rename(name) for name in peer_markets]
    if not peer_series:
        return market_name, pd.Series(dtype=float, name=market_name)
    peers = pd.concat(peer_series, axis=1).sort_index().ffill().dropna(how="all")
    if peers.empty:
        return "Peer basket", pd.Series(dtype=float, name="Peer basket")
    normalized = peers.apply(lambda series: series / series.dropna().iloc[0] if len(series.dropna()) else series)
    benchmark_close = normalized.mean(axis=1).rename("Peer basket")
    return "Peer basket", benchmark_close


def build_state(settings: Settings, market_name: str) -> dict[str, Any]:
    close = load_index_close(settings, market_name)
    index_features = compute_index_features(close, settings)
    member_prices, constituents = load_member_universe_close(settings, market_name)
    breadth = compute_universe_breadth(member_prices, settings)
    benchmark_label, benchmark_close = build_benchmark_close(settings, market_name)
    relative_strength = compute_relative_strength_features(close, benchmark_close)
    signal_scores, composite = compute_signal_scores(index_features, breadth, settings, relative_strength=relative_strength)
    regime = build_market_regime(index_features, breadth, composite, settings)
    trade_ideas = generate_trade_ideas(index_features, breadth, regime, settings, relative_strength=relative_strength)
    member_ideas = generate_member_trade_ideas(member_prices, constituents, settings)
    action_board = build_action_board(member_ideas, settings)
    tripwires = build_tripwires(index_features, breadth, regime)
    risk_budget = build_risk_budget(regime, tripwires, len(action_board))
    entry_plans = build_entry_plans(trade_ideas, action_board)
    return {
        "market_name": market_name,
        "ticker": settings.indices[market_name],
        "close": close,
        "index_features": index_features,
        "member_prices": member_prices,
        "constituents": constituents,
        "breadth": breadth,
        "benchmark_close": benchmark_close,
        "benchmark_label": benchmark_label,
        "relative_strength": relative_strength,
        "signal_scores": signal_scores,
        "regime": regime,
        "trade_ideas": trade_ideas,
        "member_ideas": member_ideas,
        "action_board": action_board,
        "tripwires": tripwires,
        "risk_budget": risk_budget,
        "entry_plans": entry_plans,
        "data_quality": health_summary(close, constituents, member_prices),
    }


def _clean_number(value: Any, *, scale: float = 1.0, digits: int = 3) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value) * scale, digits)


def build_chartbook(state: dict[str, Any], lookback: int = 252) -> dict[str, list[dict[str, float | str | None]]]:
    index_features: pd.DataFrame = state["index_features"]
    breadth: dict[str, pd.Series] = state["breadth"]
    relative_strength: pd.DataFrame = state.get("relative_strength", pd.DataFrame())
    if index_features.empty:
        return {"price_history": [], "oscillator_history": [], "breadth_history": [], "relative_strength_history": [], "signal_family_history": []}

    tail = index_features.tail(lookback).copy()
    breadth_50 = breadth.get("pct_above_50", pd.Series(dtype=float)).reindex(tail.index)
    breadth_200 = breadth.get("pct_above_200", pd.Series(dtype=float)).reindex(tail.index)
    breadth_mom = breadth.get("breadth_mom_200", pd.Series(dtype=float)).reindex(tail.index)
    relative_tail = relative_strength.reindex(tail.index)

    price_history = [
        {
            "date": str(pd.Timestamp(idx).date()),
            "close": _clean_number(row.get("close"), digits=2),
            "ma20": _clean_number(row.get("ma20"), digits=2),
            "ma50": _clean_number(row.get("ma50"), digits=2),
            "ma200": _clean_number(row.get("ma200"), digits=2),
            "drawdown_pct": _clean_number(row.get("drawdown"), scale=100, digits=2),
        }
        for idx, row in tail.iterrows()
    ]
    oscillator_history = [
        {
            "date": str(pd.Timestamp(idx).date()),
            "rsi14": _clean_number(row.get("rsi14"), digits=1),
            "volatility_percentile": _clean_number(row.get("rv20_pct"), scale=100, digits=1),
            "range_position": _clean_number(row.get("range_pos"), scale=100, digits=1),
            "momentum_20d": _clean_number(row.get("roc_20d"), scale=100, digits=2),
        }
        for idx, row in tail.iterrows()
    ]
    breadth_history = [
        {
            "date": str(pd.Timestamp(idx).date()),
            "pct_above_50": _clean_number(breadth_50.loc[idx], scale=100, digits=1),
            "pct_above_200": _clean_number(breadth_200.loc[idx], scale=100, digits=1),
            "breadth_momentum": _clean_number(breadth_mom.loc[idx], scale=100, digits=1),
        }
        for idx in tail.index
    ]
    trend_stack_series = pd.Series(
        [
            sum(1 for window in [10, 20, 50, 100, 200] if pd.notna(tail.iloc[pos].get(f"dist_ma{window}")) and float(tail.iloc[pos].get(f"dist_ma{window}")) > 0)
            for pos in range(len(tail))
        ],
        index=tail.index,
    )
    stack_delta_20 = trend_stack_series - trend_stack_series.shift(20)
    breadth_thrust = ((breadth_50 - 0.55) * 2.2 + breadth_mom * 4.0).reindex(tail.index)
    washout_reversal = (((0.30 - breadth_50).clip(lower=0)) * 2.5 + breadth_mom * 5.0).reindex(tail.index)
    volatility_release = ((0.35 - tail["rv20_pct"]).clip(lower=-1.0) + tail["roc_5d"].fillna(0.0) * 6.0 - (tail["vol_term_structure"].fillna(1.0) - 1.0)).reindex(tail.index)
    relative_strength_history = [
        {
            "date": str(pd.Timestamp(idx).date()),
            "rs_gap_20d": _clean_number(relative_tail.loc[idx].get("rs_gap_20d"), scale=100, digits=2) if idx in relative_tail.index else None,
            "rs_gap_60d": _clean_number(relative_tail.loc[idx].get("rs_gap_60d"), scale=100, digits=2) if idx in relative_tail.index else None,
            "rs_vs_ma50": _clean_number(relative_tail.loc[idx].get("rs_vs_ma50"), scale=100, digits=2) if idx in relative_tail.index else None,
        }
        for idx in tail.index
    ]
    signal_family_history = [
        {
            "date": str(pd.Timestamp(idx).date()),
            "regime_shift": _clean_number(stack_delta_20.loc[idx], digits=2),
            "breadth_thrust": _clean_number(breadth_thrust.loc[idx], digits=2),
            "washout_reversal": _clean_number(washout_reversal.loc[idx], digits=2),
            "volatility_release": _clean_number(volatility_release.loc[idx], digits=2),
        }
        for idx in tail.index
    ]
    return {
        "price_history": price_history,
        "oscillator_history": oscillator_history,
        "breadth_history": breadth_history,
        "relative_strength_history": relative_strength_history,
        "signal_family_history": signal_family_history,
    }


def build_setup_diagnostics(backtest: BacktestResult, minimum_samples: int) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for breakdown in backtest.setup_breakdowns:
        summary = breakdown["summary_metrics"]
        trades = int(summary.get("trades", 0))
        average_return = float(summary.get("average_return", 0.0))
        cumulative_return = float(summary.get("cumulative_return", 0.0))
        win_rate = float(summary.get("win_rate", 0.0))
        max_drawdown = float(summary.get("max_drawdown", 0.0))
        quality_score = round(
            100
            * (
                0.25 * clamp(trades / max(minimum_samples * 3, 1))
                + 0.25 * clamp((average_return + 0.01) / 0.03)
                + 0.2 * clamp((win_rate - 0.40) / 0.25)
                + 0.2 * clamp((cumulative_return + 0.05) / 0.25)
                + 0.1 * clamp((0.30 + max_drawdown) / 0.30)
            ),
            1,
        )
        if trades >= minimum_samples and average_return > 0 and cumulative_return > 0 and win_rate >= 0.5 and max_drawdown >= -0.15:
            verdict = "FAVORABLE"
        elif trades >= minimum_samples and (average_return > 0 or cumulative_return > 0 or win_rate >= 0.5):
            verdict = "MIXED"
        else:
            verdict = "WEAK"
        diagnostics.append(
            {
                "setup_key": str(breakdown["setup_key"]),
                "direction": str(breakdown["direction"]),
                "trades": trades,
                "win_rate": round(win_rate, 4),
                "average_return": round(average_return, 6),
                "cumulative_return": round(cumulative_return, 6),
                "max_drawdown": round(max_drawdown, 6),
                "quality_score": quality_score,
                "verdict": verdict,
            }
        )
    return sorted(diagnostics, key=lambda row: row["quality_score"], reverse=True)


def decorate_trade_ideas(trade_ideas: list[Any], setup_diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostics_lookup = {row["setup_key"]: row for row in setup_diagnostics}
    decorated: list[dict[str, Any]] = []
    for idea in trade_ideas:
        payload = idea.to_dict()
        diagnostic = diagnostics_lookup.get(payload["setup_key"])
        if diagnostic:
            payload["backtest_trades"] = diagnostic["trades"]
            payload["backtest_win_rate"] = diagnostic["win_rate"]
            payload["backtest_average_return"] = diagnostic["average_return"]
            payload["quality_score"] = diagnostic["quality_score"]
            payload["quality_verdict"] = diagnostic["verdict"]
            if diagnostic["verdict"] == "WEAK":
                payload["status"] = "AVOID"
            elif diagnostic["verdict"] == "FAVORABLE" and float(payload.get("conviction", 0.0)) >= 55:
                payload["status"] = "ACTIVE"
            else:
                payload["status"] = "WATCHLIST"
        decorated.append(payload)
    return decorated


def snapshot_from_state(state: dict[str, Any], settings: Settings, backtest: BacktestResult | None = None, as_of: str | None = None) -> Snapshot:
    as_of = as_of or str(date.today())
    setup_diagnostics = build_setup_diagnostics(backtest, int(settings.trade_idea["minimum_samples"])) if backtest else []
    snapshot = Snapshot(
        as_of=as_of,
        market=state["market_name"],
        data_quality=state["data_quality"],
        regime=state["regime"],
        signal_scores=state["signal_scores"],
        trade_ideas=decorate_trade_ideas(state["trade_ideas"], setup_diagnostics),
        action_board=[item.to_dict() for item in state["action_board"]],
        tripwires=[wire.to_dict() for wire in state["tripwires"]],
        risk_budget=state["risk_budget"],
        entry_plans=[plan.to_dict() for plan in state["entry_plans"]],
        metadata={
            "ticker": state["ticker"],
            "benchmark": state.get("benchmark_label", ""),
            "config_version": settings.config_version,
            "strategy_version": settings.strategy_version,
            "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "source_health": {
                "index_history_available": bool(len(state["close"])),
                "member_universe_available": bool(not state["member_prices"].empty),
                "stale_warning": len(state["close"]) > 0 and str(pd.Timestamp(state["close"].index[-1]).date()) != as_of,
            },
        },
        research={
            "chartbook": build_chartbook(state),
            "setup_diagnostics": setup_diagnostics,
            "summary": {
                "favorable_setups": sum(1 for row in setup_diagnostics if row["verdict"] == "FAVORABLE"),
                "watchlist_setups": sum(1 for row in setup_diagnostics if row["verdict"] == "MIXED"),
                "weak_setups": sum(1 for row in setup_diagnostics if row["verdict"] == "WEAK"),
            },
        },
    )
    payload = snapshot.to_dict()
    validate_payload(payload, "market_snapshot.schema.json")
    validate_payload({"trade_ideas": payload["trade_ideas"]}, "trade_idea_list.schema.json")
    validate_payload({"action_board": payload["action_board"]}, "action_board.schema.json")
    return snapshot


def write_artifacts(settings: Settings, snapshot: Snapshot, backtest: BacktestResult) -> dict[str, str]:
    run_dir = settings.artifact_dir / "runs" / snapshot.as_of / "markets" / slugify(snapshot.market)
    latest_dir = settings.artifact_dir / "latest" / "markets" / slugify(snapshot.market)
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = run_dir / "snapshot.json"
    backtest_path = run_dir / "backtest.json"
    snapshot_path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
    backtest_path.write_text(json.dumps(backtest.to_dict(), indent=2), encoding="utf-8")
    validate_payload(json.loads(snapshot_path.read_text(encoding="utf-8")), "market_snapshot.schema.json")
    validate_payload(json.loads(backtest_path.read_text(encoding="utf-8")), "backtest_result.schema.json")

    shutil.copy2(snapshot_path, latest_dir / "snapshot.json")
    shutil.copy2(backtest_path, latest_dir / "backtest.json")
    return {
        "snapshot_path": str(snapshot_path),
        "backtest_path": str(backtest_path),
        "latest_snapshot_path": str(latest_dir / "snapshot.json"),
        "latest_backtest_path": str(latest_dir / "backtest.json"),
    }


def write_manifest(settings: Settings, market_records: list[dict[str, Any]], as_of: str) -> Path:
    payload = {
        "as_of": as_of,
        "config_version": settings.config_version,
        "strategy_version": settings.strategy_version,
        "markets": market_records,
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }
    validate_payload(payload, "run_manifest.schema.json")
    run_manifest = settings.artifact_dir / "runs" / as_of / "manifest.json"
    latest_manifest = settings.artifact_dir / "latest.json"
    run_manifest.parent.mkdir(parents=True, exist_ok=True)
    run_manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return run_manifest


def generate_market_outputs(settings: Settings, market_name: str, as_of: str | None = None) -> tuple[Snapshot, BacktestResult, dict[str, str]]:
    state = build_state(settings, market_name)
    backtest = run_backtest(state["close"], settings, market_name, breadth=state["breadth"])
    snapshot = snapshot_from_state(state, settings, backtest=backtest, as_of=as_of)
    validate_payload(backtest.to_dict(), "backtest_result.schema.json")
    paths = write_artifacts(settings, snapshot, backtest)
    return snapshot, backtest, paths


def validate_snapshot_tree(root: Path) -> list[str]:
    checked: list[str] = []
    for path in root.rglob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "snapshot.json":
            validate_payload(payload, "market_snapshot.schema.json")
        elif path.name == "backtest.json":
            validate_payload(payload, "backtest_result.schema.json")
        elif path.name == "manifest.json" or path.name == "latest.json":
            validate_payload(payload, "run_manifest.schema.json")
        checked.append(str(path))
    return checked
