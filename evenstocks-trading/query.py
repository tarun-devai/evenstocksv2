"""
Read API for the trading database — use this from the website / backend / LLM.

Query by NSE symbol OR BSE scrip code OR company name.  The module does fuzzy
matching against the ``company_name`` column in eod_nse / eod_bse so that a
user typing "tata motors" gets resolved to symbol TATAMOTORS / scrip 500570.

Typical use from the Node/Flask backend:

    from evenstocks_trading.query import find_stock, get_eod, get_intraday

    hits = find_stock("tata motors")
    # → [{"nse_symbol": "TATAMOTORS", "bse_scrip": "500570", "name": "Tata Motors Ltd", ...}]

    eod = get_eod(nse_symbol="TATAMOTORS", days=90)
    intraday = get_intraday(nse_symbol="TATAMOTORS", d=date.today())
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from storage import connect, normalize_name


# ═══════════════════════════════════════════════════════════════
#  LOOKUP — resolve user input to symbol / scrip code
# ═══════════════════════════════════════════════════════════════

def find_stock(query: str, *, limit: int = 10) -> List[Dict[str, Any]]:
    """Fuzzy-find stocks by any of: company name, NSE symbol, BSE scrip code,
    BSE SC_NAME, Screener slug, ISIN.

    Uses the ``stock_master`` + ``stock_alias`` tables populated by
    ``build_mapping.py``.  Falls back to a direct LIKE scan of eod_nse /
    eod_bse if mapping tables are empty (first run before mapping was built).

    Matching strategy (in order):
      1. Exact match on normalized alias  → returns 1 authoritative row
      2. Prefix match on normalized alias  → substring matches
      3. Substring match on normalized company name

    Results merged by stock_master.id so the same company isn't listed twice.
    """
    raw = query.strip()
    if not raw:
        return []
    q_norm = normalize_name(raw)
    q_upper = raw.upper()

    with connect() as c:
        c.row_factory = _row_dict

        # If the mapping table is empty, fall back to the old LIKE scan.
        count = c.execute("SELECT COUNT(*) AS n FROM stock_master").fetchone()["n"]
        if count == 0:
            return _find_stock_legacy(c, q_upper, limit)

        # 1. Exact match on alias_norm — fastest, strongest signal.
        exact = c.execute("""
            SELECT DISTINCT m.id, m.isin, m.nse_symbol, m.bse_scrip,
                   m.company_name AS name, m.screener_slug,
                   1 AS match_rank
            FROM stock_alias a
            JOIN stock_master m ON m.id = a.stock_id
            WHERE a.alias_norm = ?
            LIMIT ?
        """, (q_norm, limit)).fetchall()

        if len(exact) >= limit or (exact and q_norm == exact[0]["nse_symbol"] and False):
            return [_clean(r) for r in exact]

        # 2. Prefix on alias_norm (handles "TATAMOT" → TATAMOTORS).
        prefix = c.execute("""
            SELECT DISTINCT m.id, m.isin, m.nse_symbol, m.bse_scrip,
                   m.company_name AS name, m.screener_slug,
                   2 AS match_rank
            FROM stock_alias a
            JOIN stock_master m ON m.id = a.stock_id
            WHERE a.alias_norm LIKE ? AND a.alias_norm != ?
            LIMIT ?
        """, (q_norm + "%", q_norm, limit)).fetchall()

        # 3. Substring on alias_norm (handles typing partial company name).
        needed = max(0, limit - len(exact) - len(prefix))
        substr = []
        if needed and len(q_norm) >= 3:
            substr = c.execute("""
                SELECT DISTINCT m.id, m.isin, m.nse_symbol, m.bse_scrip,
                       m.company_name AS name, m.screener_slug,
                       3 AS match_rank
                FROM stock_alias a
                JOIN stock_master m ON m.id = a.stock_id
                WHERE a.alias_norm LIKE ? AND a.alias_norm NOT LIKE ?
                LIMIT ?
            """, ("%" + q_norm + "%", q_norm + "%", needed)).fetchall()

    # Merge by master id — prefer earlier (better) match_rank.
    seen: Dict[int, Dict[str, Any]] = {}
    for r in exact + prefix + substr:
        if r["id"] not in seen:
            seen[r["id"]] = r
    return [_clean(r) for r in list(seen.values())[:limit]]


def _clean(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "nse_symbol": row.get("nse_symbol"),
        "bse_scrip": row.get("bse_scrip"),
        "name": row.get("name"),
        "screener_slug": row.get("screener_slug"),
        "isin": row.get("isin"),
    }


def _find_stock_legacy(c, q_upper: str, limit: int) -> List[Dict[str, Any]]:
    """LIKE-based fallback used only before build_mapping.py has been run."""
    sql = """
        WITH nse AS (
            SELECT DISTINCT symbol AS nse_symbol, NULL AS bse_scrip,
                            company_name AS name, isin
            FROM eod_nse
            WHERE UPPER(symbol) LIKE ? OR UPPER(company_name) LIKE ?
        ),
        bse AS (
            SELECT DISTINCT NULL AS nse_symbol, scrip_code AS bse_scrip,
                            company_name AS name, isin
            FROM eod_bse
            WHERE scrip_code = ? OR UPPER(company_name) LIKE ?
        )
        SELECT * FROM nse UNION ALL SELECT * FROM bse
    """
    like = f"%{q_upper}%"
    rows = c.execute(sql, (like, like, q_upper, like)).fetchall()
    merged: Dict[str, Dict[str, Any]] = {}
    loose: List[Dict[str, Any]] = []
    for r in rows:
        if r.get("isin"):
            slot = merged.setdefault(r["isin"], {
                "nse_symbol": None, "bse_scrip": None,
                "name": r.get("name"), "isin": r["isin"], "screener_slug": None,
            })
            if r.get("nse_symbol"): slot["nse_symbol"] = r["nse_symbol"]
            if r.get("bse_scrip"): slot["bse_scrip"] = r["bse_scrip"]
        else:
            loose.append({**r, "screener_slug": None})
    return (list(merged.values()) + loose)[:limit]


def resolve(query: str) -> Optional[Dict[str, Any]]:
    """Return the single best-match stock, or None."""
    hits = find_stock(query, limit=1)
    return hits[0] if hits else None


# ═══════════════════════════════════════════════════════════════
#  EOD — daily OHLCV
# ═══════════════════════════════════════════════════════════════

def get_eod(
    *,
    nse_symbol: Optional[str] = None,
    bse_scrip: Optional[str] = None,
    days: int = 90,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Daily OHLCV for one stock.  Give either nse_symbol or bse_scrip.

    If ``from_date`` / ``to_date`` aren't set, returns the last ``days`` days.
    """
    if (nse_symbol is None) == (bse_scrip is None):
        raise ValueError("Pass exactly one of nse_symbol or bse_scrip")

    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=days)

    if nse_symbol:
        sql = """SELECT date, open, high, low, close, ltp, prev_close, volume, value, series
                 FROM eod_nse
                 WHERE symbol = ? AND date BETWEEN ? AND ?
                 ORDER BY date"""
        args = (nse_symbol.upper(), from_date.isoformat(), to_date.isoformat())
    else:
        sql = """SELECT date, open, high, low, close, ltp, prev_close, volume, value, series
                 FROM eod_bse
                 WHERE scrip_code = ? AND date BETWEEN ? AND ?
                 ORDER BY date"""
        args = (str(bse_scrip), from_date.isoformat(), to_date.isoformat())

    with connect() as c:
        c.row_factory = _row_dict
        return c.execute(sql, args).fetchall()


# ═══════════════════════════════════════════════════════════════
#  INTRADAY — minute-ticks
# ═══════════════════════════════════════════════════════════════

def get_intraday(
    *,
    nse_symbol: Optional[str] = None,
    bse_scrip: Optional[str] = None,
    d: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Minute-level LTP series for one stock on one date.  Default = today."""
    if (nse_symbol is None) == (bse_scrip is None):
        raise ValueError("Pass exactly one of nse_symbol or bse_scrip")

    d = d or date.today()
    day_start = f"{d.isoformat()} 00:00:00"
    day_end = f"{d.isoformat()} 23:59:59"

    if nse_symbol:
        sql = """SELECT timestamp, price FROM intraday_nse
                 WHERE symbol = ? AND timestamp BETWEEN ? AND ?
                 ORDER BY timestamp"""
        args = (nse_symbol.upper(), day_start, day_end)
    else:
        sql = """SELECT timestamp, price FROM intraday_bse
                 WHERE scrip_code = ? AND timestamp BETWEEN ? AND ?
                 ORDER BY timestamp"""
        args = (str(bse_scrip), day_start, day_end)

    with connect() as c:
        c.row_factory = _row_dict
        return c.execute(sql, args).fetchall()


def get_intraday_range(
    *,
    nse_symbol: Optional[str] = None,
    bse_scrip: Optional[str] = None,
    from_ts: str,
    to_ts: str,
) -> List[Dict[str, Any]]:
    """Minute ticks across a custom timestamp range (YYYY-MM-DD HH:MM:SS)."""
    if (nse_symbol is None) == (bse_scrip is None):
        raise ValueError("Pass exactly one of nse_symbol or bse_scrip")

    if nse_symbol:
        sql = """SELECT timestamp, price FROM intraday_nse
                 WHERE symbol = ? AND timestamp BETWEEN ? AND ?
                 ORDER BY timestamp"""
        args = (nse_symbol.upper(), from_ts, to_ts)
    else:
        sql = """SELECT timestamp, price FROM intraday_bse
                 WHERE scrip_code = ? AND timestamp BETWEEN ? AND ?
                 ORDER BY timestamp"""
        args = (str(bse_scrip), from_ts, to_ts)

    with connect() as c:
        c.row_factory = _row_dict
        return c.execute(sql, args).fetchall()


# ═══════════════════════════════════════════════════════════════
#  helpers
# ═══════════════════════════════════════════════════════════════

def _row_dict(cursor, row):
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


if __name__ == "__main__":
    import argparse, json

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("find"); p1.add_argument("query")
    p2 = sub.add_parser("eod")
    p2.add_argument("--nse"); p2.add_argument("--bse"); p2.add_argument("--days", type=int, default=30)
    p3 = sub.add_parser("intraday")
    p3.add_argument("--nse"); p3.add_argument("--bse"); p3.add_argument("--date")

    args = ap.parse_args()
    if args.cmd == "find":
        print(json.dumps(find_stock(args.query), indent=2, default=str))
    elif args.cmd == "eod":
        print(json.dumps(
            get_eod(nse_symbol=args.nse, bse_scrip=args.bse, days=args.days),
            indent=2, default=str,
        ))
    elif args.cmd == "intraday":
        d = date.fromisoformat(args.date) if args.date else None
        print(json.dumps(
            get_intraday(nse_symbol=args.nse, bse_scrip=args.bse, d=d),
            indent=2, default=str,
        ))
