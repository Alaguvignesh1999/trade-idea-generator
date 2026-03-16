import Link from "next/link";

import { loadBacktest, loadManifest, loadSnapshot } from "../lib/data";

export default async function HomePage() {
  const manifest = await loadManifest();
  const marketCards = await Promise.all(
    manifest.markets.map(async (market) => {
      const snapshot = await loadSnapshot(market.snapshot_path);
      const backtest = await loadBacktest(market.backtest_path);
      return { market, snapshot, backtest };
    }),
  );

  return (
    <main className="shell">
      <section className="hero">
        <span className="pill">Latest run {manifest.as_of} · strategy {manifest.strategy_version}</span>
        <h1 style={{ fontFamily: "var(--font-headline)" }}>Trade ideas with provenance, not mystery.</h1>
        <p>
          This app is intentionally read-first. The Python engine generates the signal stack, trade ideas, action board, tripwires, and backtests. The web layer only presents the latest validated artifacts.
        </p>
      </section>

      <section className="grid markets">
        {marketCards.map(({ market, snapshot, backtest }) => (
          <article key={market.slug} className="card">
            <div className="market-title">
              <h2 style={{ fontFamily: "var(--font-headline)" }}>{market.market}</h2>
              <span className="market-bias">{market.bias}</span>
            </div>
            <p style={{ color: "var(--muted)" }}>
              {String(snapshot.regime.posture ?? "Selective")} · top setup{" "}
              <strong>{String(snapshot.trade_ideas[0]?.name ?? "N/A")}</strong>
            </p>
            <div className="metric-row">
              <div className="metric">
                <div className="metric-label">Composite</div>
                <div className="metric-value">{Number(snapshot.regime.composite ?? 0).toFixed(1)}</div>
              </div>
              <div className="metric">
                <div className="metric-label">Backtest Win Rate</div>
                <div className="metric-value">{(Number(backtest.summary_metrics.win_rate ?? 0) * 100).toFixed(1)}%</div>
              </div>
              <div className="metric">
                <div className="metric-label">Trade Ideas</div>
                <div className="metric-value">{snapshot.trade_ideas.length}</div>
              </div>
            </div>
            <Link className="detail-link" href={`/market/${market.slug}`}>
              View market detail
            </Link>
          </article>
        ))}
      </section>
    </main>
  );
}
