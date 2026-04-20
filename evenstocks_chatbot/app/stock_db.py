"""
stock_db.py — Search and fetch stock data from stocks.db
"""

import os
import json
import sqlite3

try:
    import urllib.request as _urlreq
    import urllib.parse as _urlparse
    _HTTP_OK = True
except ImportError:
    _HTTP_OK = False

DB_PATH = os.path.join("data", "stocks.db")

# evenstocks-api runs at :5809 on the host; inside docker-compose the service
# name is "evenstocks-api".  Override via env if needed.
TRADING_API_BASE = os.environ.get("TRADING_API_BASE", "http://evenstocks-api:5809")


def get_conn() -> sqlite3.Connection | None:
    if not os.path.exists(DB_PATH):
        return None
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def search_stocks(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    """Fuzzy search stocks by name. Returns list of {stock_name, url, market_cap}.
    Empty query returns all stocks (limited). Case- and separator-insensitive: 'tatamotors',
    'Tata Motors', 'TATA_MOTORS' all match 'Tata_Motors'."""
    q = query.strip().lower().replace(" ", "").replace("_", "").replace(".", "").replace("-", "")
    rows = conn.execute(
        """SELECT stock_name, url, market_cap, current_price, stock_pe
           FROM company_info
           WHERE REPLACE(REPLACE(REPLACE(LOWER(stock_name), '_', ''), '-', ''), '.', '') LIKE ?
           ORDER BY
             CASE
               WHEN REPLACE(REPLACE(REPLACE(LOWER(stock_name), '_', ''), '-', ''), '.', '') = ? THEN 0
               WHEN REPLACE(REPLACE(REPLACE(LOWER(stock_name), '_', ''), '-', ''), '.', '') LIKE ? THEN 1
               ELSE 2
             END,
             stock_name
           LIMIT ?""",
        (f"%{q}%", q, f"{q}%", limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_company_info(conn: sqlite3.Connection, stock_name: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM company_info WHERE stock_name = ?", (stock_name,)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    # Parse JSON fields
    for key in ("pros", "cons"):
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
    return d


def get_financial_tables(conn: sqlite3.Connection, stock_name: str) -> dict:
    rows = conn.execute(
        "SELECT table_type, data FROM financial_tables WHERE stock_name = ?",
        (stock_name,),
    ).fetchall()
    tables = {}
    for r in rows:
        try:
            tables[r["table_type"]] = json.loads(r["data"])
        except Exception:
            tables[r["table_type"]] = []
    return tables


def get_pdf_texts(conn: sqlite3.Connection, stock_name: str) -> list[dict]:
    try:
        rows = conn.execute(
            """SELECT doc_type, title, text FROM pdf_texts
               WHERE stock_name = ? AND text != ''
               ORDER BY doc_type, doc_index""",
            (stock_name,),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []


def build_stock_context(conn: sqlite3.Connection, stock_name: str) -> str | None:
    """Build a full text context block for Claude from all stock data."""
    info = get_company_info(conn, stock_name)
    if not info:
        return None

    parts = []
    parts.append(f"# {stock_name.replace('_', ' ')}")
    parts.append(f"URL: {info.get('url', '')}\n")

    # Key metrics
    parts.append("## Key Metrics")
    for key in ("market_cap", "current_price", "high_low", "stock_pe",
                 "book_value", "dividend_yield", "roce", "roe", "face_value"):
        val = info.get(key, "")
        if val:
            label = key.replace("_", " ").title()
            parts.append(f"- {label}: {val}")

    # About
    if info.get("about"):
        parts.append(f"\n## About\n{info['about']}")

    # Pros / Cons
    for section in ("pros", "cons"):
        items = info.get(section, [])
        if items and isinstance(items, list):
            parts.append(f"\n## {section.title()}")
            for item in items:
                parts.append(f"- {item}")

    # Financial tables
    tables = get_financial_tables(conn, stock_name)
    for table_type, data in tables.items():
        if not data:
            continue
        parts.append(f"\n## {table_type.replace('-', ' ').title()}")
        # Convert table rows to readable text
        rows = data if isinstance(data, list) and data and isinstance(data[0], dict) else []
        if not rows and isinstance(data, list) and data and isinstance(data[0], list):
            # nested tables — flatten first one
            rows = data[0] if data[0] and isinstance(data[0][0], dict) else []
        for row in rows[:20]:  # limit rows to keep context manageable
            line = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
            parts.append(line)

    # PDF document texts (trimmed)
    pdf_texts = get_pdf_texts(conn, stock_name)
    for doc in pdf_texts[:4]:  # limit documents
        doc_type = doc["doc_type"].replace("_", " ").title()
        title = doc["title"]
        text = doc["text"][:3000]  # trim long texts
        parts.append(f"\n## Document: {doc_type} — {title}")
        parts.append(text)

    # Trading data (NSE EOD last 30 days + today's intraday summary)
    trading_ctx = _fetch_trading_context(stock_name)
    if trading_ctx:
        parts.append("\n## Trading Data (NSE)")
        parts.append(trading_ctx)

    return "\n".join(parts)


def _http_get_json(path: str, params: dict) -> dict | None:
    if not _HTTP_OK:
        print(f"[trading-api] urllib not available, skipping {path}")
        return None
    qs = _urlparse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{TRADING_API_BASE}{path}?{qs}"
    try:
        with _urlreq.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # Log so "trading data not provided" in LLM output can be traced to an
        # actual network failure rather than silent emptiness.
        print(f"[trading-api] {path} failed: {type(e).__name__}: {e}")
        return None


def resolve_nse_symbol(stock_name: str) -> str | None:
    """Screener-style 'Tata_Motors' → NSE symbol 'TATAMOTORS' via trading API."""
    pretty = stock_name.replace("_", " ").strip()
    hits = _http_get_json("/api/stock/search", {"q": pretty, "limit": 3}) or {}
    for r in hits.get("results") or []:
        if r.get("nse_symbol"):
            return r["nse_symbol"]
    return None


def get_eod_rows(nse_symbol: str, days: int = 90) -> list[dict]:
    """Fetch EOD rows from trading API. Returns [] if unavailable."""
    resp = _http_get_json("/api/stock/eod", {"symbol": nse_symbol, "days": days}) or {}
    return resp.get("data") or []


def _sma(values: list[float], window: int) -> float | None:
    vs = [v for v in values if isinstance(v, (int, float))]
    if len(vs) < window:
        return None
    return sum(vs[-window:]) / window


def _rsi(closes: list[float], period: int = 14) -> float | None:
    closes = [c for c in closes if isinstance(c, (int, float))]
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        delta = closes[-i] - closes[-i - 1]
        (gains if delta > 0 else losses).append(abs(delta))
    avg_g = sum(gains) / period if gains else 0
    avg_l = sum(losses) / period if losses else 0
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return round(100 - (100 / (1 + rs)), 2)


def compute_indicators(rows: list[dict]) -> dict:
    """Compute simple technical indicators from EOD rows (ordered ascending by date)."""
    closes = [r.get("close") for r in rows if r.get("close") is not None]
    highs = [r.get("high") for r in rows if r.get("high") is not None]
    lows = [r.get("low") for r in rows if r.get("low") is not None]
    vols = [r.get("volume") or 0 for r in rows]

    if not closes:
        return {}

    last = closes[-1]
    return {
        "last_close": round(last, 2),
        "sma_20": round(_sma(closes, 20), 2) if _sma(closes, 20) else None,
        "sma_50": round(_sma(closes, 50), 2) if _sma(closes, 50) else None,
        "sma_200": round(_sma(closes, 200), 2) if _sma(closes, 200) else None,
        "rsi_14": _rsi(closes, 14),
        "period_high": round(max(highs), 2) if highs else None,
        "period_low": round(min(lows), 2) if lows else None,
        "pct_from_high": round((last / max(highs) - 1) * 100, 2) if highs else None,
        "pct_from_low": round((last / min(lows) - 1) * 100, 2) if lows else None,
        "avg_volume": int(sum(vols) / len(vols)) if vols else None,
        "last_volume": int(vols[-1]) if vols else None,
        "trend_5d": round(((last / closes[-6]) - 1) * 100, 2) if len(closes) >= 6 else None,
        "trend_30d": round(((last / closes[-31]) - 1) * 100, 2) if len(closes) >= 31 else None,
    }


def _fetch_trading_context(stock_name: str) -> str | None:
    """Build technical context block for the LLM: price history + indicators."""
    nse_symbol = resolve_nse_symbol(stock_name)
    if not nse_symbol:
        return None

    rows = get_eod_rows(nse_symbol, days=90)
    if not rows:
        return f"Resolved to NSE:{nse_symbol} — no EOD data yet in trading DB."

    ind = compute_indicators(rows)

    def _fmt(v, suffix=""):
        if v is None: return "N/A"
        if isinstance(v, (int, float)): return f"{v:,.2f}{suffix}"
        return str(v)

    lines = [
        f"- NSE symbol: {nse_symbol}",
        f"- Last close: ₹{_fmt(ind.get('last_close'))}",
        f"- 5-day move: {_fmt(ind.get('trend_5d'), '%')}   30-day move: {_fmt(ind.get('trend_30d'), '%')}",
        f"- 90-day range: ₹{_fmt(ind.get('period_low'))} – ₹{_fmt(ind.get('period_high'))}  "
        f"(now {_fmt(ind.get('pct_from_high'), '%')} from high, {_fmt(ind.get('pct_from_low'), '%')} from low)",
        f"- Moving averages: SMA20={_fmt(ind.get('sma_20'))}  SMA50={_fmt(ind.get('sma_50'))}  SMA200={_fmt(ind.get('sma_200'))}",
        f"- RSI(14): {_fmt(ind.get('rsi_14'))}  (>70 overbought, <30 oversold)",
        f"- Volume: last={ind.get('last_volume') or 0:,}  avg-90d={ind.get('avg_volume') or 0:,}",
    ]

    lines.append("\nRecent daily OHLC (most recent last):")
    for r in rows[-10:]:
        lines.append(
            f"  {r.get('date')}  O:{_fmt(r.get('open'))}  H:{_fmt(r.get('high'))}  "
            f"L:{_fmt(r.get('low'))}  C:{_fmt(r.get('close'))}  V:{r.get('volume') or 0:,}"
        )
    return "\n".join(lines)
