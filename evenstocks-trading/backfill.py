"""
One-time historical backfill — walks a date range, downloads every day's
bhavcopy (NSE EQ, BSE EQ, NSE Index), and stores the EOD rows into SQLite.

Does NOT do intraday — NSE/BSE don't expose historical 1-min publicly, so
intraday is only built going forward by ``capture_eod.py`` / ``capture_live.py``.

Usage:
    python backfill.py --from 2024-07-01 --to 2026-04-20
    python backfill.py --from 2024-07-01 --to 2026-04-20 --keep-csvs
    python backfill.py --from 2024-07-01 --to 2026-04-20 --nse-only

Notes:
  - The 2024+ bhavcopy format (``BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip``)
    starts around July 2024.  Earlier dates will 404 silently.
  - Holidays and weekends are auto-skipped.
  - Safe to interrupt and re-run — ``INSERT OR REPLACE`` means re-ingest is free.
"""

from __future__ import annotations

import argparse
import time
import traceback
from datetime import date
from pathlib import Path

from stock_data import (
    bse_bhavcopy,
    bse_bhavcopy_old,
    nse_bhavcopy,
    nse_bhavcopy_old,
    nse_index_bhavcopy,
    trading_dates,
)
from storage import (
    init_db,
    save_bse_eod_from_bhavcopy,
    save_bse_eod_from_bhavcopy_old,
    save_nse_eod_from_bhavcopy,
    save_nse_eod_from_bhavcopy_old,
    stats,
)

DATA_DIR = Path(__file__).parent / "data"
BHAV_DIR = DATA_DIR / "bhav"

# Both NSE and BSE moved to their current "BhavCopy_*_CM_0_0_0_..." format on
# roughly this date.  Before this, URLs and column schemas are different.
FORMAT_CUTOFF = date(2024, 7, 8)


def _process_day(
    d: date,
    *,
    do_nse: bool,
    do_bse: bool,
    do_index: bool,
    keep_csvs: bool,
) -> dict:
    result = {"date": d, "nse_rows": 0, "bse_rows": 0, "idx": False}
    use_new = d >= FORMAT_CUTOFF

    if do_nse:
        if use_new:
            p = nse_bhavcopy(d, BHAV_DIR / "nse_eq")
            save_fn = save_nse_eod_from_bhavcopy
            save_args = ()
        else:
            p = nse_bhavcopy_old(d, BHAV_DIR / "nse_eq_old")
            save_fn = save_nse_eod_from_bhavcopy_old
            save_args = ()
        if p:
            try:
                result["nse_rows"] = save_fn(p, *save_args)
            except Exception as e:
                print(f"[{d}] NSE save failed: {e}")
            if not keep_csvs:
                try:
                    p.unlink()
                except OSError:
                    pass

    if do_index:
        p = nse_index_bhavcopy(d, BHAV_DIR / "nse_index")
        result["idx"] = bool(p)

    if do_bse:
        if use_new:
            p = bse_bhavcopy(d, BHAV_DIR / "bse_eq")
            save_fn = save_bse_eod_from_bhavcopy
            save_args = ()
        else:
            p = bse_bhavcopy_old(d, BHAV_DIR / "bse_eq_old")
            save_fn = save_bse_eod_from_bhavcopy_old
            save_args = (d,)  # old format may lack date column; pass explicitly
        if p:
            try:
                result["bse_rows"] = save_fn(p, *save_args)
            except Exception as e:
                print(f"[{d}] BSE save failed: {e}")
            if not keep_csvs:
                try:
                    p.unlink()
                except OSError:
                    pass

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--nse-only", action="store_true")
    ap.add_argument("--bse-only", action="store_true")
    ap.add_argument("--skip-index", action="store_true", help="don't download NSE index files")
    ap.add_argument("--keep-csvs", action="store_true",
                    help="keep raw bhavcopy CSVs on disk after ingest (default: delete)")
    ap.add_argument("--pause", type=float, default=0.4,
                    help="seconds between days (polite on exchanges)")
    args = ap.parse_args()

    frm = date.fromisoformat(args.from_date)
    to = date.fromisoformat(args.to_date)
    do_nse = not args.bse_only
    do_bse = not args.nse_only
    do_index = not args.skip_index and do_nse

    init_db()
    days = trading_dates(frm, to)
    old_days = sum(1 for d in days if d < FORMAT_CUTOFF)
    new_days = len(days) - old_days
    keep_csvs = args.keep_csvs
    print(f"[backfill] {len(days)} weekdays from {frm} to {to}")
    print(f"[backfill] NSE={do_nse}  BSE={do_bse}  IDX={do_index}  keep_csvs={keep_csvs}")
    print(f"[backfill] format split: {old_days} pre-{FORMAT_CUTOFF} (old URLs) + {new_days} from {FORMAT_CUTOFF} (new URLs)")

    total_nse = total_bse = idx_hits = nse_days = bse_days = 0
    t0 = time.time()

    for i, d in enumerate(days, 1):
        try:
            r = _process_day(
                d,
                do_nse=do_nse, do_bse=do_bse, do_index=do_index,
                keep_csvs=keep_csvs,
            )
            total_nse += r["nse_rows"]
            total_bse += r["bse_rows"]
            if r["nse_rows"]: nse_days += 1
            if r["bse_rows"]: bse_days += 1
            if r["idx"]: idx_hits += 1
        except Exception:
            print(f"[{d}] crashed:"); traceback.print_exc()

        if i % 10 == 0 or i == len(days):
            el = time.time() - t0
            print(
                f"[backfill] {i}/{len(days)}  NSE days:{nse_days} rows:{total_nse} | "
                f"BSE days:{bse_days} rows:{total_bse} | IDX:{idx_hits}  {el:.0f}s"
            )
        time.sleep(args.pause)

    print(f"\n[backfill] done.  stats = {stats()}")


if __name__ == "__main__":
    main()
