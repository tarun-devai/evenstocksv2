# evenstocks-trading

Market data pipeline for EvenStocks: NSE + BSE end-of-day history, 1-min intraday, and a read API for the website.

## Files

| File | Purpose |
|---|---|
| `stock_data.py` | Core HTTP client for NSE/BSE — live quotes, intraday, bhavcopy download. No DB writes. |
| `storage.py` | SQLite layer. Schema, upsert helpers. Uses WAL so website can read while captures write. |
| `backfill.py` | **One-time.** Walks a date range, downloads every day's bhavcopies, ingests into DB. |
| `capture_eod.py` | **Daily 4 PM.** Downloads today's bhavcopy + full intraday for every stock. |
| `capture_live.py` | **Market hours.** Polls intraday every N minutes while the market is open. |
| `query.py` | Read API for the website / chatbot — `find_stock()`, `resolve()`, `get_eod()`, `get_intraday()`. |
| `build_mapping.py` | **One-shot after backfill.** Builds `stock_master` + `stock_alias` so any user-typed name (NSE symbol, BSE scrip, Screener slug, company name) resolves to one canonical stock record. |
| `data/trading.db` | SQLite database (created on first run). |
| `data/bhav/` | Raw bhavcopy cache (can be pruned after ingest). |

## Setup

```bash
cd evenstocks-trading
pip install -r requirements.txt
python storage.py            # initialize the DB
```

## Step 1 — Backfill history (run ONCE)

```bash
python backfill.py --from 2024-07-01 --to 2026-04-20
```

This walks every weekday, downloads the NSE EQ + BSE EQ + NSE Index bhavcopies for that day, and ingests into `eod_nse` / `eod_bse`. Takes ~2-4 hours depending on network. Safe to interrupt and re-run — it's idempotent.

**Note**: The 2024+ bhavcopy format starts around **July 2024**. Dates before that will 404 silently. If you need earlier history, we'll need to add the old-format downloader.

By default raw CSVs are deleted after ingest. Pass `--keep-csvs` to keep them.

## Step 1b — Build the name-mapping tables (run after any backfill)

```bash
python build_mapping.py
```

Why: NSE symbols (`TATAMOTORS`), BSE scrip codes (`500570`), Screener slugs (`Tata_Motors`), and company names (`Tata Motors Ltd`) all refer to the same underlying stock but use different strings. This script:

1. Reads every distinct (ISIN, symbol, company_name) tuple from `eod_nse` and `eod_bse`.
2. Groups by ISIN — same ISIN on both exchanges → single `stock_master` row.
3. If `evenstocks_chatbot/data/stocks.db` exists, merges Screener slugs into the same rows by normalized-name match.
4. Emits multiple `stock_alias` entries per stock so users can search by any form:
   - NSE symbol, BSE scrip, company name (multiple variants), ISIN, Screener slug.

Re-run it after every backfill — it's idempotent (drops and rebuilds the tables).

Check it worked:
```bash
python -c "from storage import connect; c=connect().__enter__(); print('masters:', c.execute('SELECT COUNT(*) FROM stock_master').fetchone()[0], 'aliases:', c.execute('SELECT COUNT(*) FROM stock_alias').fetchone()[0])"
python query.py find "tata motors"    # should now find TATAMOTORS + 500570
python query.py find "tcs"            # TATA CONSULTANCY SERVICES
python query.py find "500325"         # Reliance via BSE scrip code
```

## Step 2 — Daily 4 PM capture (scheduled)

Runs once each trading day, after market close.

```bash
python capture_eod.py
```

What it does:
1. Downloads today's NSE + BSE bhavcopy, ingests EOD rows.
2. Reads today's symbol list from the bhavcopy.
3. For every NSE symbol + every BSE scrip, pulls today's 1-min intraday and upserts into `intraday_nse` / `intraday_bse`.

Runtime: ~30–40 minutes (NSE ~10 min, BSE ~20 min at default 0.3s delay).

**Smoke test first:**
```bash
python capture_eod.py --limit 10       # first 10 stocks only
```

**Schedule on Windows** (elevated Command Prompt):
```cmd
schtasks /create /tn "EvenStocks EOD Capture" ^
  /tr "cmd /c cd /d c:\tarun\research\evenstocksv2\evenstocks-trading && python capture_eod.py >> capture_eod.log 2>&1" ^
  /sc weekly /d MON,TUE,WED,THU,FRI /st 16:00 /ru "%USERNAME%"
```

## Step 3 — Market-hours live poller (scheduled, optional)

Runs during 9:15 → 15:30. Polls every 15 minutes (configurable). Useful for near-real-time charts on the website.

```bash
python capture_live.py                 # every 15 min
python capture_live.py --interval 5    # every 5 min
python capture_live.py --nse-only --limit 50  # focused testing
```

The poller:
- Waits until 9:15 if started earlier.
- Polls in a loop.
- Exits cleanly at 15:30.

Because NSE's endpoint returns the full cumulative day on every call, later polls *enrich* the DB with more rows; there's no penalty to having both the 4 PM and the live poller running — data upserts dedupe by `(symbol, timestamp)`.

**Schedule on Windows:**
```cmd
schtasks /create /tn "EvenStocks Live Poller" ^
  /tr "cmd /c cd /d c:\tarun\research\evenstocksv2\evenstocks-trading && python capture_live.py >> capture_live.log 2>&1" ^
  /sc weekly /d MON,TUE,WED,THU,FRI /st 09:15 /ru "%USERNAME%"
```

## Reading from the DB (for the website)

```python
from evenstocks_trading.query import find_stock, get_eod, get_intraday
from datetime import date

# Resolve a user-typed name to a stock record
hits = find_stock("tata motors")
# → [{"nse_symbol": "TATAMOTORS", "bse_scrip": "500570", "name": "Tata Motors Ltd", ...}]

# Last 90 days of daily OHLCV
eod = get_eod(nse_symbol="TATAMOTORS", days=90)

# Today's minute-ticks (for a live chart)
intra = get_intraday(nse_symbol="TATAMOTORS", d=date.today())
```

Or from the command line for a quick peek:
```bash
python query.py find "tata motors"
python query.py eod --nse TATAMOTORS --days 30
python query.py intraday --nse TATAMOTORS
```

## Database schema

```sql
eod_nse(symbol, date, open, high, low, close, ltp, prev_close,
        volume, value, series, isin, company_name)
eod_bse(scrip_code, date, open, high, low, close, ltp, prev_close,
        volume, value, symbol, isin, company_name, series)
intraday_nse(symbol, timestamp, price)
intraday_bse(scrip_code, timestamp, price)
```

All tables use composite PKs that double as natural dedup keys. WAL mode is on — readers never block writers.

## Operational notes

- **Rate limits**: Default 0.3s between requests. NSE and BSE tolerate this fine. If you get 429s, raise `--delay` to 0.5.
- **Missing days**: Holidays and weekends just 404 — no error handling needed. Check `stats()` after a run.
- **Disk usage**: ~50 MB/month of EOD, ~300 MB/month of full-market intraday. Plan accordingly.
- **Backup**: `cp data/trading.db data/trading.db.bak` before destructive ops.
- **Reset**: `rm data/trading.db*` (the `-wal` and `-shm` files too) and re-run `python storage.py`.
