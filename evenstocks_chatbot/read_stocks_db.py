"""
read_stocks_db.py
────────────────────────────────────────────────────────────────
Utility to read and query data from stocks.db

Usage:
  python read_stocks_db.py                          # summary stats
  python read_stocks_db.py --stock "Ksolves_India"  # one stock's full data
  python read_stocks_db.py --list                   # list all stock names
  python read_stocks_db.py --table quarters --stock "Ksolves_India"
  python read_stocks_db.py --sql "SELECT stock_name, market_cap, roce FROM company_info LIMIT 10"
  python read_stocks_db.py --pdfs "Ksolves_India"   # show PDF texts for a stock
"""

import os
import json
import sqlite3
import argparse

DB_PATH = os.path.join("data", "stocks.db")


def get_conn():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        print("Run scrape_tables.py or scrape_pdfs.py first.")
        exit(1)
    return sqlite3.connect(DB_PATH)


def summary():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM company_info").fetchone()[0]
    print(f"Total stocks in DB: {total}")

    # Table counts
    tables_count = conn.execute("SELECT COUNT(DISTINCT stock_name) FROM financial_tables").fetchone()[0]
    print(f"Stocks with financial tables: {tables_count}")

    # PDF counts
    try:
        pdfs = conn.execute("SELECT COUNT(*) FROM pdf_texts").fetchone()[0]
        pdf_stocks = conn.execute("SELECT COUNT(DISTINCT stock_name) FROM pdf_texts").fetchone()[0]
        print(f"PDF records: {pdfs}  (across {pdf_stocks} stocks)")
    except sqlite3.OperationalError:
        print("PDF table not yet created (run scrape_pdfs.py)")

    # Sample
    print("\n--- Sample (first 5 stocks) ---")
    rows = conn.execute(
        "SELECT stock_name, market_cap, current_price, stock_pe, roce, roe FROM company_info LIMIT 5"
    ).fetchall()
    cols = ["stock_name", "market_cap", "price", "PE", "ROCE", "ROE"]
    print(f"{'stock_name':<30} {'market_cap':>12} {'price':>10} {'PE':>8} {'ROCE':>8} {'ROE':>8}")
    print("-" * 80)
    for r in rows:
        print(f"{r[0]:<30} {r[1] or '':>12} {r[2] or '':>10} {r[3] or '':>8} {r[4] or '':>8} {r[5] or '':>8}")
    conn.close()


def list_stocks():
    conn = get_conn()
    rows = conn.execute("SELECT stock_name FROM company_info ORDER BY stock_name").fetchall()
    for r in rows:
        print(r[0])
    print(f"\nTotal: {len(rows)}")
    conn.close()


def show_stock(stock_name):
    conn = get_conn()

    # Company info
    row = conn.execute("SELECT * FROM company_info WHERE stock_name = ?", (stock_name,)).fetchone()
    if not row:
        print(f"Stock '{stock_name}' not found.")
        conn.close()
        return

    cols = [d[0] for d in conn.execute("SELECT * FROM company_info LIMIT 0").description]
    print("=" * 60)
    print(f"  {stock_name}")
    print("=" * 60)
    for col, val in zip(cols, row):
        if col in ("pros", "cons") and val:
            items = json.loads(val)
            if items:
                print(f"\n  {col.upper()}:")
                for item in items:
                    print(f"    - {item}")
        elif col == "about" and val:
            print(f"\n  ABOUT:\n    {val[:300]}{'...' if len(val) > 300 else ''}")
        else:
            print(f"  {col:<18} {val or ''}")

    # Financial tables
    tables = conn.execute(
        "SELECT table_type, data FROM financial_tables WHERE stock_name = ?", (stock_name,)
    ).fetchall()

    for table_type, data_json in tables:
        data = json.loads(data_json)
        if not data:
            continue
        print(f"\n--- {table_type.upper()} ---")
        # Handle both flat list and nested list of tables
        rows_list = data if isinstance(data[0], dict) else data[0] if data else []
        if not rows_list:
            continue
        headers = list(rows_list[0].keys())
        # Print header
        header_line = "  ".join(f"{h:>12}" for h in headers[:8])
        print(header_line)
        print("-" * len(header_line))
        for r in rows_list[:10]:  # show first 10 rows
            vals = [r.get(h, "") for h in headers[:8]]
            print("  ".join(f"{v:>12}" for v in vals))
        if len(rows_list) > 10:
            print(f"  ... ({len(rows_list)} rows total)")

    conn.close()


def show_table(stock_name, table_type):
    conn = get_conn()
    row = conn.execute(
        "SELECT data FROM financial_tables WHERE stock_name = ? AND table_type = ?",
        (stock_name, table_type)
    ).fetchone()

    if not row:
        print(f"No '{table_type}' data for '{stock_name}'")
        conn.close()
        return

    data = json.loads(row[0])
    print(json.dumps(data, indent=2, ensure_ascii=False))
    conn.close()


def run_sql(query):
    conn = get_conn()
    try:
        cursor = conn.execute(query)
        cols = [d[0] for d in cursor.description] if cursor.description else []
        rows = cursor.fetchall()

        if not rows:
            print("No results.")
            conn.close()
            return

        # Print as table
        widths = [max(len(str(c)), max(len(str(r[i])) for r in rows)) for i, c in enumerate(cols)]
        header = "  ".join(f"{c:<{widths[i]}}" for i, c in enumerate(cols))
        print(header)
        print("-" * len(header))
        for r in rows:
            print("  ".join(f"{str(v):<{widths[i]}}" for i, v in enumerate(r)))
        print(f"\n({len(rows)} rows)")
    except Exception as e:
        print(f"SQL error: {e}")
    conn.close()


def show_pdfs(stock_name):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT doc_type, doc_index, title, filename, LENGTH(text) as text_len "
            "FROM pdf_texts WHERE stock_name = ? ORDER BY doc_type, doc_index",
            (stock_name,)
        ).fetchall()
    except sqlite3.OperationalError:
        print("PDF table not yet created (run scrape_pdfs.py)")
        conn.close()
        return

    if not rows:
        print(f"No PDFs for '{stock_name}'")
        conn.close()
        return

    print(f"\nPDFs for {stock_name}:")
    print(f"{'type':<18} {'#':>3} {'title':<40} {'text_chars':>10}")
    print("-" * 75)
    for r in rows:
        print(f"{r[0]:<18} {r[1]:>3} {r[2][:40]:<40} {r[4] or 0:>10}")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Read from stocks.db")
    parser.add_argument("--stock", type=str, help="Show full data for a stock")
    parser.add_argument("--list", action="store_true", help="List all stock names")
    parser.add_argument("--table", type=str, help="Show specific table (use with --stock)")
    parser.add_argument("--sql", type=str, help="Run a raw SQL query")
    parser.add_argument("--pdfs", type=str, help="Show PDFs for a stock")
    args = parser.parse_args()

    if args.sql:
        run_sql(args.sql)
    elif args.list:
        list_stocks()
    elif args.stock and args.table:
        show_table(args.stock, args.table)
    elif args.stock:
        show_stock(args.stock)
    elif args.pdfs:
        show_pdfs(args.pdfs)
    else:
        summary()


if __name__ == "__main__":
    main()
