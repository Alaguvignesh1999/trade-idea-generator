type ChartRecord = {
  date: string;
  [key: string]: string | number | null;
};

type LineDefinition = {
  key: string;
  label: string;
  color: string;
  dashed?: boolean;
};

type ResearchLineChartProps = {
  data: ChartRecord[];
  lines: LineDefinition[];
  valueSuffix?: string;
  minValue?: number;
  maxValue?: number;
};

const WIDTH = 760;
const HEIGHT = 240;
const MARGIN = { top: 16, right: 12, bottom: 26, left: 12 };

function buildPath(points: Array<{ x: number; y: number; value: number | null }>) {
  let path = "";
  let active = false;
  for (const point of points) {
    if (point.value === null) {
      active = false;
      continue;
    }
    path += `${active ? "L" : "M"}${point.x.toFixed(2)},${point.y.toFixed(2)} `;
    active = true;
  }
  return path.trim();
}

function toNumber(value: string | number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatAxisValue(value: number, suffix: string) {
  if (Math.abs(value) >= 1000) {
    return `${value.toFixed(0)}${suffix}`;
  }
  if (Math.abs(value) >= 100) {
    return `${value.toFixed(0)}${suffix}`;
  }
  if (Math.abs(value) >= 10) {
    return `${value.toFixed(1)}${suffix}`;
  }
  return `${value.toFixed(2)}${suffix}`;
}

export function ResearchLineChart({ data, lines, valueSuffix = "", minValue, maxValue }: ResearchLineChartProps) {
  if (!data.length) {
    return <div className="chart-empty">No history available yet.</div>;
  }

  const numericValues = data.flatMap((row) => lines.map((line) => toNumber(row[line.key]))).filter((value): value is number => value !== null);
  const rawMin = minValue ?? Math.min(...numericValues);
  const rawMax = maxValue ?? Math.max(...numericValues);
  const padding = rawMin === rawMax ? Math.max(Math.abs(rawMin) * 0.1, 1) : (rawMax - rawMin) * 0.12;
  const yMin = rawMin - padding;
  const yMax = rawMax + padding;
  const innerWidth = WIDTH - MARGIN.left - MARGIN.right;
  const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  const x = (index: number) => MARGIN.left + (index / Math.max(data.length - 1, 1)) * innerWidth;
  const y = (value: number) => MARGIN.top + (1 - (value - yMin) / Math.max(yMax - yMin, 1e-9)) * innerHeight;

  const gridValues = Array.from({ length: 4 }, (_, index) => yMin + ((yMax - yMin) * index) / 3);

  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        {lines.map((line) => {
          const latest = [...data].reverse().find((row) => toNumber(row[line.key]) !== null);
          const latestValue = latest ? toNumber(latest[line.key]) : null;
          return (
            <div key={line.key} className="chart-legend-item">
              <span className="chart-legend-swatch" style={{ background: line.color }} />
              <span>
                {line.label}
                {latestValue !== null ? ` ${formatAxisValue(latestValue, valueSuffix)}` : ""}
              </span>
            </div>
          );
        })}
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="chart-svg" role="img" aria-label="Research chart">
        {gridValues.map((value) => {
          const yValue = y(value);
          return (
            <g key={value}>
              <line className="chart-grid-line" x1={MARGIN.left} y1={yValue} x2={WIDTH - MARGIN.right} y2={yValue} />
              <text className="chart-axis" x={WIDTH - MARGIN.right} y={yValue - 4} textAnchor="end">
                {formatAxisValue(value, valueSuffix)}
              </text>
            </g>
          );
        })}
        {lines.map((line) => {
          const points = data.map((row, index) => {
            const value = toNumber(row[line.key]);
            return { x: x(index), y: value === null ? 0 : y(value), value };
          });
          const activePoints = points.filter((point): point is { x: number; y: number; value: number } => point.value !== null);
          const latestPoint = activePoints[activePoints.length - 1];
          const path = buildPath(points);
          return (
            <g key={line.key}>
              <path d={path} fill="none" stroke={line.color} strokeOpacity={0.16} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" />
              <path
                d={path}
                fill="none"
                stroke={line.color}
                strokeWidth={2.6}
                strokeDasharray={line.dashed ? "5 5" : undefined}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {latestPoint ? <circle cx={latestPoint.x} cy={latestPoint.y} r={4.2} fill={line.color} stroke="rgba(5, 10, 24, 0.9)" strokeWidth={1.5} /> : null}
            </g>
          );
        })}
        <text className="chart-axis" x={MARGIN.left} y={HEIGHT - 6}>
          {data[0]?.date}
        </text>
        <text className="chart-axis" x={WIDTH - MARGIN.right} y={HEIGHT - 6} textAnchor="end">
          {data[data.length - 1]?.date}
        </text>
      </svg>
    </div>
  );
}
