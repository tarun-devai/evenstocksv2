"""
NSE + BSE market data — live quotes, intraday, and historical bhavcopies.

LIVE       nse_live(symbol), bse_live(scrip_code)
INTRADAY   nse_intraday(symbol), bse_intraday(scrip_code)      # today's 1-min LTP
BHAVCOPY   nse_bhavcopy(date), bse_bhavcopy(date), nse_index_bhavcopy(date),
           nse_sme_bhavcopy(date), download_history_range(from, to, dir)

Endpoints used:
  NSE quote      https://www.nseindia.com/api/quote-equity
  NSE intraday   https://www.nseindia.com/api/chart-databyindex?index={SYM}EQN
  BSE quote      https://api.bseindia.com/BseIndiaAPI/api/getScripHeaderData/w
  BSE intraday   https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w
  NSE EQ bhav    https://archives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{YYYYMMDD}_F_0000.csv.zip
  NSE IND        https://archives.nseindia.com/content/indices/ind_close_all_{DDMMYYYY}.csv
  NSE SME        https://archives.nseindia.com/archives/sme/bhavcopy/sme{DDMMYY}.csv
  BSE EQ bhav    https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_{YYYYMMDD}_F_0000.CSV
"""

from __future__ import annotations

import urllib3
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

try:
    import pandas as pd
except ImportError:
    pd = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


# ═══════════════════════════════════════════════════════════════
#  LIVE — NSE
# ═══════════════════════════════════════════════════════════════

_NSE_BASE = "https://www.nseindia.com"
_NSE_LIVE_HEADERS = {
    "User-Agent": _UA,
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{_NSE_BASE}/get-quotes/equity?symbol=RELIANCE",
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive",
}


def _nse_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_NSE_LIVE_HEADERS)
    s.get(f"{_NSE_BASE}/get-quotes/equity?symbol=RELIANCE", timeout=10)
    return s


def nse_live(symbol: str, *, raw: bool = False) -> Dict[str, Any]:
    """Live quote for an NSE equity symbol, e.g. 'RELIANCE', 'TCS'."""
    s = _nse_session()
    r = s.get(f"{_NSE_BASE}/api/quote-equity", params={"symbol": symbol.upper()}, timeout=10)
    r.raise_for_status()
    data = r.json()
    if raw:
        return data

    price = data.get("priceInfo", {}) or {}
    day = price.get("intraDayHighLow", {}) or {}
    yr = price.get("weekHighLow", {}) or {}
    return {
        "symbol": symbol.upper(),
        "last_price": price.get("lastPrice"),
        "change": price.get("change"),
        "pct_change": price.get("pChange"),
        "open": price.get("open"),
        "high": day.get("max"),
        "low": day.get("min"),
        "prev_close": price.get("previousClose"),
        "vwap": price.get("vwap"),
        "upper_circuit": price.get("upperCP"),
        "lower_circuit": price.get("lowerCP"),
        "week_52_high": yr.get("max"),
        "week_52_low": yr.get("min"),
        "last_update": (data.get("metadata") or {}).get("lastUpdateTime"),
    }


# ═══════════════════════════════════════════════════════════════
#  LIVE — BSE
# ═══════════════════════════════════════════════════════════════

_BSE_API = "https://api.bseindia.com/BseIndiaAPI/api"
_BSE_LIVE_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.bseindia.com",
    "Referer": "https://www.bseindia.com/",
    "Connection": "keep-alive",
}


def bse_live(scrip_code: str, *, raw: bool = False) -> Dict[str, Any]:
    """Live quote for a BSE equity scrip, e.g. '500325' (Reliance)."""
    s = requests.Session()
    s.headers.update(_BSE_LIVE_HEADERS)
    r = s.get(
        f"{_BSE_API}/getScripHeaderData/w",
        params={"Debtflag": "", "scripcode": str(scrip_code), "seriesid": ""},
        timeout=10, verify=False,
    )
    r.raise_for_status()
    data = r.json()
    if raw:
        return data

    header = data.get("Header", {}) or {}
    curr = data.get("CurrRate", {}) or {}
    ohlc = data.get("OHLC", {}) or {}
    day = data.get("Day_Data", {}) or {}
    return {
        "scrip_code": str(scrip_code),
        "name": header.get("CoName") or header.get("Scrip_Name"),
        "industry": header.get("IndustryName") or header.get("Industry"),
        "last_price": curr.get("LTP") or curr.get("CurrRate"),
        "change": curr.get("Chg"),
        "pct_change": curr.get("PcChg"),
        "open": ohlc.get("Open"),
        "high": ohlc.get("High"),
        "low": ohlc.get("Low"),
        "prev_close": ohlc.get("PrevClose"),
        "week_52_high": day.get("WeekHighPrice") or header.get("WkHi"),
        "week_52_low": day.get("WeekLowPrice") or header.get("WkLo"),
        "face_value": header.get("FaceValue"),
        "market_cap": header.get("MktCap"),
        "last_update": curr.get("UpdOn") or header.get("UpdOn"),
    }


# ═══════════════════════════════════════════════════════════════
#  INTRADAY — today's 1-min series
# ═══════════════════════════════════════════════════════════════

def nse_intraday(
    symbol: str,
    *,
    raw: bool = False,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Today's 1-min LTP series for an NSE symbol (full 9:15 → 15:30 session).

    Returns ``[{"timestamp": "YYYY-MM-DD HH:MM:SS", "price": float}, ...]``.
    Pass a ``session`` when calling in a loop to reuse cookies.
    """
    s = session or _nse_session()
    r = s.get(
        f"{_NSE_BASE}/api/chart-databyindex",
        params={"index": f"{symbol.upper()}EQN"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    if raw:
        return data
    points = data.get("grapthData") or []
    return [
        {"timestamp": datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S"),
         "price": price}
        for ts, price in points
    ]


def bse_intraday(
    scrip_code: str,
    *,
    raw: bool = False,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Today's intraday chart series for a BSE scrip code."""
    if session is None:
        session = requests.Session()
        session.headers.update(_BSE_LIVE_HEADERS)
    r = session.get(
        f"{_BSE_API}/StockReachGraph/w",
        params={"scripcode": str(scrip_code), "flag": "0"},
        timeout=15, verify=False,
    )
    r.raise_for_status()
    data = r.json()
    if raw:
        return data

    points = data.get("graphData") or data.get("Data") or data.get("Table") or []
    out: List[Dict[str, Any]] = []
    for p in points:
        if isinstance(p, list) and len(p) >= 2:
            ts, price = p[0], p[1]
            try:
                ts_fmt = datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                ts_fmt = str(ts)
            out.append({"timestamp": ts_fmt, "price": price})
        elif isinstance(p, dict):
            ts = p.get("dttm") or p.get("Date") or p.get("ticks") or p.get("x")
            price = p.get("ltp") or p.get("price") or p.get("Close") or p.get("y")
            out.append({"timestamp": str(ts), "price": price})
    return out


# ═══════════════════════════════════════════════════════════════
#  BHAVCOPY — shared helpers
# ═══════════════════════════════════════════════════════════════

def trading_dates(from_date: date, to_date: date) -> List[date]:
    """All weekdays (Mon-Fri) in [from_date, to_date], inclusive."""
    out: List[date] = []
    cur = from_date
    while cur <= to_date:
        if cur.weekday() < 5:
            out.append(cur)
        cur += timedelta(days=1)
    return out


def _download(url: str, dest: Path, *, verify: bool = True, timeout: int = 30) -> bool:
    """Stream a URL to disk.  Returns True on success, False on 404 / network fail."""
    headers = {"User-Agent": _UA, "Accept": "*/*"}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=timeout, verify=verify) as r:
            if r.status_code == 404:
                return False
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
        return True
    except requests.RequestException:
        return False


# ═══════════════════════════════════════════════════════════════
#  BHAVCOPY — NSE EQ / IND / SME
# ═══════════════════════════════════════════════════════════════

def nse_bhavcopy(d: date, out_dir: str | Path) -> Optional[Path]:
    """Download + extract NSE EQ bhavcopy (2024+ format) for one trading date.

    Returns CSV path or None.  Use ``nse_bhavcopy_old`` for dates before
    2024-07-08 where this format doesn't exist.
    """
    out_dir = Path(out_dir)
    date_str = d.strftime("%Y%m%d")
    zip_name = f"BhavCopy_NSE_CM_0_0_0_{date_str}_F_0000.csv.zip"
    url = f"https://archives.nseindia.com/content/cm/{zip_name}"
    zip_path = out_dir / zip_name
    if not _download(url, zip_path):
        return None
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(out_dir)
            csv_name = z.namelist()[0]
    finally:
        zip_path.unlink(missing_ok=True)
    return out_dir / csv_name


def nse_bhavcopy_old(d: date, out_dir: str | Path) -> Optional[Path]:
    """Download + extract OLD-format NSE EQ bhavcopy (pre-2024-07-08).

    URL: archives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MMM}/cm{DD}{MMM}{YYYY}bhav.csv.zip
    e.g. cm02MAY2023bhav.csv.zip
    """
    out_dir = Path(out_dir)
    mmm = d.strftime("%b").upper()  # "May" → "MAY"
    yyyy = d.strftime("%Y")
    dd = d.strftime("%d")
    zip_name = f"cm{dd}{mmm}{yyyy}bhav.csv.zip"
    url = f"https://archives.nseindia.com/content/historical/EQUITIES/{yyyy}/{mmm}/{zip_name}"
    zip_path = out_dir / zip_name
    if not _download(url, zip_path):
        return None
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(out_dir)
            csv_name = z.namelist()[0]
    finally:
        zip_path.unlink(missing_ok=True)
    return out_dir / csv_name


def nse_index_bhavcopy(d: date, out_dir: str | Path) -> Optional[Path]:
    """Download NSE daily-close indices file for one date."""
    out_dir = Path(out_dir)
    date_str = d.strftime("%d%m%Y")
    name = f"ind_close_all_{date_str}.csv"
    url = f"https://archives.nseindia.com/content/indices/{name}"
    path = out_dir / name
    return path if _download(url, path) else None


def nse_sme_bhavcopy(d: date, out_dir: str | Path) -> Optional[Path]:
    """Download NSE SME bhavcopy for one date."""
    out_dir = Path(out_dir)
    date_str = d.strftime("%d%m%y")
    name = f"sme{date_str}.csv"
    url = f"https://archives.nseindia.com/archives/sme/bhavcopy/{name}"
    path = out_dir / name
    return path if _download(url, path) else None


# ═══════════════════════════════════════════════════════════════
#  BHAVCOPY — BSE EQ
# ═══════════════════════════════════════════════════════════════

def bse_bhavcopy(d: date, out_dir: str | Path) -> Optional[Path]:
    """Download BSE EQ bhavcopy (2024+ format) for one trading date."""
    out_dir = Path(out_dir)
    date_str = d.strftime("%Y%m%d")
    name = f"BhavCopy_BSE_CM_0_0_0_{date_str}_F_0000.CSV"
    url = f"https://www.bseindia.com/download/BhavCopy/Equity/{name}"
    path = out_dir / name
    return path if _download(url, path, verify=False) else None


def bse_bhavcopy_old(d: date, out_dir: str | Path) -> Optional[Path]:
    """Download + extract OLD-format BSE EQ bhavcopy (pre-2024-07-08).

    URL: www.bseindia.com/download/BhavCopy/Equity/EQ_ISINCODE_{DDMMYY}.zip
    e.g. EQ_ISINCODE_020524.zip  (2 May 2024)
    """
    out_dir = Path(out_dir)
    date_str = d.strftime("%d%m%y")
    zip_name = f"EQ_ISINCODE_{date_str}.zip"
    url = f"https://www.bseindia.com/download/BhavCopy/Equity/{zip_name}"
    zip_path = out_dir / zip_name
    if not _download(url, zip_path, verify=False):
        return None
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(out_dir)
            csv_name = z.namelist()[0]
    finally:
        zip_path.unlink(missing_ok=True)
    return out_dir / csv_name


# ═══════════════════════════════════════════════════════════════
#  RANGE HELPER
# ═══════════════════════════════════════════════════════════════

def download_history_range(
    from_date: date,
    to_date: date,
    root_dir: str | Path,
    *,
    include_nse_eq: bool = True,
    include_bse_eq: bool = True,
    include_nse_index: bool = True,
    include_nse_sme: bool = False,
    verbose: bool = True,
) -> Dict[str, List[Path]]:
    """Walk every weekday in [from, to] and download selected bhavcopies."""
    root = Path(root_dir)
    result = {"nse_eq": [], "bse_eq": [], "nse_index": [], "nse_sme": []}
    for d in trading_dates(from_date, to_date):
        if include_nse_eq:
            p = nse_bhavcopy(d, root / "nse_eq")
            if p:
                result["nse_eq"].append(p)
                if verbose: print(f"[NSE EQ ]  {d}  {p.name}")
        if include_nse_index:
            p = nse_index_bhavcopy(d, root / "nse_index")
            if p:
                result["nse_index"].append(p)
                if verbose: print(f"[NSE IND]  {d}  {p.name}")
        if include_nse_sme:
            p = nse_sme_bhavcopy(d, root / "nse_sme")
            if p:
                result["nse_sme"].append(p)
                if verbose: print(f"[NSE SME]  {d}  {p.name}")
        if include_bse_eq:
            p = bse_bhavcopy(d, root / "bse_eq")
            if p:
                result["bse_eq"].append(p)
                if verbose: print(f"[BSE EQ ]  {d}  {p.name}")

    if verbose:
        print(
            f"\nDone.  NSE-EQ:{len(result['nse_eq'])}  BSE-EQ:{len(result['bse_eq'])}"
            f"  NSE-IND:{len(result['nse_index'])}  NSE-SME:{len(result['nse_sme'])}"
        )
    return result
