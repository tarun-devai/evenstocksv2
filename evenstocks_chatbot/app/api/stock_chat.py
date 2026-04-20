"""
stock_chat.py — WebSocket endpoint for stock analysis chatbot
"""

import json
import asyncio

import anthropic
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import MODEL, MAX_TOKENS
from app.session import ChatSession
from app.stock_db import (
    get_conn, search_stocks, build_stock_context,
    resolve_nse_symbol, get_eod_rows,
)

router = APIRouter()

client = anthropic.Anthropic()


def _build_charts_payload(stock_names: list[str]) -> list[dict]:
    """For each Screener stock name, return chart-ready data for the frontend.

    Shape: [{screener_name, nse_symbol, eod: [...], count}]
    Rows we don't have (no NSE match, no EOD data) are skipped but logged so
    you can diagnose why a chart didn't render.
    """
    out = []
    for sn in stock_names:
        if not sn:
            continue
        nse = resolve_nse_symbol(sn)
        if not nse:
            print(f"[charts] no NSE symbol for '{sn}' — check /api/stock/search on evenstocks-api")
            continue
        rows = get_eod_rows(nse, days=90)
        if not rows:
            print(f"[charts] no EOD data for {nse} — backfill may not be populated yet")
            continue
        out.append({
            "screener_name": sn,
            "nse_symbol": nse,
            "eod": [
                {"date": r.get("date"), "close": r.get("close"),
                 "open": r.get("open"), "high": r.get("high"), "low": r.get("low"),
                 "volume": r.get("volume")}
                for r in rows
            ],
            "count": len(rows),
        })
    print(f"[charts] built {len(out)}/{len([s for s in stock_names if s])} charts")
    return out

STOCK_SYSTEM_PROMPT = """You are an expert Indian stock market analyst covering BSE/NSE-listed equities.

You will receive two kinds of data:
  1. FUNDAMENTAL data from Screener — company info, financial tables, PDFs, shareholding.
  2. TECHNICAL data under a '## Trading Data (NSE)' block — last-close, SMA/RSI,
     volume, 90-day OHLC history, 5-day and 30-day price moves.

Produce a thorough investment report with these sections (skip any where data is truly missing):

1. **Company Overview** — business, sector, market position
2. **Key Metrics** — PE, PB, ROCE, ROE, dividend yield, book value, market cap
3. **Financial Performance** — revenue/profit trends, margins, from quarterly/annual tables
4. **Balance Sheet Health** — debt, cash flow, leverage
5. **Shareholding Pattern** — promoter/FII/DII changes
6. **Technical Analysis** — use the NSE trading data:
   - Trend: price vs SMA20 / SMA50 / SMA200 (above = bullish, below = bearish)
   - Momentum: RSI(14) — >70 overbought, <30 oversold, 50 neutral
   - Range position: where is the price within the 90-day high/low band?
   - Short vs long-term moves: 5-day and 30-day % change
   - Support/resistance: derive from recent lows/highs in the OHLC table
   - Volume: is the recent volume above or below the 90-day average?
   - Candlestick pattern hints from recent 3-5 days OHLC (e.g. long upper wicks, gaps)
7. **Strengths & Risks** — merge fundamental + technical
8. **Overall Assessment** — bull case vs bear case, conviction, who should buy/avoid, timeframe

Guidelines:
- Use actual numbers from the provided data. Be specific, not generic.
- When doing comparisons between stocks, use a table for technical + fundamental side-by-side.
- Format with clear markdown headers and bullet points.
- If technical data says "no EOD data yet in trading DB", explicitly flag that you can't do technical analysis yet and skip section 6.
- Never hallucinate prices or indicators — use only what's provided."""


@router.websocket("/ws/stock-chat")
async def stock_chat_ws(ws: WebSocket):
    await ws.accept()
    session = ChatSession()
    db_conn = get_conn()

    if not db_conn:
        await ws.send_json({
            "type": "error",
            "message": "Database not found. Run scrape_tables.py first.",
        })
        await ws.close()
        return

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            action = data.get("action", "message")

            # ── Stop generation ──────────────────────────────
            if action == "stop":
                session.cancel_event.set()
                continue

            # ── Clear chat ───────────────────────────────────
            if action == "clear":
                session.clear()
                await ws.send_json({"type": "cleared"})
                continue

            # ── Search stocks ────────────────────────────────
            if action == "search":
                query = data.get("query", "").strip()
                results = search_stocks(db_conn, query)
                await ws.send_json({
                    "type": "search_results",
                    "results": results,
                })
                continue

            # ── Analyze a stock ──────────────────────────────
            if action == "analyze":
                stock_name = data.get("stock_name", "").strip()
                if not stock_name:
                    continue

                context = build_stock_context(db_conn, stock_name)
                if not context:
                    await ws.send_json({
                        "type": "error",
                        "message": f"No data found for '{stock_name}'",
                    })
                    continue

                # Build the analysis prompt
                user_msg = (
                    f"Analyze the following stock and provide a detailed investment report:\n\n"
                    f"{context}"
                )
                session.clear()
                session.add("user", user_msg)
                session.cancel_event.clear()

                await ws.send_json({"type": "stream_start"})
                full_response = ""
                input_tokens = output_tokens = 0

                try:
                    with client.messages.stream(
                        model=MODEL,
                        max_tokens=MAX_TOKENS,
                        system=STOCK_SYSTEM_PROMPT,
                        messages=session.messages,
                    ) as stream:
                        for event in stream:
                            if session.cancel_event.is_set():
                                full_response += "\n\n*(generation stopped)*"
                                stream.close()
                                break
                            if hasattr(event, "type") and event.type == "content_block_delta":
                                chunk = event.delta.text
                                full_response += chunk
                                await ws.send_json({
                                    "type": "stream_delta",
                                    "content": chunk,
                                })
                        final = stream.get_final_message()
                        input_tokens = final.usage.input_tokens
                        output_tokens = final.usage.output_tokens
                except anthropic.APIError as e:
                    full_response = f"API Error: {e.message}"
                    await ws.send_json({"type": "stream_delta", "content": full_response})

                if full_response:
                    session.add("assistant", full_response)

                # Send chart data for the analyzed stock — frontend renders below response.
                charts = _build_charts_payload([stock_name])
                if charts:
                    await ws.send_json({"type": "charts", "charts": charts})

                await ws.send_json({
                    "type": "stream_end",
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                })
                continue

            # ── Compare multiple stocks ──────────────────────
            if action == "compare":
                stock_names = data.get("stock_names", [])
                user_text = data.get("content", "").strip()
                if not stock_names or len(stock_names) < 2:
                    continue

                contexts = []
                for sn in stock_names:
                    ctx = build_stock_context(db_conn, sn.strip())
                    if ctx:
                        contexts.append(f"=== {sn.upper()} ===\n{ctx}")

                if not contexts:
                    await ws.send_json({
                        "type": "error",
                        "message": f"No data found for the requested stocks",
                    })
                    continue

                combined = "\n\n".join(contexts)
                user_msg = (
                    f"Compare the following stocks and provide a detailed comparative analysis. "
                    f"User's request: {user_text}\n\n{combined}"
                )
                session.clear()
                session.add("user", user_msg)
                session.cancel_event.clear()

                await ws.send_json({"type": "stream_start"})
                full_response = ""
                input_tokens = output_tokens = 0

                try:
                    with client.messages.stream(
                        model=MODEL,
                        max_tokens=MAX_TOKENS,
                        system=STOCK_SYSTEM_PROMPT,
                        messages=session.messages,
                    ) as stream:
                        for event in stream:
                            if session.cancel_event.is_set():
                                full_response += "\n\n*(generation stopped)*"
                                stream.close()
                                break
                            if hasattr(event, "type") and event.type == "content_block_delta":
                                chunk = event.delta.text
                                full_response += chunk
                                await ws.send_json({
                                    "type": "stream_delta",
                                    "content": chunk,
                                })
                        final = stream.get_final_message()
                        input_tokens = final.usage.input_tokens
                        output_tokens = final.usage.output_tokens
                except anthropic.APIError as e:
                    full_response = f"API Error: {e.message}"
                    await ws.send_json({"type": "stream_delta", "content": full_response})

                if full_response:
                    session.add("assistant", full_response)

                # Send chart data for every stock being compared.
                charts = _build_charts_payload(stock_names)
                if charts:
                    await ws.send_json({"type": "charts", "charts": charts})

                await ws.send_json({
                    "type": "stream_end",
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                })
                continue

            # ── Follow-up question about current stock ───────
            if action == "message":
                user_text = data.get("content", "").strip()
                if not user_text:
                    continue

                session.add("user", user_text)
                session.cancel_event.clear()

                await ws.send_json({"type": "stream_start"})
                full_response = ""
                input_tokens = output_tokens = 0

                try:
                    with client.messages.stream(
                        model=MODEL,
                        max_tokens=MAX_TOKENS,
                        system=STOCK_SYSTEM_PROMPT,
                        messages=session.messages,
                    ) as stream:
                        for event in stream:
                            if session.cancel_event.is_set():
                                full_response += "\n\n*(generation stopped)*"
                                stream.close()
                                break
                            if hasattr(event, "type") and event.type == "content_block_delta":
                                chunk = event.delta.text
                                full_response += chunk
                                await ws.send_json({
                                    "type": "stream_delta",
                                    "content": chunk,
                                })
                        final = stream.get_final_message()
                        input_tokens = final.usage.input_tokens
                        output_tokens = final.usage.output_tokens
                except anthropic.APIError as e:
                    full_response = f"API Error: {e.message}"
                    await ws.send_json({"type": "stream_delta", "content": full_response})

                if full_response:
                    session.add("assistant", full_response)

                await ws.send_json({
                    "type": "stream_end",
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if db_conn:
            db_conn.close()
