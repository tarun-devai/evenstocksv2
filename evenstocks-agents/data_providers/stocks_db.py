"""SQLite reader for Screener-scraped stock data. Mirrors chatbot's stock_db pattern."""

import json
import os
import sqlite3
from typing import Optional

DB_PATH = os.getenv("STOCKS_DB_PATH", "/app/data/stocks.db")


def get_conn() -> Optional[sqlite3.Connection]:
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().replace(" ", "_").replace(".", "").upper()


def get_company_info(ticker: str) -> Optional[dict]:
    conn = get_conn()
    if conn is None:
        return None
    try:
        normalized = normalize_ticker(ticker)
        row = conn.execute(
            "SELECT * FROM company_info WHERE UPPER(stock_name) = ? LIMIT 1",
            (normalized,),
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM company_info WHERE UPPER(stock_name) LIKE ? LIMIT 1",
                (f"%{normalized}%",),
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        for k in ("pros", "cons"):
            if d.get(k):
                try:
                    d[k] = json.loads(d[k])
                except Exception:
                    pass
        return d
    finally:
        conn.close()


def get_financial_tables(ticker: str) -> dict:
    conn = get_conn()
    if conn is None:
        return {}
    try:
        normalized = normalize_ticker(ticker)
        rows = conn.execute(
            "SELECT table_type, data FROM financial_tables WHERE UPPER(stock_name) = ?",
            (normalized,),
        ).fetchall()
        tables = {}
        for r in rows:
            try:
                tables[r["table_type"]] = json.loads(r["data"])
            except Exception:
                tables[r["table_type"]] = []
        return tables
    finally:
        conn.close()


def get_full_snapshot(ticker: str) -> Optional[dict]:
    info = get_company_info(ticker)
    if not info:
        return None
    return {
        "company_info": info,
        "financial_tables": get_financial_tables(info.get("stock_name", ticker)),
    }
