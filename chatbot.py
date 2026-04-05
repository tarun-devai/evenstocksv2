"""
AI Chatbot Backend — FastAPI + WebSocket + Anthropic Streaming
==============================================================
Install:  pip install fastapi uvicorn anthropic python-dotenv
Run:      uvicorn main:app --reload --port 8000
Open:     http://localhost:8000

Set your API key:
  export ANTHROPIC_API_KEY=sk-ant-...
  (or create a .env file with ANTHROPIC_API_KEY=sk-ant-...)
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="Claude Chatbot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Anthropic client ───────────────────────────────────────────────
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM_PROMPT = (
    "You are a helpful, friendly AI assistant. Be concise but thorough. "
    "Use markdown formatting when helpful. For code, always specify the language."
)

# ─── In-memory chat history per connection ───────────────────────────
class ChatSession:
    def __init__(self):
        self.messages: list[dict] = []
        self.created = datetime.now()
        self.cancel_event = asyncio.Event()

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def clear(self):
        self.messages.clear()


# ─── WebSocket endpoint ─────────────────────────────────────────────
@app.websocket("/ws/chat")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    session = ChatSession()

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            action = data.get("action", "message")

            # ── Stop generation ──────────────────────────────────
            if action == "stop":
                session.cancel_event.set()
                continue

            # ── Clear chat ───────────────────────────────────────
            if action == "clear":
                session.clear()
                await ws.send_json({"type": "cleared"})
                continue

            # ── Send message ─────────────────────────────────────
            if action == "message":
                user_text = data.get("content", "").strip()
                if not user_text:
                    continue

                session.add("user", user_text)
                session.cancel_event.clear()

                # Signal streaming start
                await ws.send_json({"type": "stream_start"})

                full_response = ""
                input_tokens = 0
                output_tokens = 0

                try:
                    # Stream from Anthropic
                    with client.messages.stream(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2048,
                        system=SYSTEM_PROMPT,
                        messages=session.messages,
                    ) as stream:
                        for event in stream:
                            # Check if client requested a stop
                            if session.cancel_event.is_set():
                                full_response += "\n\n*(generation stopped)*"
                                stream.close()
                                break

                            if hasattr(event, "type"):
                                if event.type == "content_block_delta":
                                    chunk = event.delta.text
                                    full_response += chunk
                                    await ws.send_json({
                                        "type": "stream_delta",
                                        "content": chunk,
                                    })

                        # Get final usage stats
                        final = stream.get_final_message()
                        input_tokens = final.usage.input_tokens
                        output_tokens = final.usage.output_tokens

                except anthropic.APIError as e:
                    full_response = f"⚠️ API Error: {e.message}"
                    await ws.send_json({
                        "type": "stream_delta",
                        "content": full_response,
                    })

                # Save assistant response to history
                if full_response:
                    session.add("assistant", full_response)

                # Signal streaming complete
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
        except:
            pass


# ─── Health check ────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "model": "claude-sonnet-4-20250514"}


# ─── Serve the frontend ─────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_ui():
    return FileResponse(FRONTEND_DIR / "index.html")


# ─── Run directly ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)