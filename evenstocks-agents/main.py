"""FastAPI entrypoint for evenstocks-agents service.

Exposes:
  GET /health                         — service health
  GET /analyze/{ticker}               — one-shot JSON verdict (blocking)
  GET /analyze/{ticker}/stream        — SSE stream of per-agent events
"""

import json
import logging
import queue
import threading
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from config import settings
from graph.orchestrator import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("evenstocks-agents")

app = FastAPI(title="EvenStocks Agents", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    ticker: str
    stock_name: str | None = None
    current_price: float | str | None = None
    analyst_reports: dict | None = None
    analyst_errors: dict | None = None
    debate: dict | None = None
    risk_views: dict | None = None
    risk_final: str | None = None
    verdict: dict | None = None
    verdict_error: str | None = None
    elapsed_sec: float | None = None
    error: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "evenstocks-agents",
        "version": "0.2.0",
        "models": {"deep": settings.DEEP_MODEL, "quick": settings.QUICK_MODEL},
        "anthropic_key_configured": bool(settings.ANTHROPIC_API_KEY),
    }


@app.get("/analyze/{ticker}", response_model=AnalyzeResponse)
def analyze(ticker: str):
    _require_api_key()
    log.info("analyze ticker=%s", ticker)
    result = run_pipeline(ticker)

    if result.get("error") and "not found" in str(result.get("error", "")).lower():
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/analyze/{ticker}/stream")
async def analyze_stream(ticker: str):
    """SSE stream: emits per-agent events as the pipeline progresses.

    Event types:
      pipeline_started
      agent_started     { agent, round? }
      agent_completed   { agent, round?, report, error? }
      pipeline_completed { elapsed_sec, rating }
      result            — final full JSON (same shape as /analyze)
      error             — any failure
    """
    _require_api_key()
    log.info("stream ticker=%s", ticker)

    q: queue.Queue = queue.Queue()
    sentinel = object()

    def worker():
        try:
            def on_event(event: str, payload: dict):
                q.put({"event": event, "data": json.dumps(payload)})

            final = run_pipeline(ticker, on_event=on_event)
            q.put({"event": "result", "data": json.dumps(final, default=str)})
        except Exception as exc:
            log.exception("stream worker failed")
            q.put({"event": "error", "data": json.dumps({"message": f"{type(exc).__name__}: {exc}"})})
        finally:
            q.put(sentinel)

    threading.Thread(target=worker, daemon=True).start()

    async def event_gen() -> AsyncIterator[dict]:
        import asyncio
        loop = asyncio.get_event_loop()
        while True:
            item = await loop.run_in_executor(None, q.get)
            if item is sentinel:
                break
            yield item

    return EventSourceResponse(event_gen())


def _require_api_key():
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured on the agents service.",
        )
