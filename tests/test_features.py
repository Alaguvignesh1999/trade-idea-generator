from trade_idea_generator.features import compute_index_features, compute_relative_strength_features, compute_universe_breadth, trend_stack


def test_index_features_have_expected_columns(settings, synthetic_close):
    features = compute_index_features(synthetic_close, settings)
    assert {"close", "drawdown", "rv20_ann", "rsi14", "ma20", "ma50", "ma200", "range_pos", "roc_20d", "efficiency_20d"}.issubset(features.columns)
    assert len(features) == len(synthetic_close.dropna())


def test_breadth_computes_for_member_universe(settings, synthetic_members):
    breadth = compute_universe_breadth(synthetic_members, settings)
    assert "pct_above_200" in breadth
    assert breadth["pct_above_200"].index.equals(synthetic_members.index)


def test_trend_stack_positive_for_uptrend(settings, synthetic_close):
    features = compute_index_features(synthetic_close, settings)
    assert trend_stack(features, settings) >= 3


def test_relative_strength_features_compute_against_benchmark(synthetic_close):
    benchmark = synthetic_close * 0.98
    relative = compute_relative_strength_features(synthetic_close, benchmark)
    assert {"rs_ratio", "rs_gap_20d", "rs_gap_60d", "rs_vs_ma50"}.issubset(relative.columns)
