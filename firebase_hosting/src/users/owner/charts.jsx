import React, { useState } from 'react';

// Small dependency-free SVG charts for the Owner analytics

const WIDTH = 800;
const PAD = { top: 16, right: 20, bottom: 30, left: 56 };

function niceMax(value) {
  if (value <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log10(value)));
  const f = value / exp;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * exp;
}

// A line chart with optional filled area, shared y axis, hover tooltip and an optional target line.
// series: [{ key, label, color, area? }]
export function LineChart({ data, xKey, series, height = 260, viewWidth = WIDTH, yMin = 0, yMaxFixed, tickCount = 4, formatY, formatX, formatTip, target, targetLabel, ariaLabel }) {
  const [hover, setHover] = useState(null);
  const W = viewWidth;
  const plotW = W - PAD.left - PAD.right;
  const plotH = height - PAD.top - PAD.bottom;
  const n = data.length;

  const maxValue = Math.max(...data.flatMap((d) => series.map((s) => d[s.key])), target || 0);
  const yMax = yMaxFixed !== undefined ? yMaxFixed : niceMax(maxValue * 1.05);
  const x = (i) => PAD.left + (n === 1 ? plotW / 2 : (i / (n - 1)) * plotW);
  const y = (v) => PAD.top + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

  const yTicks = Array.from({ length: tickCount + 1 }, (_, k) => yMin + (k / tickCount) * (yMax - yMin));
  const labelCount = Math.min(W < 600 ? 4 : 6, n);
  const xLabelIdx = Array.from({ length: labelCount }, (_, k) => (labelCount === 1 ? 0 : Math.round((k * (n - 1)) / (labelCount - 1))));

  const onMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const px = ((event.clientX - rect.left) / rect.width) * W;
    const index = Math.round(((px - PAD.left) / plotW) * (n - 1));
    setHover(Math.max(0, Math.min(n - 1, index)));
  };

  const hovered = hover === null ? null : data[hover] || null; // the data can change under the pointer
  const leftPct = hover === null ? 0 : (x(hover) / W) * 100;

  return (
    <div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 mb-2">
        {series.map((s) => (
          <span key={s.key} className="inline-flex items-center gap-2 text-xs text-google-gray-700">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
            {s.label}
          </span>
        ))}
        {target !== undefined && (
          <span className="inline-flex items-center gap-2 text-xs text-google-gray-700">
            <span className="h-0 w-4 border-t-2 border-dashed" style={{ borderColor: '#EA4335' }} />
            {targetLabel}
          </span>
        )}
      </div>

      <div className="relative">
        <svg
          viewBox={`0 0 ${W} ${height}`}
          className="w-full h-auto block"
          role="img"
          aria-label={ariaLabel}
          onMouseMove={onMove}
          onMouseLeave={() => setHover(null)}
        >
          {yTicks.map((t) => (
            <g key={t}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} stroke="#E8EAED" strokeWidth="1" />
              <text x={PAD.left - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill="#70757A">{formatY(t)}</text>
            </g>
          ))}
          {xLabelIdx.map((i) => (
            <text key={i} x={x(i)} y={height - 8} textAnchor={i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle'} fontSize="11" fill="#70757A">
              {formatX(data[i][xKey])}
            </text>
          ))}

          {target !== undefined && (
            <line x1={PAD.left} x2={W - PAD.right} y1={y(target)} y2={y(target)} stroke="#EA4335" strokeWidth="1.5" strokeDasharray="6 5" />
          )}

          {series.map((s) => {
            const line = data.map((d, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(d[s.key]).toFixed(1)}`).join(' ');
            return (
              <g key={s.key}>
                {s.area && n > 1 && (
                  <path d={`${line} L${x(n - 1).toFixed(1)},${y(yMin)} L${x(0).toFixed(1)},${y(yMin)} Z`} fill={s.color} opacity="0.12" />
                )}
                <path d={line} fill="none" stroke={s.color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
              </g>
            );
          })}

          {hovered && (
            <g>
              <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={PAD.top + plotH} stroke="#9AA0A6" strokeWidth="1" strokeDasharray="3 3" />
              {series.map((s) => (
                <circle key={s.key} cx={x(hover)} cy={y(hovered[s.key])} r="4.5" fill="#fff" stroke={s.color} strokeWidth="2.5" />
              ))}
            </g>
          )}
        </svg>

        {hovered && (
          <div
            className="pointer-events-none absolute top-2 z-10 rounded-lg border border-google-gray-200 bg-white px-3 py-2 text-xs shadow-lg"
            style={{ left: `${leftPct}%`, transform: leftPct > 65 ? 'translateX(calc(-100% - 12px))' : 'translateX(12px)' }}
          >
            <div className="font-semibold text-google-gray-900 mb-1">{formatTip(hovered[xKey])}</div>
            {series.map((s) => (
              <div key={s.key} className="flex items-center justify-between gap-4 text-google-gray-700">
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
                  {s.label}
                </span>
                <span className="font-semibold text-google-gray-900">{formatY(hovered[s.key], true)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Horizontal bars for a ranked breakdown. items: [{ key, label, value, color, note? }]
export function BarList({ items, format, columns = 1, showShare = true, emptyText = 'Nothing to show for this period.' }) {
  if (!items.length) return <div className="text-sm text-google-gray-600">{emptyText}</div>;
  const max = Math.max(...items.map((i) => i.value)) || 1;
  const total = items.reduce((sum, i) => sum + i.value, 0) || 1;
  return (
    <ul className={columns === 2 ? 'grid grid-cols-1 lg:grid-cols-2 gap-x-12 gap-y-4' : 'space-y-4'}>
      {items.map((item) => (
        <li key={item.key}>
          <div className="flex justify-between items-baseline gap-3 text-sm mb-1.5">
            <span className="font-medium text-google-gray-900 truncate">
              {item.label}
              {item.note && <span className="ml-2 text-xs font-normal text-google-gray-500">{item.note}</span>}
            </span>
            <span className="shrink-0 text-google-gray-700">
              <span className="font-bold text-google-gray-900">{format(item.value)}</span>
              {showShare && <span className="ml-2 text-xs text-google-gray-500">{Math.round((item.value / total) * 100)}%</span>}
            </span>
          </div>
          <div className="h-2.5 rounded-full bg-google-gray-100 overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${(item.value / max) * 100}%`, backgroundColor: item.color }} />
          </div>
        </li>
      ))}
    </ul>
  );
}
