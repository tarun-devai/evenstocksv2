"""
stock_detail.py — REST endpoints for stock detail pages
"""

from fastapi import APIRouter, HTTPException
from app.stock_db import get_conn, search_stocks, get_company_info, get_financial_tables

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/search")
async def api_search_stocks(q: str = "", limit: int = 20):
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        results = search_stocks(conn, q, limit)
        return {"results": results}
    finally:
        conn.close()


# Popular large-cap Indian tickers for the home-page ticker strip.
# Ordered roughly by retail interest / index weight.
POPULAR_TICKERS = [
    "Reliance_Industries", "TCS", "HDFC_Bank", "Infosys", "ICICI_Bank",
    "Bharti_Airtel", "SBI", "ITC", "Larsen_&_Toubro", "Kotak_Mah_Bank",
    "Hind_Unilever", "Axis_Bank", "Bajaj_Finance", "Maruti_Suzuki", "Sun_PharmaInds",
    "Tata_Motors", "Tata_Steel", "Asian_Paints", "HCL_Technologies", "NTPC",
    "Power_Grid_Corpn", "UltraTech_Cem", "Titan_Company", "Wipro", "Oil_India",
    "Adani_Enterp", "JSW_Steel", "Coal_India", "Nestle_India", "IndusInd_Bank",
]


@router.get("/popular")
async def api_popular_stocks():
    """Returns a curated list of popular stocks with prices for the home ticker strip."""
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        placeholders = ",".join("?" for _ in POPULAR_TICKERS)
        rows = conn.execute(
            f"""SELECT stock_name, current_price, high_low, market_cap, stock_pe
                FROM company_info
                WHERE stock_name IN ({placeholders})""",
            POPULAR_TICKERS,
        ).fetchall()
        by_name = {r["stock_name"]: dict(r) for r in rows}
        # preserve curated order and drop any missing
        ordered = [by_name[t] for t in POPULAR_TICKERS if t in by_name]
        return {"results": ordered}
    finally:
        conn.close()


@router.get("/{stock_name}")
async def api_get_stock_detail(stock_name: str):
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        info = get_company_info(conn, stock_name)
        if not info:
            raise HTTPException(status_code=404, detail=f"Stock '{stock_name}' not found")
        tables = get_financial_tables(conn, stock_name)
        return {"info": info, "tables": tables}
    finally:
        conn.close()
