import Link from "next/link";
import { notFound } from "next/navigation";

import { loadBacktest, loadManifest, loadSnapshot } from "../../../lib/data";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export default async function MarketPage({ params }: PageProps) {
  const { slug } = await params;
  const manifest = await loadManifest();
  const market = manifest.markets.find((item) => item.slug === slug);
  if (!market) {
    notFound();
  }

  const snapshot = await loadSnapshot(market.snapshot_path);
  const backtest = await loadBacktest(market.backtest_path);

  return (
    <main className="shell">
      <section className="hero">
        <Link className="pill" href="/">
          Back to dashboard
        </Link>
        <h1 style={{ fontFamily: "var(--font-headline)" }}>{snapshot.market}</h1>
        <p>
          Run date {snapshot.as_of}. Config {String(snapshot.metadata.config_version)}. Strategy {String(snapshot.metadata.strategy_version)}.
        </p>
      </section>

      <section className="section-grid">
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Top Trade Ideas</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Setup</th>
                <th>Direction</th>
                <th>Conviction</th>
                <th>Thesis</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.trade_ideas.map((idea) => (
                <tr key={String(idea.setup_key) + String(idea.name)}>
                  <td>{String(idea.name)}</td>
                  <td>{String(idea.direction)}</td>
                  <td>{Number(idea.conviction).toFixed(1)}</td>
                  <td>{String(idea.thesis)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Risk Budget</h2>
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
          <p style={{ color: "var(--muted)", marginTop: 16 }}>{String(snapshot.risk_budget.posture ?? "")}</p>
        </article>
      </section>

      <section className="split" style={{ marginTop: 18 }}>
        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Action Board</h2>
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
        </article>

        <article className="card">
          <h2 style={{ fontFamily: "var(--font-headline)" }}>Tripwires</h2>
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
        </article>
      </section>

      <section style={{ marginTop: 18 }}>
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
          <p style={{ marginTop: 16, color: "var(--muted)" }}>
            Entry rule: {backtest.entry_rule}
            <br />
            Exit rule: {backtest.exit_rule}
          </p>
        </article>
      </section>
    </main>
  );
}
