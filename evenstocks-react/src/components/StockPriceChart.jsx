import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { getStockEod, getStockIntraday } from '../services/tradingApi';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
);

const RANGES = [
  { key: '1M', days: 30 },
  { key: '3M', days: 90 },
  { key: '6M', days: 180 },
  { key: '1Y', days: 365 },
  { key: 'INTRADAY', days: 0 },
];

const StockPriceChart = ({ nseSymbol, bseScrip, isDark = true }) => {
  const [range, setRange] = useState('3M');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Cache per (symbol, range) — switching ranges after the first load is instant
  // and doesn't re-hit the server.  Cleared when the stock itself changes.
  const cacheRef = useRef({});
  const lastKeyRef = useRef(null);

  useEffect(() => {
    if (!nseSymbol && !bseScrip) return;
    const stockKey = nseSymbol || bseScrip;
    // New stock → blow the cache for the previous one.
    if (lastKeyRef.current && lastKeyRef.current !== stockKey) {
      cacheRef.current = {};
    }
    lastKeyRef.current = stockKey;

    const cacheKey = `${stockKey}::${range}`;
    if (cacheRef.current[cacheKey]) {
      setData(cacheRef.current[cacheKey]);
      setError('');
      return;
    }

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const active = RANGES.find((r) => r.key === range);
        const resp = active.key === 'INTRADAY'
          ? await getStockIntraday({ nseSymbol, bseScrip })
          : await getStockEod({ nseSymbol, bseScrip, days: active.days });
        if (cancelled) return;
        cacheRef.current[cacheKey] = resp;
        setData(resp);
      } catch (e) {
        if (!cancelled) setError(String(e.message || e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [nseSymbol, bseScrip, range]);

  const chartData = useMemo(() => {
    if (!data?.data?.length) return null;
    const isIntra = range === 'INTRADAY';
    const labels = data.data.map((row) => row.timestamp || row.date);
    const prices = data.data.map((row) =>
      isIntra ? Number(row.price) : Number(row.close ?? row.ltp)
    );
    return {
      labels,
      datasets: [{
        label: isIntra ? 'LTP (₹)' : 'Close (₹)',
        data: prices,
        borderColor: '#02634d',
        backgroundColor: 'rgba(2, 99, 77, 0.14)',
        fill: true,
        borderWidth: 2,
        pointRadius: isIntra ? 0 : 2,
        pointHoverRadius: 5,
        tension: 0.25,
      }],
    };
  }, [data, range]);

  const options = useMemo(() => ({
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
      x: {
        ticks: {
          color: isDark ? '#9ca3af' : '#4b5563',
          maxTicksLimit: 8, autoSkip: true,
        },
        grid: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' },
      },
      y: {
        ticks: {
          color: isDark ? '#9ca3af' : '#4b5563',
          callback: (v) => `₹${v}`,
        },
        grid: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' },
      },
    },
  }), [isDark]);

  const bg = isDark ? '#141a18' : '#ffffff';
  const border = isDark ? '#24302b' : '#e4e8e6';
  const text = isDark ? '#e4e6e4' : '#111827';
  const muted = isDark ? '#9ca3af' : '#6b7280';

  return (
    <div style={{
      background: bg, border: `1px solid ${border}`, borderRadius: 10,
      padding: 16, color: text,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            {data?.resolved_symbol || nseSymbol || bseScrip} — Price
          </div>
          <div style={{ fontSize: 11, color: muted }}>
            {data?.count != null && `${data.count} ${range === 'INTRADAY' ? 'ticks today' : 'days'}`}
            {data?.resolve_note && (
              <span style={{ marginLeft: 6, opacity: 0.7 }}>
                · {data.resolve_note}
              </span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {RANGES.map((r) => (
            <button
              key={r.key}
              onClick={() => setRange(r.key)}
              style={{
                padding: '4px 10px', fontSize: 11, fontWeight: 600,
                border: `1px solid ${border}`,
                background: range === r.key ? '#02634d' : 'transparent',
                color: range === r.key ? '#fff' : muted,
                borderRadius: 4, cursor: 'pointer',
              }}>
              {r.key === 'INTRADAY' ? '1D' : r.key}
            </button>
          ))}
        </div>
      </div>
      <div style={{ height: 260 }}>
        {loading && <div style={{ color: muted, fontSize: 13 }}>Loading…</div>}
        {!loading && error && (
          <div style={{ color: '#f87171', fontSize: 13 }}>Failed: {error}</div>
        )}
        {!loading && !error && !chartData && (
          <div style={{ color: muted, fontSize: 13 }}>
            No data yet. Run the backfill or 4 PM capture.
          </div>
        )}
        {!loading && !error && chartData && <Line data={chartData} options={options} />}
      </div>
    </div>
  );
};

export default StockPriceChart;
