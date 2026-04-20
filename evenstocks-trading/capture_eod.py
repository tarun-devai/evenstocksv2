"""
End-of-day capture.

Schedule this ONCE per trading day, some time after 3:30 PM IST (4:00 PM is
safe).  Flow:

  1. Download today's bhavcopies (NSE EQ, BSE EQ, NSE Index).
  2. Load the EOD rows into SQLite (eod_nse / eod_bse).
  3. Get the full stock list from today's bhavcopy.
  4. For every stock, pull today's 1-min intraday series (full 9:15 → 15:30)
     and upsert into intraday_nse / intraday_bse.

NSE's chart-databyindex endpoint keeps serving the full-day series after
market close, so one run at 4 PM captures everything for that day.

Usage:
    python capture_eod.py                 # capture everything for today
    python capture_eod.py --date 2026-04-20
    python capture_eod.py --nse-only
    python capture_eod.py --bse-only
    python capture_eod.py --skip-intraday # bhavcopy only
    python capture_eod.py --limit 20      # smoke test on first 20 stocks
    python capture_eod.py --delay 0.5     # slower, politer requests
"""

from __future__ import annotations

import argparse
import time
import traceback
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests

from stock_data import (
    _BSE_LIVE_HEADERS,
    _nse_session,
    bse_bhavcopy,
    bse_intraday,
    nse_bhavcopy,
    nse_index_bhavcopy,
    nse_intraday,
)
from storage import (
    connect,
    init_db,
    save_bse_eod_from_bhavcopy,
    save_intraday_bse,
    save_intraday_nse,
    save_nse_eod_from_bhavcopy,
    stats,
)

DATA_DIR = Path(__file__).parent / "data"
BHAV_DIR = DATA_DIR / "bhav"


# ─── bhavcopy → DB ─────────────────────────────────────────────

def ingest_bhavcopies(target: date, *, nse: bool = True, bse: bool = True) -> tuple[Path | None, Path | None]:
    """Download + persist today's bhavcopies to the SQLite EOD tables."""
    nse_path = bse_path = None
    if nse:
        print(f"[bhav] NSE EQ for {target}…")
        nse_path = nse_bhavcopy(target, BHAV_DIR / "nse_eq")
        if nse_path:
            n = save_nse_eod_from_bhavcopy(nse_path)
            print(f"[bhav] NSE EQ  → {n} rows in eod_nse")
        else:
            print(f"[bhav] NSE EQ bhavcopy not yet available for {target}")

        # Indices (stored as raw CSV cache; DB table not defined yet — skip DB for now)
        idx = nse_index_bhavcopy(target, BHAV_DIR / "nse_index")
        if idx:
            print(f"[bhav] NSE IND  saved → {idx.name}")

    if bse:
        print(f"[bhav] BSE EQ for {target}…")
        bse_path = bse_bhavcopy(target, BHAV_DIR / "bse_eq")
        if bse_path:
            n = save_bse_eod_from_bhavcopy(bse_path)
            print(f"[bhav] BSE EQ  → {n} rows in eod_bse")
        else:
            print(f"[bhav] BSE EQ bhavcopy not yet available for {target}")

    return nse_path, bse_path


# ─── intraday capture ─────────────────────────────────────────

def capture_nse_intraday(symbols: list[str], *, delay: float = 0.3) -> None:
    session = _nse_session()
    ok = fail = total_rows = 0
    t0 = time.time()
    with connect() as db:
        for i, symbol in enumerate(symbols, 1):
            try:
                rows = nse_intraday(symbol, session=session)
                total_rows += save_intraday_nse(symbol, rows, conn=db)
                ok += 1
            except Exception:
                fail += 1
            if i % 50 == 0 or i == len(symbols):
                db.commit()  # checkpoint progress
                el = time.time() - t0
                print(f"[NSE intraday] {i}/{len(symbols)}  ok={ok} fail={fail} rows+={total_rows} {el:.0f}s")
            time.sleep(delay)
    print(f"[NSE intraday] done — {ok} ok, {fail} fail, +{total_rows} rows")


def capture_bse_intraday(scrips: list[str], *, delay: float = 0.3) -> None:
    session = requests.Session()
    session.headers.update(_BSE_LIVE_HEADERS)
    ok = fail = total_rows = 0
    t0 = time.time()
    with connect() as db:
        for i, scrip in enumerate(scrips, 1):
            try:
                rows = bse_intraday(scrip, session=session)
                total_rows += save_intraday_bse(scrip, rows, conn=db)
                ok += 1
            except Exception:
                fail += 1
            if i % 100 == 0 or i == len(scrips):
                db.commit()
                el = time.time() - t0
                print(f"[BSE intraday] {i}/{len(scrips)}  ok={ok} fail={fail} rows+={total_rows} {el:.0f}s")
            time.sleep(delay)
    print(f"[BSE intraday] done — {ok} ok, {fail} fail, +{total_rows} rows")


# ─── stock list discovery ─────────────────────────────────────

def discover_nse_symbols(nse_bhav_path: Path) -> list[str]:
    df = pd.read_csv(nse_bhav_path)
    df = df[df["SctySrs"].isin(["EQ", "BE", "BZ"])]
    return sorted(df["TckrSymb"].dropna().astype(str).unique().tolist())


def discover_bse_scrips(bse_bhav_path: Path) -> list[str]:
    df = pd.read_csv(bse_bhav_path)
    col = "FinInstrmId" if "FinInstrmId" in df.columns else "SC_CODE"
    return sorted(df[col].dropna().astype(str).unique().tolist())


# ─── main ──────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nse-only", action="store_true")
    ap.add_argument("--bse-only", action="store_true")
    ap.add_argument("--skip-intraday", action="store_true")
    ap.add_argument("--skip-bhavcopy", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--date", type=str, default="")
    args = ap.parse_args()

    target = date.fromisoformat(args.date) if args.date else date.today()
    do_nse = not args.bse_only
    do_bse = not args.nse_only

    print(f"[eod] target = {target}   started = {datetime.now():%Y-%m-%d %H:%M:%S}")
    init_db()

    nse_path = bse_path = None
    if not args.skip_bhavcopy:
        try:
            nse_path, bse_path = ingest_bhavcopies(target, nse=do_nse, bse=do_bse)
        except Exception:
            print("[bhav] crashed:")
            traceback.print_exc()

    if args.skip_intraday:
        print(f"[eod] skipping intraday.  stats = {stats()}")
        return

    if do_nse:
        try:
            if nse_path is None:
                # Maybe already downloaded earlier — try to find it
                nse_path = BHAV_DIR / "nse_eq" / f"BhavCopy_NSE_CM_0_0_0_{target:%Y%m%d}_F_0000.csv"
                if not nse_path.exists():
                    print("[NSE intraday] no bhavcopy to list symbols from; skipping.")
                    nse_path = None
            if nse_path:
                syms = discover_nse_symbols(nse_path)
                if args.limit:
                    syms = syms[: args.limit]
                print(f"[NSE intraday] {len(syms)} symbols")
                capture_nse_intraday(syms, delay=args.delay)
        except Exception:
            print("[NSE intraday] crashed:")
            traceback.print_exc()

    if do_bse:
        try:
            if bse_path is None:
                bse_path = BHAV_DIR / "bse_eq" / f"BhavCopy_BSE_CM_0_0_0_{target:%Y%m%d}_F_0000.CSV"
                if not bse_path.exists():
                    print("[BSE intraday] no bhavcopy to list scrips from; skipping.")
                    bse_path = None
            if bse_path:
                scrips = discover_bse_scrips(bse_path)
                if args.limit:
                    scrips = scrips[: args.limit]
                print(f"[BSE intraday] {len(scrips)} scrips")
                capture_bse_intraday(scrips, delay=args.delay)
        except Exception:
            print("[BSE intraday] crashed:")
            traceback.print_exc()

    print(f"[eod] finished = {datetime.now():%Y-%m-%d %H:%M:%S}   stats = {stats()}")


if __name__ == "__main__":
    main()
