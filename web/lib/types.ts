export type Manifest = {
  as_of: string;
  config_version: string;
  strategy_version: string;
  generated_at: string;
  markets: Array<{
    market: string;
    slug: string;
    snapshot_path: string;
    backtest_path: string;
    bias: string;
    composite: number;
  }>;
};

export type Snapshot = {
  as_of: string;
  market: string;
  data_quality: Record<string, unknown>;
  regime: Record<string, unknown>;
  signal_scores: Array<Record<string, unknown>>;
  trade_ideas: Array<Record<string, unknown>>;
  action_board: Array<Record<string, unknown>>;
  tripwires: Array<Record<string, unknown>>;
  risk_budget: Record<string, unknown>;
  entry_plans: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
};

export type BacktestResult = {
  market: string;
  strategy_version: string;
  config_version: string;
  test_window: Record<string, string>;
  entry_rule: string;
  exit_rule: string;
  cost_assumptions: Record<string, number>;
  summary_metrics: Record<string, number>;
  setup_breakdowns: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
};
