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

export type ChartPoint = {
  date: string;
  [key: string]: string | number | null;
};

export type SetupDiagnostic = {
  setup_key: string;
  direction: string;
  trades: number;
  win_rate: number;
  average_return: number;
  cumulative_return: number;
  max_drawdown: number;
  quality_score: number;
  verdict: "FAVORABLE" | "MIXED" | "WEAK";
};

export type TradeIdea = {
  setup_key: string;
  name: string;
  direction: string;
  conviction: number;
  suitability: number;
  thesis: string;
  status: string;
  backtest_trades?: number;
  backtest_win_rate?: number;
  backtest_average_return?: number;
  quality_score?: number;
  quality_verdict?: string;
  [key: string]: unknown;
};

export type Snapshot = {
  as_of: string;
  market: string;
  data_quality: Record<string, unknown>;
  regime: Record<string, unknown>;
  signal_scores: Array<Record<string, unknown>>;
  trade_ideas: Array<TradeIdea>;
  action_board: Array<Record<string, unknown>>;
  tripwires: Array<Record<string, unknown>>;
  risk_budget: Record<string, unknown>;
  entry_plans: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
  research: {
    chartbook: {
      price_history: ChartPoint[];
      oscillator_history: ChartPoint[];
      breadth_history: ChartPoint[];
      relative_strength_history: ChartPoint[];
      signal_family_history: ChartPoint[];
    };
    setup_diagnostics: SetupDiagnostic[];
    summary: {
      favorable_setups: number;
      watchlist_setups: number;
      weak_setups: number;
    };
  };
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
