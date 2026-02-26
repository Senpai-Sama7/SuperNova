/**
 * Conformal prediction interval band chart
 * @param {Array} stream - Stream of prediction data
 * @param {Array} ci - Confidence interval [lower, upper]
 * @param {number} width - Chart width
 * @param {number} height - Chart height
 */
export const ConformalBandChart = ({ stream, ci, width = 450, height = 100 }) => {
  if (!stream || stream.length < 3) return null;
  const data = stream.slice(-40);
  const allVals = data.flatMap((d) => [d.actual, d.predicted]);
  const min = Math.min(...allVals, ci[0]) * 0.95;
  const max = Math.max(...allVals, ci[1]) * 1.05;
  const range = max - min || 1;
  const xScale = (i) => (i / (data.length - 1)) * 100;
  const yScale = (v) => 100 - ((v - min) / range) * 100;

  const upperY = yScale(ci[1]);
  const lowerY = yScale(ci[0]);

  const actualPoints = data
    .map((d, i) => `${xScale(i)},${yScale(d.actual)}`)
    .join(" ");
  const predictedPoints = data
    .map((d, i) => `${xScale(i)},${yScale(d.predicted)}`)
    .join(" ");

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      style={{ borderRadius: 6, overflow: "visible" }}
    >
      <defs>
        <linearGradient id="ci-band" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00ffd5" stopOpacity="0.15" />
          <stop offset="50%" stopColor="#00ffd5" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#00ffd5" stopOpacity="0.15" />
        </linearGradient>
      </defs>
      {/* CI band */}
      <rect
        x="0"
        y={upperY}
        width="100"
        height={lowerY - upperY}
        fill="url(#ci-band)"
      />
      <line
        x1="0"
        y1={upperY}
        x2="100"
        y2={upperY}
        stroke="#34d39944"
        strokeWidth="0.5"
        strokeDasharray="2 2"
      />
      <line
        x1="0"
        y1={lowerY}
        x2="100"
        y2={lowerY}
        stroke="#f8717144"
        strokeWidth="0.5"
        strokeDasharray="2 2"
      />
      {/* Predicted line */}
      <polyline
        points={predictedPoints}
        fill="none"
        stroke="#a78bfa"
        strokeWidth="1.5"
        opacity="0.6"
      />
      {/* Actual line */}
      <polyline
        points={actualPoints}
        fill="none"
        stroke="#00ffd5"
        strokeWidth="2"
        style={{ filter: "drop-shadow(0 0 3px #00ffd566)" }}
      />
    </svg>
  );
};
