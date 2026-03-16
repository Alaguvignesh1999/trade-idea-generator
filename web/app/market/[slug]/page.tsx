import Link from "next/link";
import { notFound } from "next/navigation";

import { ComparisonBars } from "../../../components/comparison-bars";
import { ResearchLineChart } from "../../../components/research-line-chart";
import { SignalHeatStrip } from "../../../components/signal-heat-strip";
import { SetupDiagnostics } from "../../../components/setup-diagnostics";
import { StackedRateBar } from "../../../components/stacked-rate-bar";
import { loadBacktest, loadManifest, loadSnapshot } from "../../../lib/data";

type PageProps = {
  params: Promise<{ slug: string }>;
};

function formatPercent(value: unknown, digits = 1) {
  const numeric = Number(value ?? 0);
  return `${(numeric * 100).toFixed(digits)}%`;
}

function formatSignedPercent(value: unknown, digits = 1) {
  const numeric = Number(value ?? 0);
  return `${numeric >= 0 ? "+" : ""}${(numeric * 100).toFixed(digits)}%`;
}

export default async function MarketPage({ params }: PageProps) {
  const { slug } = await params;
  const manifest = await loadManifest();
  const market = manifest.markets.find((item) => item.slug === slug);
  if (!market) {
    notFound();
  }

  const snapshot = await loadSnapshot(market.snapshot_path);
  const backtest = await loadBacktest(market.backtest_path);
  const priceHistory = snapshot.research?.chartbook?.price_history ?? [];
  const oscillatorHistory = snapshot.research?.chartbook?.oscillator_history ?? [];
  const breadthHistory = snapshot.research?.chartbook?.breadth_history ?? [];
  const relativeStrengthHistory = snapshot.research?.chartbook?.relative_strength_history ?? [];
  const signalFamilyHistory = snapshot.research?.chartbook?.signal_family_history ?? [];
  const setupDiagnostics = snapshot.research?.setup_diagnostics ?? [];
  const benchmark = (backtest.metadata?.benchmark ?? {}) as Record<string, number>;
  const directionBreakdowns = (backtest.metadata?.direction_breakdowns ?? {}) as Record<string, Record<string, number>>;
  const triggeredTripwires = snapshot.tripwires.filter((wire) => String(wire.status).toUpperCase() === "TRIGGERED").length;
  const activeIdeas = snapshot.trade_ideas.filter((idea) => String(idea.status).toUpperCase() === "ACTIVE").length;

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <span className="hero-kicker">Market Command Deck</span>
          <Link className="pill" href="/">
            Back to dashboard
          </Link>
          <h1 style={{ fontFamily: "var(--font-headline)" }}>{snapshot.market}</h1>
          <p>
            Run date {snapshot.as_of}. Config {String(snapshot.metadata.config_version)}. Strategy {String(snapshot.metadata.strategy_version)}. This page is built
            for tape reading first: price structure, breadth, relative strength, and setup quality in one dark research workflow.
          </p>
        </div>
        <div className="hero-console">
          <div className="hero-stat">
            <span className="hero-stat-label">Regime posture</span>
            <strong className="hero-stat-value">{String(snapshot.regime.posture ?? "Selective")}</strong>
            <span className="hero-stat-note">Composite {Number(snapshot.regime.composite ?? 0).toFixed(1)}</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Benchmark</span>
            <strong className="hero-stat-value">{String(snapshot.metadata.benchmark ?? "Peer basket")}</strong>
            <span className="hero-stat-note">{formatSignedPercent(Number(benchmark.buy_hold_return ?? 0), 1)} buy and hold</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Active ideas</span>
            <strong className="hero-stat-value">{activeIdeas}</strong>
            <span className="hero-stat-note">{snapshot.trade_ideas.length} total setups on screen</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Tripwires</span>
            <strong className="hero-stat-value">{triggeredTripwires}</strong>
            <span className="hero-stat-note">Triggered risk responses</span>
          </div>
        </div>
      </section>

      <section className="section-grid">
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Market Regime</h2>
          <div className="metric-row">
            <div className="metric">
              <div className="metric-label">Composite</div>
              <div className="metric-value">{Number(snapshot.regime.composite ?? 0).toFixed(1)}</div>
            </div>
            <div className="metric">
              <div className="metric-label">Bull Probability</div>
              <div className="metric-value">{Number(snapshot.regime.bull_probability ?? 0).toFixed(1)}%</div>
            </div>
            <div className="metric">
              <div className="metric-label">Bear Probability</div>
              <div className="metric-value">{Number(snapshot.regime.bear_probability ?? 0).toFixed(1)}%</div>
            </div>
          </div>
          <SignalHeatStrip
            signals={snapshot.signal_scores.map((signal) => ({
              key: String(signal.key),
              score: Number(signal.score ?? 0),
              label: String(signal.label ?? ""),
            }))}
          />
          <div className="signal-summary-grid">
            {snapshot.signal_scores.map((signal) => (
              <div key={String(signal.key)} className="signal-score-card">
                <div className="signal-score-topline">
                  <span>{String(signal.key).replaceAll("_", " ")}</span>
                  <strong>{String(signal.raw)}</strong>
                </div>
                <div className="signal-score-label">{String(signal.label)}</div>
                <p>{String(signal.detail)}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Research Pulse</h2>
          <div className="metric-row">
            <div className="metric">
              <div className="metric-label">Favorable</div>
              <div className="metric-value">{Number(snapshot.research?.summary?.favorable_setups ?? 0).toFixed(0)}</div>
            </div>
            <div className="metric">
              <div className="metric-label">Mixed</div>
              <div className="metric-value">{Number(snapshot.research?.summary?.watchlist_setups ?? 0).toFixed(0)}</div>
            </div>
            <div className="metric">
              <div className="metric-label">Weak</div>
              <div className="metric-value">{Number(snapshot.research?.summary?.weak_setups ?? 0).toFixed(0)}</div>
            </div>
          </div>
          <div className="metric-row">
            <div className="metric">
              <div className="metric-label">Gross</div>
              <div className="metric-value">{Number(snapshot.risk_budget.gross_target ?? 0).toFixed(1)}%</div>
            </div>
            <div className="metric">
              <div className="metric-label">Net</div>
              <div className="metric-value">{Number(snapshot.risk_budget.net_target ?? 0).toFixed(1)}%</div>
            </div>
            <div className="metric">
              <div className="metric-label">Cash</div>
              <div className="metric-value">{Number(snapshot.risk_budget.cash_target ?? 0).toFixed(1)}%</div>
            </div>
          </div>
          <p style={{ color: "var(--text-soft)", marginTop: 16 }}>{String(snapshot.risk_budget.posture ?? "")}</p>
        </article>
      </section>

      <section className="chart-grid" style={{ marginTop: 18 }}>
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Price And Moving Averages</h2>
          <p className="chart-copy">Price movement with the key moving averages that drive most of the regime logic.</p>
          <ResearchLineChart
            data={priceHistory}
            lines={[
              { key: "close", label: "Close", color: "#67e8f9" },
              { key: "ma20", label: "MA20", color: "#f59e0b" },
              { key: "ma50", label: "MA50", color: "#38bdf8" },
              { key: "ma200", label: "MA200", color: "#a78bfa", dashed: true },
            ]}
          />
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Momentum And Volatility</h2>
          <p className="chart-copy">RSI, volatility percentile, and range position on the same 0-100 scale for quick read-through.</p>
          <ResearchLineChart
            data={oscillatorHistory}
            lines={[
              { key: "rsi14", label: "RSI 14", color: "#67e8f9" },
              { key: "volatility_percentile", label: "Vol Percentile", color: "#fb7185" },
              { key: "range_position", label: "Range Position", color: "#facc15" },
            ]}
            minValue={0}
            maxValue={100}
            valueSuffix="%"
          />
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Breadth Participation</h2>
          <p className="chart-copy">Internal participation matters more than the headline index level when you are deciding whether to trust a move.</p>
          <ResearchLineChart
            data={breadthHistory}
            lines={[
              { key: "pct_above_50", label: "% Above 50DMA", color: "#2dd4bf" },
              { key: "pct_above_200", label: "% Above 200DMA", color: "#38bdf8" },
              { key: "breadth_momentum", label: "Breadth Momentum", color: "#fb7185", dashed: true },
            ]}
            valueSuffix="%"
          />
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Signal Family Monitor</h2>
          <p className="chart-copy">Regime shift pressure, breadth thrust or washout behavior, and volatility release states over time.</p>
          <ResearchLineChart
            data={signalFamilyHistory}
            lines={[
              { key: "regime_shift", label: "Regime Shift", color: "#a78bfa" },
              { key: "breadth_thrust", label: "Breadth Thrust", color: "#2dd4bf" },
              { key: "washout_reversal", label: "Washout Reversal", color: "#f59e0b" },
              { key: "volatility_release", label: "Vol Release", color: "#fb7185" },
            ]}
          />
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Relative Strength Vs Benchmark</h2>
          <p className="chart-copy">How this market is performing relative to {String(snapshot.metadata.benchmark ?? "its benchmark")} across medium-term lookbacks.</p>
          <ResearchLineChart
            data={relativeStrengthHistory}
            lines={[
              { key: "rs_gap_20d", label: "RS Gap 20d", color: "#67e8f9" },
              { key: "rs_gap_60d", label: "RS Gap 60d", color: "#38bdf8" },
              { key: "rs_vs_ma50", label: "RS vs MA50", color: "#a78bfa", dashed: true },
            ]}
            valueSuffix="%"
          />
        </article>
      </section>

      <section style={{ marginTop: 18 }}>
        <article className="card">
          <div className="section-header">
            <div>
              <h2 style={{ fontFamily: "var(--font-headline)" }}>Trade Ideas With Quality Context</h2>
              <p className="chart-copy">Weak setups are explicitly downgraded so you can separate ideas worth studying from noise worth ignoring.</p>
            </div>
          </div>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Setup</th>
                  <th>Status</th>
                  <th>Dir</th>
                  <th>Conviction</th>
                  <th>Quality</th>
                  <th>Backtest Win</th>
                  <th>Avg Trade</th>
                  <th>Thesis</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.trade_ideas.map((idea) => (
                  <tr key={String(idea.setup_key) + String(idea.name)}>
                    <td>{String(idea.name)}</td>
                    <td>
                      <span className={`idea-status idea-${String(idea.status).toLowerCase()}`}>{String(idea.status)}</span>
                    </td>
                    <td>{String(idea.direction)}</td>
                    <td>{Number(idea.conviction).toFixed(1)}</td>
                    <td>{idea.quality_score !== undefined ? `${Number(idea.quality_score).toFixed(1)} | ${String(idea.quality_verdict ?? "")}` : "N/A"}</td>
                    <td>{idea.backtest_win_rate !== undefined ? formatPercent(idea.backtest_win_rate) : "N/A"}</td>
                    <td>{idea.backtest_average_return !== undefined ? formatSignedPercent(idea.backtest_average_return, 2) : "N/A"}</td>
                    <td>{String(idea.thesis)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <section className="split" style={{ marginTop: 18 }}>
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Strategy Vs Benchmark</h2>
          <p className="chart-copy">A quick performance reality check against buy-and-hold so the setup engine does not hide behind isolated wins.</p>
          <ComparisonBars
            items={[
              { label: "Strategy cumulative", value: Number(backtest.summary_metrics.cumulative_return ?? 0), format: "percent" },
              { label: "Buy and hold", value: Number(benchmark.buy_hold_return ?? 0), format: "percent" },
              { label: "Excess vs buy and hold", value: Number(backtest.summary_metrics.excess_return_vs_buy_hold ?? 0), format: "percent" },
              { label: "Strategy max drawdown", value: Number(backtest.summary_metrics.max_drawdown ?? 0), format: "percent" },
            ]}
          />
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Execution Outcome Mix</h2>
          <p className="chart-copy">This makes it easier to see whether the engine is earning targets, getting stopped out, or mostly timing out.</p>
          <StackedRateBar
            slices={[
              { label: "Target", value: Number(backtest.summary_metrics.target_rate ?? 0), color: "#2dd4bf" },
              { label: "Stop", value: Number(backtest.summary_metrics.stop_rate ?? 0), color: "#fb7185" },
              { label: "Time Exit", value: Number(backtest.summary_metrics.time_exit_rate ?? 0), color: "#f59e0b" },
            ]}
          />
        </article>
      </section>

      <section className="split" style={{ marginTop: 18 }}>
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Action Board</h2>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Sector</th>
                  <th>Dir</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.action_board.map((row) => (
                  <tr key={String(row.symbol)}>
                    <td>{String(row.symbol)}</td>
                    <td>{String(row.sector)}</td>
                    <td>{String(row.direction)}</td>
                    <td>{Number(row.diversified_score).toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Tripwires</h2>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Tripwire</th>
                  <th>Status</th>
                  <th>Response</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.tripwires.map((wire) => (
                  <tr key={String(wire.name)}>
                    <td>{String(wire.name)}</td>
                    <td className={`status-${String(wire.status).toLowerCase()}`}>{String(wire.status)}</td>
                    <td>{String(wire.response)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <section className="split" style={{ marginTop: 18 }}>
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Backtest Summary</h2>
          <div className="metric-row">
            <div className="metric">
              <div className="metric-label">Trades</div>
              <div className="metric-value">{Number(backtest.summary_metrics.trades ?? 0).toFixed(0)}</div>
            </div>
            <div className="metric">
              <div className="metric-label">Win Rate</div>
              <div className="metric-value">{(Number(backtest.summary_metrics.win_rate ?? 0) * 100).toFixed(1)}%</div>
            </div>
            <div className="metric">
              <div className="metric-label">Cumulative Return</div>
              <div className="metric-value">{(Number(backtest.summary_metrics.cumulative_return ?? 0) * 100).toFixed(1)}%</div>
            </div>
          </div>
          <div className="metric-row">
            <div className="metric">
              <div className="metric-label">Avg Trade</div>
              <div className="metric-value">{formatSignedPercent(backtest.summary_metrics.average_return ?? 0, 2)}</div>
            </div>
            <div className="metric">
              <div className="metric-label">Median Trade</div>
              <div className="metric-value">{formatSignedPercent(backtest.summary_metrics.median_return ?? 0, 2)}</div>
            </div>
            <div className="metric">
              <div className="metric-label">Max Drawdown</div>
              <div className="metric-value">{formatSignedPercent(backtest.summary_metrics.max_drawdown ?? 0, 1)}</div>
            </div>
          </div>
          <p style={{ marginTop: 16, color: "var(--text-soft)" }}>
            Entry rule: {backtest.entry_rule}
            <br />
            Exit rule: {backtest.exit_rule}
          </p>
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Setup Diagnostics</h2>
          <p className="chart-copy">This is the fastest way to see which setups deserve attention and which ones need redesign.</p>
          <SetupDiagnostics diagnostics={setupDiagnostics} />
        </article>
      </section>

      <section className="split" style={{ marginTop: 18 }}>
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Long Vs Short Profile</h2>
          <p className="chart-copy">Direction-level breakdowns show whether one side of the book is carrying or dragging the strategy.</p>
          <ComparisonBars
            items={[
              { label: "Long cumulative", value: Number(directionBreakdowns.LONG?.cumulative_return ?? 0), format: "percent" },
              { label: "Short cumulative", value: Number(directionBreakdowns.SHORT?.cumulative_return ?? 0), format: "percent" },
              { label: "Long expectancy", value: Number(directionBreakdowns.LONG?.expectancy ?? 0), format: "percent" },
              { label: "Short expectancy", value: Number(directionBreakdowns.SHORT?.expectancy ?? 0), format: "percent" },
            ]}
          />
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Direction Outcome Mix</h2>
          <div className="direction-grid">
            <div>
              <div className="direction-title">Long Book</div>
              <StackedRateBar
                slices={[
                  { label: "Target", value: Number(directionBreakdowns.LONG?.target_rate ?? 0), color: "#2dd4bf" },
                  { label: "Stop", value: Number(directionBreakdowns.LONG?.stop_rate ?? 0), color: "#fb7185" },
                  { label: "Time Exit", value: Number(directionBreakdowns.LONG?.time_exit_rate ?? 0), color: "#f59e0b" },
                ]}
              />
            </div>
            <div>
              <div className="direction-title">Short Book</div>
              <StackedRateBar
                slices={[
                  { label: "Target", value: Number(directionBreakdowns.SHORT?.target_rate ?? 0), color: "#2dd4bf" },
                  { label: "Stop", value: Number(directionBreakdowns.SHORT?.stop_rate ?? 0), color: "#fb7185" },
                  { label: "Time Exit", value: Number(directionBreakdowns.SHORT?.time_exit_rate ?? 0), color: "#f59e0b" },
                ]}
              />
            </div>
          </div>
        </article>
      </section>
    </main>
  );
}
