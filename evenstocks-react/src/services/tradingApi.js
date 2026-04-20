/**
 * Client for the trading data endpoints served by evenstocks-api (Flask, :5809).
 * Backed by SQLite in evenstocks-trading/data/trading.db.
 */

const API_BASE = process.env.REACT_APP_TRADING_API || 'http://localhost:5809';

async function _get(path, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v != null && v !== '')
  ).toString();
  const url = `${API_BASE}${path}${qs ? `?${qs}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    // Try to pull the JSON error body — Flask gives us message + hint on 503.
    let detail = '';
    try {
      const body = await res.json();
      detail = body.message || body.error || body.hint || '';
      if (body.hint) detail += ` — ${body.hint}`;
    } catch { /* non-JSON body, keep empty */ }
    throw new Error(`${res.status} ${detail || res.statusText}`);
  }
  return res.json();
}

/** Fuzzy search stocks by name / NSE symbol / BSE scrip code. */
export const searchStocks = (query, limit = 10) =>
  _get('/api/stock/search', { q: query, limit });

/** Daily OHLCV history.  Pass nse_symbol OR bse_scrip. */
export const getStockEod = ({ nseSymbol, bseScrip, days = 90 } = {}) =>
  _get('/api/stock/eod', {
    symbol: nseSymbol,
    scrip: bseScrip,
    days,
  });

/** Minute-level ticks for one date (default today).  Pass nse_symbol OR bse_scrip. */
export const getStockIntraday = ({ nseSymbol, bseScrip, date } = {}) =>
  _get('/api/stock/intraday', {
    symbol: nseSymbol,
    scrip: bseScrip,
    date,
  });
