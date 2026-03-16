from trade_idea_generator.backtest import run_backtest
from trade_idea_generator.features import compute_universe_breadth
from trade_idea_generator.ranking import setup_catalog


def test_backtest_is_deterministic(settings, synthetic_close):
    first = run_backtest(synthetic_close, settings, "Synthetic")
    second = run_backtest(synthetic_close, settings, "Synthetic")
    assert first.to_dict() == second.to_dict()


def test_backtest_has_setup_breakdowns(settings, synthetic_close):
    result = run_backtest(synthetic_close, settings, "Synthetic")
    assert result.setup_breakdowns
    assert "trades" in result.summary_metrics
    assert len(result.setup_breakdowns) == len(setup_catalog())
    assert "benchmark_buy_hold_return" in result.summary_metrics
    assert "benchmark" in result.metadata


def test_backtest_accepts_breadth_inputs(settings, synthetic_close, synthetic_members):
    breadth = compute_universe_breadth(synthetic_members, settings)
    result = run_backtest(synthetic_close, settings, "Synthetic", breadth=breadth)
    setup_keys = {row["setup_key"] for row in result.setup_breakdowns}
    assert "breadth_thrust_long" in setup_keys
    assert "breadth_weakness_short" in setup_keys
