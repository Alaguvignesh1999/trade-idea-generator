from trade_idea_generator.features import compute_index_features, compute_relative_strength_features, compute_universe_breadth
from trade_idea_generator.signals import build_market_regime, build_risk_budget, build_tripwires, compute_signal_scores


def test_signal_scores_and_regime_are_populated(settings, synthetic_close, synthetic_members):
    features = compute_index_features(synthetic_close, settings)
    breadth = compute_universe_breadth(synthetic_members, settings)
    relative_strength = compute_relative_strength_features(synthetic_close, synthetic_close * 0.99)
    signal_scores, composite = compute_signal_scores(features, breadth, settings, relative_strength=relative_strength)
    regime = build_market_regime(features, breadth, composite, settings)
    assert signal_scores
    assert isinstance(composite, float)
    assert "bias" in regime
    keys = {row["key"] for row in signal_scores}
    assert {"trend_slope", "trend_efficiency", "vol_term_structure", "momentum_5d", "momentum_60d", "breadth_short_term", "regime_shift", "breadth_event", "volatility_release", "relative_strength_market"}.issubset(keys)


def test_tripwires_and_risk_budget_are_generated(settings, synthetic_close, synthetic_members):
    features = compute_index_features(synthetic_close, settings)
    breadth = compute_universe_breadth(synthetic_members, settings)
    _, composite = compute_signal_scores(features, breadth, settings)
    regime = build_market_regime(features, breadth, composite, settings)
    tripwires = build_tripwires(features, breadth, regime)
    risk_budget = build_risk_budget(regime, tripwires, action_board_count=4)
    assert len(tripwires) >= 4
    assert "gross_target" in risk_budget
