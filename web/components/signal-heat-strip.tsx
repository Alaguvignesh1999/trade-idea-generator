type SignalDatum = {
  key: string;
  score: number;
  label?: string;
};

type SignalHeatStripProps = {
  signals: SignalDatum[];
};

function signalColor(score: number) {
  if (score >= 0.5) return "#2dd4bf";
  if (score >= 0.1) return "#67e8f9";
  if (score > -0.1) return "#7dd3fc";
  if (score > -0.5) return "#f59e0b";
  return "#fb7185";
}

export function SignalHeatStrip({ signals }: SignalHeatStripProps) {
  if (!signals.length) {
    return <div className="chart-empty">No signal heat available.</div>;
  }

  return (
    <div className="heat-strip">
      {signals.map((signal) => (
        <div key={signal.key} className="heat-cell" title={`${signal.key}: ${signal.score.toFixed(2)} ${signal.label ?? ""}`}>
          <span className="heat-swatch" style={{ background: signalColor(signal.score) }} />
          <span className="heat-label">{signal.key.replaceAll("_", " ")}</span>
        </div>
      ))}
    </div>
  );
}
