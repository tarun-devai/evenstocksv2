"""
Build the unified stock mapping (stock_master + stock_alias).

NSE symbols, BSE scrip codes, and Screener slugs all refer to the same
underlying companies — but use different strings.  This script walks the
trading DB (eod_nse + eod_bse) and, optionally, the Screener stocks.db, and
produces:

  stock_master   — one row per company, keyed by ISIN where possible
  stock_alias    — every name/ticker/scrip that should resolve to that row,
                   stored both raw and in a normalized form for matching

Run after every backfill.  Idempotent — it rewrites the two tables each time.

Usage:
    python build_mapping.py
    python build_mapping.py --screener-db /path/to/stocks.db
    python build_mapping.py --verbose

The Screener DB lives at ``evenstocks_chatbot/data/stocks.db`` by default.
"""

from __future__ import annotations

import argparse
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from storage import DB_PATH, connect, init_db, normalize_name


DEFAULT_SCREENER_DB = (
    Path(__file__).parent.parent / "evenstocks_chatbot" / "data" / "stocks.db"
)


def _pull_nse(conn: sqlite3.Connection) -> list[dict]:
    """One row per distinct NSE symbol — with its most-recent ISIN + company name."""
    rows = conn.execute("""
        SELECT
            symbol,
            MAX(date)       AS last_seen,
            MIN(date)       AS first_seen,
            (SELECT isin FROM eod_nse e2
               WHERE e2.symbol = e1.symbol AND e2.isin IS NOT NULL AND e2.isin <> ''
               ORDER BY date DESC LIMIT 1)                AS isin,
            (SELECT company_name FROM eod_nse e2
               WHERE e2.symbol = e1.symbol AND e2.company_name IS NOT NULL AND e2.company_name <> ''
               ORDER BY date DESC LIMIT 1)                AS company_name
        FROM eod_nse e1
        GROUP BY symbol
    """).fetchall()
    return [
        {"symbol": r[0], "last_seen": r[1], "first_seen": r[2],
         "isin": r[3], "company_name": r[4]}
        for r in rows
    ]


def _pull_bse(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT
            scrip_code,
            MAX(date) AS last_seen,
            MIN(date) AS first_seen,
            (SELECT isin FROM eod_bse e2
               WHERE e2.scrip_code = e1.scrip_code AND e2.isin IS NOT NULL AND e2.isin <> ''
               ORDER BY date DESC LIMIT 1)              AS isin,
            (SELECT company_name FROM eod_bse e2
               WHERE e2.scrip_code = e1.scrip_code AND e2.company_name IS NOT NULL AND e2.company_name <> ''
               ORDER BY date DESC LIMIT 1)              AS company_name,
            (SELECT symbol FROM eod_bse e2
               WHERE e2.scrip_code = e1.scrip_code AND e2.symbol IS NOT NULL AND e2.symbol <> ''
               ORDER BY date DESC LIMIT 1)              AS symbol
        FROM eod_bse e1
        GROUP BY scrip_code
    """).fetchall()
    return [
        {"scrip_code": r[0], "last_seen": r[1], "first_seen": r[2],
         "isin": r[3], "company_name": r[4], "bse_ticker": r[5]}
        for r in rows
    ]


def _pull_screener(screener_db: Path) -> list[dict]:
    """Read Screener's scraped stock list.  Schema differs — try several shapes."""
    if not screener_db.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{screener_db}?mode=ro", uri=True)
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
    except sqlite3.Error:
        return []

    rows: list[dict] = []
    try:
        # Common Screener table shape: stocks(stock_name, url, market_cap, ...)
        if "stocks" in tables:
            cur = conn.execute("SELECT stock_name FROM stocks WHERE stock_name IS NOT NULL")
            for (name,) in cur.fetchall():
                slug = str(name).strip()
                if not slug:
                    continue
                pretty = slug.replace("_", " ")
                rows.append({"slug": slug, "pretty": pretty})
        elif "company_info" in tables:
            cur = conn.execute("SELECT stock_name FROM company_info WHERE stock_name IS NOT NULL")
            for (name,) in cur.fetchall():
                slug = str(name).strip()
                rows.append({"slug": slug, "pretty": slug.replace("_", " ")})
    except sqlite3.Error:
        pass
    finally:
        conn.close()
    return rows


def _alias_variants(*names: str) -> set[str]:
    """Emit a small set of variant strings for alias insertion.

    For a name 'Tata Motors Ltd', produce {'Tata Motors Ltd', 'Tata Motors',
    'Tata_Motors'} so users can find the stock by any of those typings.
    """
    out: set[str] = set()
    for n in names:
        if not n:
            continue
        s = str(n).strip()
        if not s:
            continue
        out.add(s)
        out.add(s.replace("_", " "))
        # Stripped-suffix version (lighter-touch than full normalize)
        tokens = [t for t in s.lower().split() if t not in {"ltd", "limited", "ltd.", "pvt", "private"}]
        if tokens:
            out.add(" ".join(tokens).title())
    return {x for x in out if x}


def build_mapping(screener_db: Path | None = None, verbose: bool = False) -> dict:
    """Rebuild stock_master + stock_alias from the EOD tables (and optionally Screener).

    Returns stats dict.
    """
    init_db()

    with connect() as conn:
        nse_rows = _pull_nse(conn)
        bse_rows = _pull_bse(conn)
    screener_rows = _pull_screener(screener_db) if screener_db else []
    if verbose:
        print(f"[map] pulled NSE:{len(nse_rows)}  BSE:{len(bse_rows)}  "
              f"Screener:{len(screener_rows)}")

    # Group rows by ISIN where possible; otherwise by NSE symbol or BSE scrip.
    # Every group becomes one stock_master row.
    groups: dict[str, dict] = {}  # key = isin or synthetic key

    def _key(row: dict, fallback: str) -> str:
        return row.get("isin") or f"{fallback}:{row[fallback]}"

    # NSE first — NSE symbols are typically the primary identifier.
    for r in nse_rows:
        k = _key(r, "symbol")
        g = groups.setdefault(k, {
            "isin": r.get("isin"), "nse_symbol": None, "bse_scrip": None,
            "company_name": None, "screener_slug": None,
            "first_seen_date": None, "last_seen_date": None,
        })
        g["nse_symbol"] = r["symbol"]
        g["company_name"] = g["company_name"] or r.get("company_name")
        g["first_seen_date"] = _earliest(g["first_seen_date"], r.get("first_seen"))
        g["last_seen_date"] = _latest(g["last_seen_date"], r.get("last_seen"))

    # BSE — try to merge by ISIN into existing NSE group first.
    for r in bse_rows:
        k = _key(r, "scrip_code")
        g = groups.get(k)
        if g is None:
            g = groups.setdefault(k, {
                "isin": r.get("isin"), "nse_symbol": None, "bse_scrip": None,
                "company_name": None, "screener_slug": None,
                "first_seen_date": None, "last_seen_date": None,
            })
        g["bse_scrip"] = r["scrip_code"]
        if not g.get("company_name"):
            g["company_name"] = r.get("company_name")
        g["first_seen_date"] = _earliest(g["first_seen_date"], r.get("first_seen"))
        g["last_seen_date"] = _latest(g["last_seen_date"], r.get("last_seen"))
        g["_bse_ticker"] = r.get("bse_ticker")  # remembered for alias emit

    # Screener — match into existing groups by normalized company name.
    # Build a quick lookup from the groups we have so far.
    by_norm_name = {}
    for g in groups.values():
        n = normalize_name(g.get("company_name"))
        if n and n not in by_norm_name:
            by_norm_name[n] = g
        # Also index by normalized NSE symbol (so 'Tata_Consultancy' matches TCS)
        nn = normalize_name(g.get("nse_symbol"))
        if nn and nn not in by_norm_name:
            by_norm_name[nn] = g

    unmatched_screener = 0
    for r in screener_rows:
        slug = r["slug"]
        norm = normalize_name(r["pretty"])
        g = by_norm_name.get(norm)
        if g is None:
            unmatched_screener += 1
            continue
        if not g.get("screener_slug"):
            g["screener_slug"] = slug

    if verbose:
        print(f"[map] grouped into {len(groups)} stocks "
              f"(Screener unmatched: {unmatched_screener})")

    # Write.
    with connect() as conn:
        conn.execute("DELETE FROM stock_alias")
        conn.execute("DELETE FROM stock_master")
        master_sql = """INSERT INTO stock_master
            (isin, nse_symbol, bse_scrip, company_name, screener_slug,
             first_seen_date, last_seen_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)"""
        alias_sql = """INSERT OR IGNORE INTO stock_alias
            (alias, alias_norm, stock_id, source) VALUES (?, ?, ?, ?)"""

        total_masters = 0
        total_aliases = 0
        for g in groups.values():
            cur = conn.execute(master_sql, (
                g.get("isin") or None,
                g.get("nse_symbol"),
                g.get("bse_scrip"),
                g.get("company_name"),
                g.get("screener_slug"),
                g.get("first_seen_date"),
                g.get("last_seen_date"),
            ))
            sid = cur.lastrowid
            total_masters += 1

            # Emit aliases from every source available for this company.
            aliases: list[tuple[str, str]] = []   # (alias, source)
            if g.get("nse_symbol"):
                aliases.append((g["nse_symbol"], "nse"))
            if g.get("bse_scrip"):
                aliases.append((g["bse_scrip"], "bse"))
            if g.get("_bse_ticker"):
                aliases.append((g["_bse_ticker"], "bse_name"))
            if g.get("company_name"):
                for v in _alias_variants(g["company_name"]):
                    aliases.append((v, "company_name"))
            if g.get("screener_slug"):
                aliases.append((g["screener_slug"], "screener"))
                aliases.append((g["screener_slug"].replace("_", " "), "screener"))
            if g.get("isin"):
                aliases.append((g["isin"], "isin"))

            seen_norms = set()
            for alias, source in aliases:
                n = normalize_name(alias)
                if not n or n in seen_norms:
                    continue
                seen_norms.add(n)
                conn.execute(alias_sql, (alias, n, sid, source))
                total_aliases += 1

    print(f"[map] built stock_master: {total_masters} rows  "
          f"stock_alias: {total_aliases} aliases")
    return {"masters": total_masters, "aliases": total_aliases,
            "screener_unmatched": unmatched_screener}


def _earliest(a, b):
    if a is None: return b
    if b is None: return a
    return a if a <= b else b


def _latest(a, b):
    if a is None: return b
    if b is None: return a
    return a if a >= b else b


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--screener-db", type=Path, default=DEFAULT_SCREENER_DB)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--no-screener", action="store_true")
    args = ap.parse_args()

    screener_path = None if args.no_screener else args.screener_db
    if screener_path and not screener_path.exists():
        print(f"[map] Screener DB not found at {screener_path} — skipping Screener slugs")
        screener_path = None

    result = build_mapping(screener_db=screener_path, verbose=args.verbose)
    print(f"[map] done: {result}")
