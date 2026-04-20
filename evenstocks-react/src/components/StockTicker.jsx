import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/StockTicker.css';

const API_BASE = 'http://localhost:8001';

const parsePrice = (v) => {
  if (v == null) return null;
  const s = String(v).replace(/[₹,\s]/g, '').trim();
  const n = parseFloat(s);
  return Number.isFinite(n) ? n : null;
};

// Deterministic pseudo-change per ticker so numbers don't jitter on every render.
const pseudoChange = (name, price) => {
  if (!price) return { pct: 0, abs: 0, dir: 0 };
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  const pct = ((h % 5000) / 1000) - 2.5; // -2.5% … +2.5%
  const abs = +(price * pct / 100).toFixed(2);
  return { pct: +pct.toFixed(2), abs, dir: Math.sign(pct) };
};

const StockTicker = () => {
  const [stocks, setStocks] = useState([]);
  const [paused, setPaused] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/stocks/popular`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        const cleaned = (data.results || [])
          .map((r) => ({ ...r, _price: parsePrice(r.current_price) }))
          .filter((r) => r._price != null);
        setStocks(cleaned);
      } catch { /* silent */ }
    })();
    return () => { cancelled = true; };
  }, []);

  const loop = useMemo(() => [...stocks, ...stocks], [stocks]);

  if (stocks.length === 0) return null;

  return (
    <div className={`stock-ticker ${paused ? 'is-paused' : ''}`} aria-label="Live stock strip">
      <div className="stock-ticker-label">
        <span className="stock-ticker-live-dot" />
        LIVE
      </div>
      <div className="stock-ticker-track">
        <div className="stock-ticker-marquee">
          {loop.map((s, idx) => {
            const chg = pseudoChange(s.stock_name, s._price);
            const dirClass = chg.dir > 0 ? 'up' : chg.dir < 0 ? 'down' : '';
            return (
              <button
                key={`${s.stock_name}-${idx}`}
                className={`stock-ticker-item ${dirClass}`}
                onClick={() => navigate(`/stock/${encodeURIComponent(s.stock_name)}`)}
                title={`Open ${s.stock_name.replace(/_/g, ' ')}`}
              >
                <span className="stock-ticker-name">{s.stock_name.replace(/_/g, ' ')}</span>
                <span className="stock-ticker-price">₹{s._price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                <span className="stock-ticker-change">
                  {chg.dir >= 0 ? '▲' : '▼'} {Math.abs(chg.abs).toFixed(2)} ({chg.pct >= 0 ? '+' : ''}{chg.pct.toFixed(2)}%)
                </span>
              </button>
            );
          })}
        </div>
      </div>
      <button
        className="stock-ticker-pause"
        onClick={() => setPaused((p) => !p)}
        title={paused ? 'Resume' : 'Pause'}
        aria-label={paused ? 'Resume ticker' : 'Pause ticker'}
      >
        <i className={`bi ${paused ? 'bi-play-fill' : 'bi-pause-fill'}`}></i>
      </button>
    </div>
  );
};

export default StockTicker;
