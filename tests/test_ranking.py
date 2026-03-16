import numpy as np
import pandas as pd

from trade_idea_generator.features import compute_index_features, compute_relative_strength_features, compute_universe_breadth
from trade_idea_generator.ranking import generate_trade_ideas
from trade_idea_generator.signals import build_market_regime, compute_signal_scores


def test_relative_strength_changes_directional_conviction(settings, synthetic_close, synthetic_members):
    settings.raw["trade_idea"]["idea_limit"] = 8
    features = compute_index_features(synthetic_close, settings)
    breadth = compute_universe_breadth(synthetic_members, settings)
    weak_benchmark = pd.Series(np.linspace(100, 130, len(synthetic_close)), index=synthetic_close.index)
    strong_benchmark = pd.Series(np.linspace(100, 165, len(synthetic_close)), index=synthetic_close.index)

    positive_rs = compute_relative_strength_features(synthetic_close, weak_benchmark)
    negative_rs = compute_relative_strength_features(synthetic_close, strong_benchmark)

    _, positive_composite = compute_signal_scores(features, breadth, settings, relative_strength=positive_rs)
    _, negative_composite = compute_signal_scores(features, breadth, settings, relative_strength=negative_rs)
    positive_regime = build_market_regime(features, breadth, positive_composite, settings)
    negative_regime = build_market_regime(features, breadth, negative_composite, settings)

    positive_ideas = {idea.setup_key: idea for idea in generate_trade_ideas(features, breadth, positive_regime, settings, relative_strength=positive_rs)}
    negative_ideas = {idea.setup_key: idea for idea in generate_trade_ideas(features, breadth, negative_regime, settings, relative_strength=negative_rs)}

    assert positive_ideas["trend_pullback_long"].conviction > negative_ideas["trend_pullback_long"].conviction
    assert negative_ideas["trend_failure_short"].conviction > positive_ideas["trend_failure_short"].conviction
