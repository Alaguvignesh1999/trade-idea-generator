type ComparisonDatum = {
  label: string;
  value: number;
  format?: "percent" | "number";
};

type ComparisonBarsProps = {
  items: ComparisonDatum[];
  symmetric?: boolean;
};

function formatValue(value: number, format: "percent" | "number" = "number") {
  if (format === "percent") {
    return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
  }
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

export function ComparisonBars({ items, symmetric = true }: ComparisonBarsProps) {
  if (!items.length) {
    return <div className="chart-empty">No comparisons available.</div>;
  }

  const extent = Math.max(...items.map((item) => Math.abs(item.value)), 0.0001);

  return (
    <div className="comparison-list">
      {items.map((item) => {
        const width = `${(Math.abs(item.value) / extent) * 50}%`;
        const positive = item.value >= 0;
        return (
          <div key={item.label} className="comparison-row">
            <div className="comparison-label">{item.label}</div>
            <div className={`comparison-track ${symmetric ? "comparison-track-symmetric" : ""}`}>
              {symmetric ? <div className="comparison-midline" /> : null}
              <div
                className={`comparison-bar ${positive ? "comparison-positive" : "comparison-negative"}`}
                style={
                  symmetric
                    ? positive
                      ? { left: "50%", width }
                      : { right: "50%", width }
                    : { width: `${(Math.abs(item.value) / extent) * 100}%` }
                }
              />
            </div>
            <div className="comparison-value">{formatValue(item.value, item.format)}</div>
          </div>
        );
      })}
    </div>
  );
}
