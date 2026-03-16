type MiniSparklineProps = {
  values: Array<number | null | undefined>;
  stroke?: string;
};

export function MiniSparkline({ values, stroke = "#0f766e" }: MiniSparklineProps) {
  const clean = values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (clean.length < 2) {
    return <div className="chart-empty">No sparkline available.</div>;
  }

  const width = 220;
  const height = 72;
  const min = Math.min(...clean);
  const max = Math.max(...clean);
  const span = Math.max(max - min, 1e-9);
  const all = values.map((value) => (typeof value === "number" && Number.isFinite(value) ? value : null));

  let path = "";
  let finalX: number | null = null;
  let finalY: number | null = null;
  all.forEach((value, index) => {
    if (value === null) {
      return;
    }
    const x = (index / Math.max(all.length - 1, 1)) * width;
    const y = height - ((value - min) / span) * (height - 8) - 4;
    path += `${path ? " L" : "M"}${x.toFixed(2)} ${y.toFixed(2)}`;
    finalX = x;
    finalY = y;
  });

  const area = `${path} L ${width} ${height} L 0 ${height} Z`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="mini-sparkline" role="img" aria-label="Mini sparkline">
      <path d={area} fill="rgba(103, 232, 249, 0.12)" />
      <path d={path} fill="none" stroke={stroke} strokeOpacity={0.16} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" />
      <path d={path} fill="none" stroke={stroke} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
      {finalX !== null && finalY !== null ? <circle cx={finalX} cy={finalY} r={3.6} fill={stroke} stroke="rgba(5, 10, 24, 0.9)" strokeWidth={1.5} /> : null}
    </svg>
  );
}
