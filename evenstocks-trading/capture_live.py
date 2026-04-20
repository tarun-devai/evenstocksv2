"""
Live intraday capture — runs during market hours.

Polls today's intraday series every N minutes (default 15) for every stock
and upserts into the SQLite intraday tables.  Since NSE's chart-databyindex
endpoint always returns the full cumulative day, later polls overwrite
earlier ones with strictly more data — your DB ends up with the complete day
by 3:30 PM, and partial days if the process is interrupted.

Start it any time after 9:15 AM IST.  It will:
  - wait until 9:15 if started earlier,
  - poll until 15:30,
  - then exit cleanly.

Usage:
    python capture_live.py                    # every 15 min, NSE + BSE
    python capture_live.py --interval 5       # every 5 min (more aggressive)
    python capture_live.py --nse-only
    python capture_live.py --limit 100        # smoke test on top 100 only
    python capture_live.py --delay 0.3        # sleep between per-stock requests

Prereq:  today's bhavcopy must be downloadable OR a previous day's bhavcopy
present so we can get the stock list.  The script auto-discovers the most
recent bhavcopy in ``data/bhav/``.
"""

from __future__ import annotations

import argparse
import time
import traceback
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path

import pandas as pd
import requests

from stock_data import (
    _BSE_LIVE_HEADERS,
    _nse_session,
    bse_intraday,
    nse_intraday,
)
from storage import (
    connect,
    init_db,
    save_intraday_bse,
    save_intraday_nse,
    stats,
)

DATA_DIR = Path(__file__).parent / "data"
BHAV_DIR = DATA_DIR / "bhav"

MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)


# ─── time helpers ──────────────────────────────────────────────

def now() -> datetime:
    return datetime.now()


def market_is_open(ts: datetime | None = None) -> bool:
    ts = ts or now()
    if ts.weekday() >= 5:
        return False
    t = ts.time()
    return MARKET_OPEN <= t <= MARKET_CLOSE


def seconds_until(target_time: dtime) -> float:
    n = now()
    target = datetime.combine(n.date(), target_time)
    if target < n:
        return 0.0
    return (target - n).total_seconds()


# ─── stock list discovery ─────────────────────────────────────

def _latest_nse_bhavcopy() -> Path | None:
    candidates = sorted((BHAV_DIR / "nse_eq").glob("BhavCopy_NSE_CM_*.csv"))
    return candidates[-1] if candidates else None


def _latest_bse_bhavcopy() -> Path | None:
    candidates = sorted((BHAV_DIR / "bse_eq").glob("BhavCopy_BSE_CM_*.CSV"))
    return candidates[-1] if candidates else None


def discover_nse_symbols() -> list[str]:
    p = _latest_nse_bhavcopy()
    if not p:
        raise SystemExit(
            "No NSE bhavcopy under data/bhav/nse_eq. "
            "Run `python capture_eod.py --skip-intraday` first to populate it."
        )
    df = pd.read_csv(p)
    df = df[df["SctySrs"].isin(["EQ", "BE", "BZ"])]
    return sorted(df["TckrSymb"].dropna().astype(str).unique().tolist())


def discover_bse_scrips() -> list[str]:
    p = _latest_bse_bhavcopy()
    if not p:
        raise SystemExit(
            "No BSE bhavcopy under data/bhav/bse_eq. "
            "Run `python capture_eod.py --skip-intraday` first to populate it."
        )
    df = pd.read_csv(p)
    col = "FinInstrmId" if "FinInstrmId" in df.columns else "SC_CODE"
    return sorted(df[col].dropna().astype(str).unique().tolist())


# ─── poll loops ────────────────────────────────────────────────

def poll_nse(symbols: list[str], *, delay: float) -> tuple[int, int, int]:
    session = _nse_session()
    ok = fail = total_rows = 0
    with connect() as db:
        for i, symbol in enumerate(symbols, 1):
            try:
                rows = nse_intraday(symbol, session=session)
                total_rows += save_intraday_nse(symbol, rows, conn=db)
                ok += 1
            except Exception:
                fail += 1
            if i % 200 == 0:
                db.commit()
            time.sleep(delay)
    return ok, fail, total_rows


def poll_bse(scrips: list[str], *, delay: float) -> tuple[int, int, int]:
    session = requests.Session()
    session.headers.update(_BSE_LIVE_HEADERS)
    ok = fail = total_rows = 0
    with connect() as db:
        for i, scrip in enumerate(scrips, 1):
            try:
                rows = bse_intraday(scrip, session=session)
                total_rows += save_intraday_bse(scrip, rows, conn=db)
                ok += 1
            except Exception:
                fail += 1
            if i % 200 == 0:
                db.commit()
            time.sleep(delay)
    return ok, fail, total_rows


# ─── main orchestration ───────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=15, help="minutes between polls")
    ap.add_argument("--nse-only", action="store_true")
    ap.add_argument("--bse-only", action="store_true")
    ap.add_argument("--delay", type=float, default=0.3, help="seconds between per-stock requests")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ignore-hours", action="store_true",
                    help="poll even outside 9:15-15:30 (for testing)")
    args = ap.parse_args()

    init_db()

    # Weekend — no trading.
    if now().weekday() >= 5 and not args.ignore_hours:
        print(f"[live] weekend ({now():%A}) — market closed.  exiting.")
        return

    # Wait until 9:15 if started early.
    if not args.ignore_hours and now().time() < MARKET_OPEN:
        wait = seconds_until(MARKET_OPEN)
        print(f"[live] waiting {wait/60:.1f} min until market open at 9:15")
        time.sleep(wait)

    do_nse = not args.bse_only
    do_bse = not args.nse_only

    nse_syms = discover_nse_symbols() if do_nse else []
    bse_scrips = discover_bse_scrips() if do_bse else []
    if args.limit:
        nse_syms = nse_syms[: args.limit]
        bse_scrips = bse_scrips[: args.limit]

    print(f"[live] starting.  NSE={len(nse_syms)} BSE={len(bse_scrips)} interval={args.interval}min")

    poll_no = 0
    while True:
        if not args.ignore_hours and not market_is_open():
            print(f"[live] market closed ({now():%H:%M}).  exiting.")
            break

        poll_no += 1
        t0 = time.time()
        print(f"\n[live] ── poll #{poll_no}  {now():%Y-%m-%d %H:%M:%S} ──")

        if do_nse:
            try:
                ok, fail, rows = poll_nse(nse_syms, delay=args.delay)
                print(f"[live NSE] ok={ok} fail={fail} rows+={rows}")
            except Exception:
                print("[live NSE] crashed:"); traceback.print_exc()

        if do_bse:
            try:
                ok, fail, rows = poll_bse(bse_scrips, delay=args.delay)
                print(f"[live BSE] ok={ok} fail={fail} rows+={rows}")
            except Exception:
                print("[live BSE] crashed:"); traceback.print_exc()

        elapsed = time.time() - t0
        print(f"[live] poll #{poll_no} done in {elapsed/60:.1f} min.  db = {stats()}")

        # Sleep until next poll, but cap so we don't run past market close.
        sleep_s = max(0, args.interval * 60 - elapsed)
        if not args.ignore_hours:
            remaining = seconds_until(MARKET_CLOSE)
            if remaining <= 0:
                break
            sleep_s = min(sleep_s, remaining)
        print(f"[live] sleeping {sleep_s:.0f}s…")
        time.sleep(sleep_s)


if __name__ == "__main__":
    main()
