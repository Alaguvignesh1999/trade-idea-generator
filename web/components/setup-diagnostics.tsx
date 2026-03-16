import type { SetupDiagnostic } from "../lib/types";

type SetupDiagnosticsProps = {
  diagnostics: SetupDiagnostic[];
};

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function SetupDiagnostics({ diagnostics }: SetupDiagnosticsProps) {
  if (!diagnostics.length) {
    return <div className="chart-empty">No setup diagnostics available yet.</div>;
  }

  return (
    <div className="diagnostic-list">
      {diagnostics.map((diagnostic) => (
        <article key={diagnostic.setup_key} className="diagnostic-card">
          <div className="diagnostic-topline">
            <div>
              <div className="diagnostic-title">{diagnostic.setup_key.replaceAll("_", " ")}</div>
              <div className="diagnostic-subtitle">
                {diagnostic.direction} | {diagnostic.trades} trades
              </div>
            </div>
            <span className={`diagnostic-verdict verdict-${diagnostic.verdict.toLowerCase()}`}>{diagnostic.verdict}</span>
          </div>
          <div className="diagnostic-bar">
            <div className={`diagnostic-bar-fill verdict-${diagnostic.verdict.toLowerCase()}`} style={{ width: `${diagnostic.quality_score}%` }} />
          </div>
          <div className="diagnostic-metrics">
            <span>Quality {diagnostic.quality_score.toFixed(1)}</span>
            <span>Win {formatPercent(diagnostic.win_rate)}</span>
            <span>Avg {(diagnostic.average_return * 100).toFixed(2)}%</span>
            <span>Cum {(diagnostic.cumulative_return * 100).toFixed(1)}%</span>
            <span>DD {(diagnostic.max_drawdown * 100).toFixed(1)}%</span>
          </div>
        </article>
      ))}
    </div>
  );
}
