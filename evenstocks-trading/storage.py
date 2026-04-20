"""
SQLite storage for NSE/BSE EOD + intraday data.

Single file: ``data/trading.db``.  WAL mode so readers (the website) can query
the DB while capture scripts are writing.

Tables:
    eod_nse(symbol, date, open, high, low, close, volume, value, series, isin, company_name)
    eod_bse(scrip_code, date, open, high, low, close, volume, value, symbol, isin, company_name)
    intraday_nse(symbol, timestamp, price)
    intraday_bse(scrip_code, timestamp, price)

All inserts use ``INSERT OR REPLACE`` so re-runs are idempotent.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

# pandas is only needed for ingesting bhavcopy CSVs.  The read path used by
# query.py / the website only needs sqlite3, so we import lazily.
try:
    import pandas as pd
except ImportError:
    pd = None

DB_PATH = Path(__file__).parent / "data" / "trading.db"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS eod_nse (
    symbol       TEXT NOT NULL,
    date         TEXT NOT NULL,
    open         REAL,
    high         REAL,
    low          REAL,
    close        REAL,
    ltp          REAL,
    prev_close   REAL,
    volume       INTEGER,
    value        REAL,
    series       TEXT,
    isin         TEXT,
    company_name TEXT,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS eod_bse (
    scrip_code   TEXT NOT NULL,
    date         TEXT NOT NULL,
    open         REAL,
    high         REAL,
    low          REAL,
    close        REAL,
    ltp          REAL,
    prev_close   REAL,
    volume       INTEGER,
    value        REAL,
    symbol       TEXT,
    isin         TEXT,
    company_name TEXT,
    series       TEXT,
    PRIMARY KEY (scrip_code, date)
);

CREATE TABLE IF NOT EXISTS intraday_nse (
    symbol       TEXT NOT NULL,
    timestamp    TEXT NOT NULL,
    price        REAL,
    PRIMARY KEY (symbol, timestamp)
);

CREATE TABLE IF NOT EXISTS intraday_bse (
    scrip_code   TEXT NOT NULL,
    timestamp    TEXT NOT NULL,
    price        REAL,
    PRIMARY KEY (scrip_code, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_eod_nse_date        ON eod_nse(date);
CREATE INDEX IF NOT EXISTS idx_eod_bse_date        ON eod_bse(date);
CREATE INDEX IF NOT EXISTS idx_intraday_nse_sym_ts ON intraday_nse(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_intraday_bse_sc_ts  ON intraday_bse(scrip_code, timestamp);
CREATE INDEX IF NOT EXISTS idx_eod_nse_isin        ON eod_nse(isin);
CREATE INDEX IF NOT EXISTS idx_eod_bse_isin        ON eod_bse(isin);

-- ═══════════════════════════════════════════════════════════════
--  MAPPING tables — one canonical row per company, many aliases
-- ═══════════════════════════════════════════════════════════════

-- One row per unique company.  isin is the primary cross-exchange key
-- (NSE and BSE use the same ISIN for the same underlying security).
CREATE TABLE IF NOT EXISTS stock_master (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    isin             TEXT UNIQUE,
    nse_symbol       TEXT,
    bse_scrip        TEXT,
    company_name     TEXT,
    screener_slug    TEXT,
    industry         TEXT,
    first_seen_date  TEXT,
    last_seen_date   TEXT,
    is_active        INTEGER DEFAULT 1
);

-- Aliases: any string a user might type to refer to this stock.
-- One stock has many aliases: NSE symbol, BSE scrip, official name, common
-- short-forms, Screener slug, variant spellings.  ``alias_norm`` is the
-- aggressively-normalised form we match against.
CREATE TABLE IF NOT EXISTS stock_alias (
    alias            TEXT NOT NULL,
    alias_norm       TEXT NOT NULL,
    stock_id         INTEGER NOT NULL,
    source           TEXT,
    PRIMARY KEY (alias_norm, stock_id),
    FOREIGN KEY (stock_id) REFERENCES stock_master(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_master_nse        ON stock_master(nse_symbol);
CREATE INDEX IF NOT EXISTS idx_master_bse        ON stock_master(bse_scrip);
CREATE INDEX IF NOT EXISTS idx_master_screener   ON stock_master(screener_slug);
CREATE INDEX IF NOT EXISTS idx_master_company    ON stock_master(company_name);
CREATE INDEX IF NOT EXISTS idx_alias_norm        ON stock_alias(alias_norm);
CREATE INDEX IF NOT EXISTS idx_alias_stock       ON stock_alias(stock_id);
"""


@contextmanager
def connect(db_path: Path | str = DB_PATH):
    """Connection context manager with WAL mode and FK on."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Create tables + indexes if they don't exist.  Idempotent."""
    with connect(db_path) as conn:
        conn.executescript(_SCHEMA)


# ═══════════════════════════════════════════════════════════════
#  INTRADAY save
# ═══════════════════════════════════════════════════════════════

def save_intraday_nse(
    symbol: str,
    rows: Iterable[dict],
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Upsert rows of ``{timestamp, price}`` for one NSE symbol.  Returns count."""
    data = [(symbol.upper(), r["timestamp"], r["price"]) for r in rows if r.get("price") is not None]
    if not data:
        return 0
    sql = "INSERT OR REPLACE INTO intraday_nse(symbol, timestamp, price) VALUES (?, ?, ?)"
    if conn is None:
        with connect() as c:
            c.executemany(sql, data)
    else:
        conn.executemany(sql, data)
    return len(data)


def save_intraday_bse(
    scrip_code: str,
    rows: Iterable[dict],
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    data = [(str(scrip_code), r["timestamp"], r["price"]) for r in rows if r.get("price") is not None]
    if not data:
        return 0
    sql = "INSERT OR REPLACE INTO intraday_bse(scrip_code, timestamp, price) VALUES (?, ?, ?)"
    if conn is None:
        with connect() as c:
            c.executemany(sql, data)
    else:
        conn.executemany(sql, data)
    return len(data)


# ═══════════════════════════════════════════════════════════════
#  EOD save — from bhavcopy CSV paths
# ═══════════════════════════════════════════════════════════════

def save_nse_eod_from_bhavcopy(csv_path: Path | str) -> int:
    """Read an NSE EQ bhavcopy CSV and upsert its rows into ``eod_nse``.

    Uses the 2024+ bhavcopy schema (BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv).
    Returns rows inserted/updated.
    """
    if pd is None:
        raise ImportError("pandas is required for bhavcopy ingest: pip install pandas")
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    # 2024+ schema columns:
    #   TradDt, TckrSymb, SctySrs, OpnPric, HghPric, LwPric, ClsPric, LastPric,
    #   PrvsClsgPric, TtlTradgVol, TtlTrfVal, ISIN, FinInstrmNm
    df = df[df["SctySrs"].isin(["EQ", "BE", "BZ"])].copy()
    df["date"] = pd.to_datetime(df["TradDt"]).dt.strftime("%Y-%m-%d")

    rows = []
    for _, r in df.iterrows():
        rows.append((
            str(r.get("TckrSymb", "")).strip(),
            r["date"],
            _num(r.get("OpnPric")),
            _num(r.get("HghPric")),
            _num(r.get("LwPric")),
            _num(r.get("ClsPric")),
            _num(r.get("LastPric")),
            _num(r.get("PrvsClsgPric")),
            _int(r.get("TtlTradgVol")),
            _num(r.get("TtlTrfVal")),
            str(r.get("SctySrs", "")).strip() or None,
            str(r.get("ISIN", "")).strip() or None,
            str(r.get("FinInstrmNm", "")).strip() or None,
        ))
    sql = """INSERT OR REPLACE INTO eod_nse
        (symbol, date, open, high, low, close, ltp, prev_close, volume, value,
         series, isin, company_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    with connect() as c:
        c.executemany(sql, rows)
    return len(rows)


def save_bse_eod_from_bhavcopy(csv_path: Path | str) -> int:
    """Read a BSE EQ bhavcopy CSV and upsert into ``eod_bse``."""
    if pd is None:
        raise ImportError("pandas is required for bhavcopy ingest: pip install pandas")
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    # BSE 2024+ schema uses the same column names as NSE (Trad_Dt, TckrSymb, OpnPric, ...)
    # plus FinInstrmId (the numeric scrip code).
    df["date"] = pd.to_datetime(df["TradDt"]).dt.strftime("%Y-%m-%d")
    # Filter out F&O / index rows; equity series only.
    if "SctySrs" in df.columns:
        valid_series = {"A", "B", "M", "MS", "MT", "P", "R", "T", "W", "X", "XT", "Z", "ZP", "EQ"}
        df = df[df["SctySrs"].isin(valid_series)].copy()
    else:
        df = df.copy()

    rows = []
    for _, r in df.iterrows():
        scrip = str(r.get("FinInstrmId") or r.get("SC_CODE") or "").strip()
        if not scrip:
            continue
        rows.append((
            scrip,
            r["date"],
            _num(r.get("OpnPric")),
            _num(r.get("HghPric")),
            _num(r.get("LwPric")),
            _num(r.get("ClsPric")),
            _num(r.get("LastPric")),
            _num(r.get("PrvsClsgPric")),
            _int(r.get("TtlTradgVol")),
            _num(r.get("TtlTrfVal")),
            str(r.get("TckrSymb", "")).strip() or None,
            str(r.get("ISIN", "")).strip() or None,
            str(r.get("FinInstrmNm", "")).strip() or None,
            str(r.get("SctySrs", "")).strip() or None,
        ))
    sql = """INSERT OR REPLACE INTO eod_bse
        (scrip_code, date, open, high, low, close, ltp, prev_close, volume, value,
         symbol, isin, company_name, series)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    with connect() as c:
        c.executemany(sql, rows)
    return len(rows)


# ═══════════════════════════════════════════════════════════════
#  EOD save — OLD bhavcopy formats (pre-2024-07-08)
# ═══════════════════════════════════════════════════════════════

def save_nse_eod_from_bhavcopy_old(csv_path: Path | str) -> int:
    """Ingest an OLD-format NSE EQ bhavcopy CSV.

    Columns: SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE,
             TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN
    """
    if pd is None:
        raise ImportError("pandas is required for bhavcopy ingest: pip install pandas")
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]  # NSE sometimes has trailing spaces
    df = df[df["SERIES"].isin(["EQ", "BE", "BZ"])].copy()
    # TIMESTAMP is like "02-MAY-2023"
    df["date"] = pd.to_datetime(df["TIMESTAMP"]).dt.strftime("%Y-%m-%d")

    rows = []
    for _, r in df.iterrows():
        rows.append((
            str(r.get("SYMBOL", "")).strip(),
            r["date"],
            _num(r.get("OPEN")),
            _num(r.get("HIGH")),
            _num(r.get("LOW")),
            _num(r.get("CLOSE")),
            _num(r.get("LAST")),
            _num(r.get("PREVCLOSE")),
            _int(r.get("TOTTRDQTY")),
            _num(r.get("TOTTRDVAL")),
            str(r.get("SERIES", "")).strip() or None,
            str(r.get("ISIN", "")).strip() or None,
            None,  # old format has no company name column
        ))
    sql = """INSERT OR REPLACE INTO eod_nse
        (symbol, date, open, high, low, close, ltp, prev_close, volume, value,
         series, isin, company_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    with connect() as c:
        c.executemany(sql, rows)
    return len(rows)


def save_bse_eod_from_bhavcopy_old(csv_path: Path | str, trade_date) -> int:
    """Ingest an OLD-format BSE EQ bhavcopy CSV.

    Columns (typical): SC_CODE, SC_NAME, SC_GROUP, SC_TYPE, OPEN, HIGH, LOW,
                       CLOSE, LAST, PREVCLOSE, NO_TRADES, NO_OF_SHRS, NET_TURNOV,
                       TDCLOINDI, ISIN_CODE, TRADING_DATE (sometimes absent)

    ``trade_date`` is a ``datetime.date`` — used when the CSV has no date column.
    """
    if pd is None:
        raise ImportError("pandas is required for bhavcopy ingest: pip install pandas")
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    # Date — prefer the column if it exists, else use the file's trade_date.
    if "TRADING_DATE" in df.columns:
        df["date"] = pd.to_datetime(df["TRADING_DATE"], errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        df["date"] = trade_date.strftime("%Y-%m-%d")

    # Keep equity groups only; filter out bonds/odd lot/etc.
    valid_groups = {"A", "B", "T", "M", "MS", "MT", "P", "R", "W", "X", "XT", "Z", "ZP"}
    if "SC_GROUP" in df.columns:
        df = df[df["SC_GROUP"].astype(str).str.strip().isin(valid_groups)].copy()

    rows = []
    for _, r in df.iterrows():
        scrip = str(r.get("SC_CODE", "")).strip()
        if not scrip:
            continue
        rows.append((
            scrip,
            r["date"],
            _num(r.get("OPEN")),
            _num(r.get("HIGH")),
            _num(r.get("LOW")),
            _num(r.get("CLOSE")),
            _num(r.get("LAST")),
            _num(r.get("PREVCLOSE")),
            _int(r.get("NO_OF_SHRS")),
            _num(r.get("NET_TURNOV")),
            None,  # no ticker in old BSE format
            str(r.get("ISIN_CODE", "")).strip() or None,
            str(r.get("SC_NAME", "")).strip() or None,
            str(r.get("SC_GROUP", "")).strip() or None,
        ))
    sql = """INSERT OR REPLACE INTO eod_bse
        (scrip_code, date, open, high, low, close, ltp, prev_close, volume, value,
         symbol, isin, company_name, series)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    with connect() as c:
        c.executemany(sql, rows)
    return len(rows)


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════

def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return f if f == f else None  # NaN check
    except (TypeError, ValueError):
        return None


def _int(v: Any) -> Optional[int]:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


# ─── Name normalization for alias matching ─────────────────────
import re as _re

_NAME_STOPWORDS = [
    "limited", "ltd", "ltd.", "pvt", "private",
    "corp", "corporation", "corp.", "inc", "inc.", "plc",
    "company", "co", "co.", "& co", "and co",
    "india", "of india",
]


def normalize_name(name: Any) -> str:
    """Aggressively normalise a company name / symbol / slug for lookup matching.

        'Tata Motors Ltd'         → 'tatamotors'
        'HDFC Bank Limited'       → 'hdfcbank'
        'Tata_Motors'             → 'tatamotors'
        '500325' (BSE scrip)      → '500325'
        'Reliance Industries Ltd' → 'relianceindustries'
        'TCS'                     → 'tcs'

    The output is stripped of whitespace, punctuation, and common legal-form
    suffixes, then lower-cased.  Two inputs that refer to the same company
    should collapse to the same normalized string the vast majority of the time.
    """
    if name is None:
        return ""
    s = str(name).lower().strip()
    s = s.replace("_", " ").replace(".", " ").replace("&", " ")
    # Drop stopword suffixes (longest first to avoid partial overlaps).
    for w in sorted(_NAME_STOPWORDS, key=len, reverse=True):
        s = _re.sub(rf"\b{_re.escape(w)}\b", " ", s)
    # Strip everything that isn't alphanum.
    s = _re.sub(r"[^a-z0-9]", "", s)
    return s


def stats() -> dict:
    """Quick row counts — useful to verify captures ran."""
    out = {}
    with connect() as c:
        for table in ("eod_nse", "eod_bse", "intraday_nse", "intraday_bse"):
            cur = c.execute(f"SELECT COUNT(*) FROM {table}")
            out[table] = cur.fetchone()[0]
    return out


if __name__ == "__main__":
    init_db()
    print(f"[storage] initialized {DB_PATH}")
    print(f"[storage] row counts: {stats()}")
