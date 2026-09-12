"""
Interceptor Hermes — AI Agent Core

Provides:
- FastAPI application with /event and /health endpoints
- Event logging to Postgres
- Config-driven LLM provider
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import os

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="Interceptor Hermes", version="0.1.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes")

# ---------------------------------------------------------------------------
# LLM config (default DeepSeek as specified)
# ---------------------------------------------------------------------------
HERMES_LLM_PROVIDER = os.getenv("HERMES_LLM_PROVIDER", "deepseek")
HERMES_LLM_MODEL = os.getenv("HERMES_LLM_MODEL", "deepseek-coder-v1.5")

# ---------------------------------------------------------------------------
# Event receipt endpoint
# ---------------------------------------------------------------------------
@app.post("/event")
async def receive_event(request: Request):
    """Receive JSON events from Hermes agents, n8n, or external services."""
    try:
        event = await request.json()
        logger.info(f"Received event: {event.get('type', 'unknown')}")
        # TODO: Persist to Postgres, dispatch to appropriate agent handler
        return JSONResponse({"status": "received", "event_type": event.get("type")}, status=200)
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status=400)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health check for Docker orchestration and load balancers."""
    return {"status": "ok", "service": "hermes", "llm_provider": HERMES_LLM_PROVIDER, "llm_model": HERMES_LLM_MODEL}


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Interceptor Hermes AI Agent is running", "version": "0.1.0"}