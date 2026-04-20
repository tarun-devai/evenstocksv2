import React, { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Filler,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

/**
 * Compact chart card rendered inline after a chatbot response.
 * Props:
 *   charts: [{ screener_name, nse_symbol, eod: [{date, close, ...}] }]
 *   isDark: bool
 */
const InlineStockChart = ({ charts, isDark = true }) => {
  if (!charts || charts.length === 0) return null;

  const bg = isDark ? '#141a18' : '#ffffff';
  const border = isDark ? '#24302b' : '#e4e8e6';
  const text = isDark ? '#e4e6e4' : '#111827';
  const muted = isDark ? '#9ca3af' : '#6b7280';

  // One row when 1 chart, two-column grid when 2+, so comparisons sit side-by-side
  const gridCols = charts.length >= 2 ? 'repeat(2, minmax(0, 1fr))' : '1fr';

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: gridCols, gap: 12, marginTop: 12,
    }}>
      {charts.map((c) => {
        const rows = c.eod || [];
        const firstClose = rows.length ? Number(rows[0].close) : null;
        const lastClose = rows.length ? Number(rows[rows.length - 1].close) : null;
        const change = firstClose && lastClose ? (lastClose - firstClose) : 0;
        const pct = firstClose ? (change / firstClose) * 100 : 0;
        const up = change >= 0;
        const color = up ? '#16a34a' : '#dc2626';
        const bgRgba = up ? 'rgba(22, 163, 74, 0.14)' : 'rgba(220, 38, 38, 0.14)';

        const data = {
          labels: rows.map((r) => r.date),
          datasets: [{
            label: c.nse_symbol,
            data: rows.map((r) => Number(r.close)),
            borderColor: color,
            backgroundColor: bgRgba,
            fill: true,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            tension: 0.25,
          }],
        };

        const options = {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { intersect: false, mode: 'index' },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => `₹${Number(ctx.parsed.y).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
              },
            },
          },
          scales: {
            x: { display: false },
            y: {
              ticks: { color: muted, callback: (v) => `₹${v}` },
              grid: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' },
            },
          },
        };

        return (
          <div key={c.nse_symbol} style={{
            background: bg, border: `1px solid ${border}`, borderRadius: 8,
            padding: 12, color: text,
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 6 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700 }}>
                  {c.nse_symbol}
                  <span style={{ fontSize: 11, color: muted, fontWeight: 400, marginLeft: 6 }}>
                    {(c.screener_name || '').replace(/_/g, ' ')}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: muted }}>
                  {rows.length} days
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 14, fontWeight: 700 }}>
                  ₹{lastClose?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </div>
                <div style={{ fontSize: 11, fontWeight: 700, color }}>
                  {up ? '▲' : '▼'} ₹{Math.abs(change).toFixed(2)} ({pct >= 0 ? '+' : ''}{pct.toFixed(2)}%)
                </div>
              </div>
            </div>
            <div style={{ height: 160 }}>
              <Line data={data} options={options} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default InlineStockChart;
