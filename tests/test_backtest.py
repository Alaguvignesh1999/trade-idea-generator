from trade_idea_generator.backtest import run_backtest


def test_backtest_is_deterministic(settings, synthetic_close):
    first = run_backtest(synthetic_close, settings, "Synthetic")
    second = run_backtest(synthetic_close, settings, "Synthetic")
    assert first.to_dict() == second.to_dict()


def test_backtest_has_setup_breakdowns(settings, synthetic_close):
    result = run_backtest(synthetic_close, settings, "Synthetic")
    assert result.setup_breakdowns
    assert "trades" in result.summary_metrics
