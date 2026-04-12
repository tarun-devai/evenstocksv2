"""
chat.py — WebSocket endpoint with stock autocomplete + DB-powered analysis
"""

import json
import anthropic
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import MODEL, MAX_TOKENS
from app.session import ChatSession
from app.stock_db import get_conn, search_stocks, build_stock_context

router = APIRouter()
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are EvenStocks AI — an expert Indian stock market analyst.

RULES:
- ONLY use stock data provided in the conversation. NEVER use training data for stock numbers.
- If stock data is provided, give a concise analytical report covering: company overview, key metrics, financial performance, balance sheet, shareholding, strengths, risks, and assessment.
- If no stock data was provided but user asks about a stock, tell them to type @ and select the stock from autocomplete.
- When comparing stocks, use only the provided data.
- Be specific with actual numbers, not generic.
- Keep responses compact — no excessive blank lines or spacing. Use short bullet points.
- Use markdown: ## for sections, **bold** for key numbers, - for bullets.
- For general questions, answer normally."""


@router.websocket("/ws/chat")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    session = ChatSession()
    db_conn = get_conn()

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

            # ── Autocomplete search ──────────────────────────
            if action == "autocomplete":
                query = data.get("query", "").strip()
                if not query or not db_conn:
                    await ws.send_json({"type": "autocomplete", "results": []})
                    continue
                results = search_stocks(db_conn, query, limit=8)
                await ws.send_json({"type": "autocomplete", "results": results})
                continue

            # ── Send message (with optional stock tags) ──────
            if action == "message":
                user_text = data.get("content", "").strip()
                selected_stocks = data.get("stocks", [])  # list of stock_name strings
                if not user_text:
                    continue

                # Build the actual message sent to Claude
                # If stocks are selected, prepend their full DB data
                context_blocks = []
                if selected_stocks and db_conn:
                    for stock_name in selected_stocks:
                        ctx = build_stock_context(db_conn, stock_name)
                        if ctx:
                            context_blocks.append(ctx)

                if context_blocks:
                    full_context = "\n\n---\n\n".join(context_blocks)
                    llm_message = (
                        f"The user has selected the following stock(s). "
                        f"All data below comes from the database — use ONLY this data.\n\n"
                        f"{full_context}\n\n"
                        f"---\n\n"
                        f"User's question: {user_text}"
                    )
                else:
                    llm_message = user_text

                # Store the user-visible text in history (not the giant context)
                session.add("user", llm_message)
                session.cancel_event.clear()

                await ws.send_json({"type": "stream_start"})

                full_response = ""
                input_tokens = output_tokens = 0

                try:
                    with client.messages.stream(
                        model=MODEL,
                        max_tokens=MAX_TOKENS,
                        system=SYSTEM_PROMPT,
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
                                await ws.send_json({"type": "stream_delta", "content": chunk})

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
                    "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
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
