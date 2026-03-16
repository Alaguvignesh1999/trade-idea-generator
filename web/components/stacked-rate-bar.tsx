type RateSlice = {
  label: string;
  value: number;
  color: string;
};

type StackedRateBarProps = {
  slices: RateSlice[];
};

export function StackedRateBar({ slices }: StackedRateBarProps) {
  const total = Math.max(slices.reduce((sum, slice) => sum + Math.max(slice.value, 0), 0), 1e-9);

  return (
    <div className="stacked-block">
      <div className="stacked-bar">
        {slices.map((slice) => (
          <div key={slice.label} style={{ width: `${(Math.max(slice.value, 0) / total) * 100}%`, background: slice.color }} />
        ))}
      </div>
      <div className="stacked-legend">
        {slices.map((slice) => (
          <div key={slice.label} className="stacked-legend-item">
            <span className="chart-legend-swatch" style={{ background: slice.color }} />
            <span>
              {slice.label} {(slice.value * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
