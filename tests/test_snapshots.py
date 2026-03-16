import pandas as pd

from trade_idea_generator.features import compute_index_features, compute_universe_breadth
from trade_idea_generator.ranking import build_action_board, build_entry_plans, generate_member_trade_ideas, generate_trade_ideas
from trade_idea_generator.schemas import validate_payload
from trade_idea_generator.signals import build_market_regime, build_risk_budget, build_tripwires, compute_signal_scores
from trade_idea_generator.snapshots import snapshot_from_state


def test_snapshot_validates_against_schema(settings, synthetic_close, synthetic_members):
    features = compute_index_features(synthetic_close, settings)
    breadth = compute_universe_breadth(synthetic_members, settings)
    signal_scores, composite = compute_signal_scores(features, breadth, settings)
    regime = build_market_regime(features, breadth, composite, settings)
    constituents = pd.DataFrame({"Symbol": synthetic_members.columns, "Name": synthetic_members.columns, "Sector": ["Tech"] * len(synthetic_members.columns)})
    member_ideas = generate_member_trade_ideas(synthetic_members, constituents, settings)
    action_board = build_action_board(member_ideas, settings)
    trade_ideas = generate_trade_ideas(features, breadth, regime, settings)
    state = {
        "market_name": "Synthetic",
        "ticker": "SYN",
        "close": synthetic_close,
        "member_prices": synthetic_members,
        "signal_scores": signal_scores,
        "regime": regime,
        "trade_ideas": trade_ideas,
        "action_board": action_board,
        "tripwires": build_tripwires(features, breadth, regime),
        "risk_budget": build_risk_budget(regime, build_tripwires(features, breadth, regime), len(action_board)),
        "entry_plans": build_entry_plans(trade_ideas, action_board),
        "data_quality": {"index_rows": len(synthetic_close)},
    }
    snapshot = snapshot_from_state(state, settings, as_of="2026-03-16")
    payload = snapshot.to_dict()
    validate_payload(payload, "market_snapshot.schema.json")
    validate_payload({"trade_ideas": payload["trade_ideas"]}, "trade_idea_list.schema.json")
    validate_payload({"action_board": payload["action_board"]}, "action_board.schema.json")
