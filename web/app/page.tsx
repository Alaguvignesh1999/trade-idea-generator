import Link from "next/link";

import { MiniSparkline } from "../components/mini-sparkline";
import { SignalHeatStrip } from "../components/signal-heat-strip";
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

  const averageComposite =
    marketCards.reduce((sum, entry) => sum + Number(entry.snapshot.regime.composite ?? 0), 0) / Math.max(marketCards.length, 1);
  const averageWinRate =
    marketCards.reduce((sum, entry) => sum + Number(entry.backtest.summary_metrics.win_rate ?? 0), 0) / Math.max(marketCards.length, 1);
  const favorableSetups = marketCards.reduce((sum, entry) => sum + Number(entry.snapshot.research?.summary?.favorable_setups ?? 0), 0);
  const totalIdeas = marketCards.reduce((sum, entry) => sum + entry.snapshot.trade_ideas.length, 0);

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <span className="hero-kicker">Orbital Market Desk</span>
          <span className="pill">Latest run {manifest.as_of} | strategy {manifest.strategy_version}</span>
          <h1 style={{ fontFamily: "var(--font-headline)" }}>Trade ideas from a dark-signal command deck.</h1>
          <p>
            This surface is built like a modern trading terminal: regime, price structure, breadth, diagnostics, and live idea quality all in one place. The Python
            engine does the thinking. The web layer keeps the latest validated artifacts readable at a glance.
          </p>
        </div>
        <div className="hero-console">
          <div className="hero-stat">
            <span className="hero-stat-label">Markets online</span>
            <strong className="hero-stat-value">{marketCards.length}</strong>
            <span className="hero-stat-note">Validated snapshot feeds</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Avg composite</span>
            <strong className="hero-stat-value">{averageComposite.toFixed(1)}</strong>
            <span className="hero-stat-note">Cross-market regime read</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Avg win rate</span>
            <strong className="hero-stat-value">{(averageWinRate * 100).toFixed(1)}%</strong>
            <span className="hero-stat-note">Reality check, not marketing</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Ideas surfaced</span>
            <strong className="hero-stat-value">{totalIdeas}</strong>
            <span className="hero-stat-note">{favorableSetups} favorable setups on deck</span>
          </div>
        </div>
      </section>

      <section className="grid markets">
        {marketCards.map(({ market, snapshot, backtest }) => (
          <article key={market.slug} className="card">
            <div className="market-title">
              <h2 style={{ fontFamily: "var(--font-headline)" }}>{market.market}</h2>
              <span className="market-bias">{market.bias}</span>
            </div>
            <p className="market-copy">
              {String(snapshot.regime.posture ?? "Selective")} | top setup <strong>{String(snapshot.trade_ideas[0]?.name ?? "N/A")}</strong>
            </p>
            <MiniSparkline values={(snapshot.research?.chartbook?.price_history ?? []).slice(-60).map((point) => Number(point.close ?? NaN))} stroke="#67e8f9" />
            <SignalHeatStrip
              signals={(snapshot.signal_scores ?? []).slice(0, 8).map((signal) => ({
                key: String(signal.key),
                score: Number(signal.score ?? 0),
                label: String(signal.label ?? ""),
              }))}
            />
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
            <div className="card-chip-row">
              <span className="idea-status idea-active">Favorable {Number(snapshot.research?.summary?.favorable_setups ?? 0).toFixed(0)}</span>
              <span className="idea-status idea-watchlist">Mixed {Number(snapshot.research?.summary?.watchlist_setups ?? 0).toFixed(0)}</span>
              <span className="idea-status idea-avoid">Weak {Number(snapshot.research?.summary?.weak_setups ?? 0).toFixed(0)}</span>
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
