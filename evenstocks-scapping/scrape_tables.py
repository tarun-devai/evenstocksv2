"""
scrape_tables.py
────────────────────────────────────────────────────────────────
Script 1: Fetches each stock's screener.in page and extracts:
  - Company info (market cap, PE, ROCE, ROE, etc.)
  - Financial tables (quarters, P&L, balance sheet, cash flow,
    ratios, shareholding)

All data is stored in a single SQLite database: data/stocks.db
  - company_info table  → one row per stock, key metrics as columns
  - financial_tables    → one row per (stock, table_type), data as JSON

Usage:
  python scrape_tables.py
  python scrape_tables.py --start 0 --end 100

Requires: pip install requests beautifulsoup4
"""

import os
import re
import json
import csv
import time
import random
import sqlite3
import logging
import argparse
import traceback
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

# ═══════════════════════════════════════════════════════════════
INPUT_CSV       = "screener_stocks.csv"
DB_PATH         = os.path.join("data", "stocks.db")
LOGIN_URL       = "https://www.screener.in/login/"
LOGIN_EMAIL     = "taruntiwari.hp@gmail.com"
LOGIN_PASSWORD  = "Tiwari2000@20"

MIN_DELAY       = 1.5
MAX_DELAY       = 3.0
REQUEST_TIMEOUT = 30

# Auto-refresh policy: skip a stock only if its row is younger than this threshold.
# Rows older than STALE_AFTER_DAYS get re-scraped automatically.
# Overridable via --stale-days or --force on the CLI.
STALE_AFTER_DAYS = 2

TABLE_SECTIONS = [
    "quarters", "profit-loss", "balance-sheet",
    "cash-flow", "ratios", "shareholding",
]

LOG_FILE = "scrape_tables.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

WEB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.screener.in/",
}


# ═══════════════════════════════════════════════════════════════
# SQLite setup
# ═══════════════════════════════════════════════════════════════
def init_db(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_info (
            stock_name   TEXT PRIMARY KEY,
            url          TEXT,
            about        TEXT,
            market_cap   TEXT,
            current_price TEXT,
            high_low     TEXT,
            stock_pe     TEXT,
            book_value   TEXT,
            dividend_yield TEXT,
            roce         TEXT,
            roe          TEXT,
            face_value   TEXT,
            pros         TEXT,
            cons         TEXT,
            last_updated TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_tables (
            stock_name  TEXT,
            table_type  TEXT,
            data        TEXT,
            PRIMARY KEY (stock_name, table_type)
        )
    """)
    # Backfill: older DBs created before the freshness feature won't have last_updated.
    existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(company_info)").fetchall()}
    if "last_updated" not in existing_cols:
        conn.execute("ALTER TABLE company_info ADD COLUMN last_updated TEXT")
    conn.commit()
    return conn


def get_last_updated(conn: sqlite3.Connection, stock_name: str) -> datetime | None:
    """Return the last_updated datetime for a stock, or None if row is missing / unset."""
    row = conn.execute(
        "SELECT last_updated FROM company_info WHERE stock_name = ?", (stock_name,)
    ).fetchone()
    if not row or not row[0]:
        return None
    try:
        # Stored as ISO-8601 UTC
        return datetime.fromisoformat(row[0])
    except ValueError:
        return None


def is_fresh(conn: sqlite3.Connection, stock_name: str, stale_after_days: float) -> bool:
    """True if the stock row exists AND its last_updated is within stale_after_days."""
    ts = get_last_updated(conn, stock_name)
    if ts is None:
        return False
    # Treat naive timestamps as UTC (older rows may have been written naive)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - ts
    return age < timedelta(days=stale_after_days)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════
def clean_name(name: str) -> str:
    return name.strip().replace(" ", "_").replace(".", "")


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(WEB_HEADERS)
    try:
        resp = session.get(LOGIN_URL, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(resp.content, "html.parser")
        csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if csrf:
            resp = session.post(
                LOGIN_URL,
                data={
                    "username": LOGIN_EMAIL,
                    "password": LOGIN_PASSWORD,
                    "csrfmiddlewaretoken": csrf["value"],
                },
                headers={**WEB_HEADERS, "Referer": LOGIN_URL},
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 200 and "login" not in resp.url:
                log.info("Logged in successfully.")
            else:
                log.warning("Login may have failed.")
        else:
            log.warning("CSRF token not found.")
    except Exception as e:
        log.warning(f"Login error: {e}")
    return session


# ═══════════════════════════════════════════════════════════════
# Extraction
# ═══════════════════════════════════════════════════════════════
def extract_company_info(soup: BeautifulSoup) -> dict:
    info = {}
    about = soup.find("div", class_=lambda c: c and "about" in c)
    if about:
        info["about"] = about.get_text(" ", strip=True)

    metric_keys = [
        "market_cap", "current_price", "high_low", "stock_pe",
        "book_value", "dividend_yield", "roce", "roe", "face_value",
    ]
    spans = soup.find_all("span", class_="nowrap value")
    for i, key in enumerate(metric_keys):
        if i < len(spans):
            info[key] = "".join(spans[i].get_text().split())

    for cls in ("pros", "cons"):
        div = soup.find("div", class_=cls)
        if div:
            info[cls] = [li.get_text(strip=True) for li in div.find_all("li")]

    return info


def _parse_html_table(table_tag) -> list[dict] | None:
    if not table_tag:
        return None
    header_row = table_tag.find("tr")
    if not header_row:
        return None

    headers = [el.get_text(strip=True)
               for el in header_row.find_all(["th", "td"]) if el.get_text(strip=True)]
    if not headers:
        return None

    rows = []
    for tr in table_tag.find_all("tr")[1:]:
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        vals = [c.get_text(strip=True) for c in cells]
        if len(vals) == len(headers) + 1:
            headers = [""] + headers
        if len(vals) != len(headers):
            continue
        rows.append(dict(zip(headers, vals)))

    return rows if rows else None


def extract_tables(soup: BeautifulSoup) -> dict:
    tables = {}
    for section_id in TABLE_SECTIONS:
        if section_id == "shareholding":
            container = soup.find("div", {"id": "quarterly-shp"})
        else:
            container = soup.find("section", {"id": section_id})

        if not container:
            tables[section_id] = []
            continue

        section_tables = []
        for tbl in container.find_all("table"):
            parsed = _parse_html_table(tbl)
            if parsed:
                section_tables.append(parsed)

        tables[section_id] = section_tables[0] if len(section_tables) == 1 else section_tables
    return tables


# ═══════════════════════════════════════════════════════════════
# Save to SQLite
# ═══════════════════════════════════════════════════════════════
def save_to_db(conn: sqlite3.Connection, stock_name: str, url: str,
               info: dict, tables: dict):
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute("""
        INSERT OR REPLACE INTO company_info
        (stock_name, url, about, market_cap, current_price, high_low,
         stock_pe, book_value, dividend_yield, roce, roe, face_value,
         pros, cons, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        stock_name, url,
        info.get("about", ""),
        info.get("market_cap", ""),
        info.get("current_price", ""),
        info.get("high_low", ""),
        info.get("stock_pe", ""),
        info.get("book_value", ""),
        info.get("dividend_yield", ""),
        info.get("roce", ""),
        info.get("roe", ""),
        info.get("face_value", ""),
        json.dumps(info.get("pros", []), ensure_ascii=False),
        json.dumps(info.get("cons", []), ensure_ascii=False),
        now_iso,
    ))

    for table_type, data in tables.items():
        conn.execute("""
            INSERT OR REPLACE INTO financial_tables (stock_name, table_type, data)
            VALUES (?, ?, ?)
        """, (stock_name, table_type, json.dumps(data, ensure_ascii=False)))

    conn.commit()


# ═══════════════════════════════════════════════════════════════
# Per-company pipeline
# ═══════════════════════════════════════════════════════════════
def process_company(session: requests.Session, conn: sqlite3.Connection,
                    name: str, url: str, stale_after_days: float, force: bool) -> bool:
    stock_name = clean_name(name)

    if not force and is_fresh(conn, stock_name, stale_after_days):
        ts = get_last_updated(conn, stock_name)
        age_hrs = (datetime.now(timezone.utc) - (ts.replace(tzinfo=timezone.utc) if ts and ts.tzinfo is None else ts)).total_seconds() / 3600 if ts else 0
        log.info(f"  [skip] {stock_name} (updated {age_hrs:.1f}h ago)")
        return True

    log.info(f"  Processing: {stock_name}")
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            log.warning(f"  HTTP {resp.status_code} for {stock_name}")
            return False
        soup = BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        log.error(f"  Fetch failed for {stock_name}: {e}")
        return False

    info = extract_company_info(soup)
    tables = extract_tables(soup)
    save_to_db(conn, stock_name, url, info, tables)

    log.info(f"  Saved: {stock_name}")
    return True


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Scrape stock tables → SQLite")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument(
        "--stale-days", type=float, default=STALE_AFTER_DAYS,
        help=f"Re-scrape rows older than this many days (default: {STALE_AFTER_DAYS}). "
             "Fresh rows are skipped automatically.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Ignore freshness and re-scrape every stock.",
    )
    args = parser.parse_args()

    stocks = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stocks.append(row)

    end = min(args.end or len(stocks), len(stocks))
    start = max(0, args.start)

    log.info("=" * 60)
    mode = "force re-scrape" if args.force else f"skip if < {args.stale_days}d old"
    log.info(f"Table Scraper  |  {len(stocks)} total  |  [{start}:{end}]  |  {mode}")
    log.info("=" * 60)

    conn = init_db(DB_PATH)
    session = create_session()
    ok = fail = 0
    t0 = time.time()

    for i in range(start, end):
        name, url = stocks[i]["name"], stocks[i]["url"]
        try:
            if process_company(session, conn, name, url, args.stale_days, args.force):
                ok += 1
            else:
                fail += 1
        except Exception as e:
            log.error(f"  [{i}] {name}: {e}\n{traceback.format_exc()}")
            fail += 1

        if (i - start + 1) % 50 == 0:
            log.info(f"\n=== Progress: {i - start + 1}/{end - start} | OK: {ok} | Fail: {fail} ===\n")

    conn.close()
    elapsed = time.time() - t0
    log.info(f"\nDone in {elapsed:.0f}s  |  OK: {ok}  |  Failed: {fail}")
    log.info(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()
