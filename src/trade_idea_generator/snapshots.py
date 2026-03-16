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
from .features import compute_index_features, compute_universe_breadth
from .models import BacktestResult, Snapshot
from .ranking import build_action_board, build_entry_plans, generate_member_trade_ideas, generate_trade_ideas
from .schemas import validate_payload
from .signals import build_market_regime, build_risk_budget, build_tripwires, compute_signal_scores
from .utils import slugify


def build_state(settings: Settings, market_name: str) -> dict[str, Any]:
    close = load_index_close(settings, market_name)
    index_features = compute_index_features(close, settings)
    member_prices, constituents = load_member_universe_close(settings, market_name)
    breadth = compute_universe_breadth(member_prices, settings)
    signal_scores, composite = compute_signal_scores(index_features, breadth, settings)
    regime = build_market_regime(index_features, breadth, composite, settings)
    trade_ideas = generate_trade_ideas(index_features, breadth, regime, settings)
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


def snapshot_from_state(state: dict[str, Any], settings: Settings, as_of: str | None = None) -> Snapshot:
    as_of = as_of or str(date.today())
    snapshot = Snapshot(
        as_of=as_of,
        market=state["market_name"],
        data_quality=state["data_quality"],
        regime=state["regime"],
        signal_scores=state["signal_scores"],
        trade_ideas=[idea.to_dict() for idea in state["trade_ideas"]],
        action_board=[item.to_dict() for item in state["action_board"]],
        tripwires=[wire.to_dict() for wire in state["tripwires"]],
        risk_budget=state["risk_budget"],
        entry_plans=[plan.to_dict() for plan in state["entry_plans"]],
        metadata={
            "ticker": state["ticker"],
            "config_version": settings.config_version,
            "strategy_version": settings.strategy_version,
            "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "source_health": {
                "index_history_available": bool(len(state["close"])),
                "member_universe_available": bool(not state["member_prices"].empty),
                "stale_warning": len(state["close"]) > 0 and str(pd.Timestamp(state["close"].index[-1]).date()) != as_of,
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
    snapshot = snapshot_from_state(state, settings, as_of=as_of)
    backtest = run_backtest(state["close"], settings, market_name)
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
