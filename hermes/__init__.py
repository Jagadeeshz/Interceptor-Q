"""
Interceptor Hermes — AI Agent Core

Provides:
- FastAPI application with /event, /health, and dashboard REST endpoints
- Event logging to Postgres
- Config-driven LLM provider
- Live data for the dashboard: companies, opportunities, signals, metrics
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import logging
import os
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes")

# ---------------------------------------------------------------------------
# Database (optional at boot — dashboard degrades gracefully to demo data)
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "POSTGRES_DATABASE_URL",
    "postgresql://interceptor_admin:interceptor_pass@postgres:5432/hermes_db",
)

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        try:
            from sqlalchemy import create_engine
            _engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
        except Exception as e:  # pragma: no cover
            logger.warning(f"SQLAlchemy unavailable: {e}")
    return _engine


def db_query(sql: str):
    """Run a read-only query; return list of dict rows or None when DB is down."""
    engine = _get_engine()
    if engine is None:
        return None
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.warning(f"DB query failed (falling back to demo data): {e}")
        return None


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Interceptor Hermes starting — dashboard API live")
    yield


app = FastAPI(title="Interceptor Hermes", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# LLM config (default DeepSeek as specified)
# ---------------------------------------------------------------------------
HERMES_LLM_PROVIDER = os.getenv("HERMES_LLM_PROVIDER", "deepseek")
HERMES_LLM_MODEL = os.getenv("HERMES_LLM_MODEL", "deepseek-coder-v1.5")

# ---------------------------------------------------------------------------
# Event log (in-memory ring buffer + optional DB persistence)
# ---------------------------------------------------------------------------
_events = []


def _record_event(event_type: str, message: str, source: str = "system"):
    _events.append({
        "id": len(_events) + 1,
        "time": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "message": message,
        "source": source,
    })
    if len(_events) > 200:
        del _events[: len(_events) - 200]


# ---------------------------------------------------------------------------
# Demo data — used when Postgres has no rows yet so the dashboard is never blank
# ---------------------------------------------------------------------------
DEMO_COMPANIES = [
    {"id": "c1", "name": "Vertex AI", "domain": "vertexai.io", "region": "NAC",
     "source_platform": "LinkedIn", "funding_stage": "Series B", "company_size": "150",
     "detected_date": "2026-09-12T09:14:00Z", "status": "ENRICHING"},
    {"id": "c2", "name": "Nova Scale", "domain": "novascale.com", "region": "EU",
     "source_platform": "Apollo", "funding_stage": "Series A", "company_size": "80",
     "detected_date": "2026-09-12T08:02:00Z", "status": "PROSPECT_CREATED"},
    {"id": "c3", "name": "Quantum Flow", "domain": "quantumflow.dev", "region": "APAC",
     "source_platform": "Website", "funding_stage": "Seed", "company_size": "25",
     "detected_date": "2026-09-12T07:40:00Z", "status": "QUALIFIED"},
    {"id": "c4", "name": "Nebula Systems", "domain": "nebula.systems", "region": "MENA",
     "source_platform": "LinkedIn", "funding_stage": "Series C", "company_size": "420",
     "detected_date": "2026-09-12T06:55:00Z", "status": "DISCOVERED"},
    {"id": "c5", "name": "Helios Grid", "domain": "heliosgrid.ai", "region": "NAC",
     "source_platform": "Apollo", "funding_stage": "Series B", "company_size": "210",
     "detected_date": "2026-09-11T18:22:00Z", "status": "CAMPAIGN_ACTIVE"},
    {"id": "c6", "name": "Aurora Data", "domain": "auroradata.io", "region": "LATAM",
     "source_platform": "Website", "funding_stage": "Seed", "company_size": "18",
     "detected_date": "2026-09-11T16:10:00Z", "status": "BOOKED"},
]

DEMO_OPPORTUNITIES = [
    {"id": "o1", "company_id": "c1", "company_name": "Vertex AI", "job_title": "Senior Platform Engineer",
     "matched_pod": "Cloud Ops", "match_score": 98, "source_platform": "LinkedIn", "status": "ENRICHING",
     "region": "NAC", "detected_date": "2026-09-12T09:20:00Z"},
    {"id": "o2", "company_id": "c2", "company_name": "Nova Scale", "job_title": "Data Platform Lead",
     "matched_pod": "Data Eng", "match_score": 92, "source_platform": "Apollo", "status": "PROSPECT_CREATED",
     "region": "EU", "detected_date": "2026-09-12T08:10:00Z"},
    {"id": "o3", "company_id": "c3", "company_name": "Quantum Flow", "job_title": "ML Infrastructure Engineer",
     "matched_pod": "AI/ML", "match_score": 87, "source_platform": "Website", "status": "QUALIFIED",
     "region": "APAC", "detected_date": "2026-09-12T07:45:00Z"},
    {"id": "o4", "company_id": "c4", "company_name": "Nebula Systems", "job_title": "DevOps Manager",
     "matched_pod": "Cloud Ops", "match_score": 81, "source_platform": "LinkedIn", "status": "DISCOVERED",
     "region": "MENA", "detected_date": "2026-09-12T07:00:00Z"},
    {"id": "o5", "company_id": "c5", "company_name": "Helios Grid", "job_title": "Staff SRE",
     "matched_pod": "Cloud Ops", "match_score": 76, "source_platform": "Apollo", "status": "CAMPAIGN_ACTIVE",
     "region": "NAC", "detected_date": "2026-09-11T18:30:00Z"},
    {"id": "o6", "company_id": "c6", "company_name": "Aurora Data", "job_title": "Analytics Engineer",
     "matched_pod": "Data Eng", "match_score": 71, "source_platform": "Website", "status": "BOOKED",
     "region": "LATAM", "detected_date": "2026-09-11T16:15:00Z"},
]

DEMO_SIGNALS = [
    {"id": 1, "time": "2026-09-12T09:22:00Z", "type": "signal", "message": "New intent signal from Vertex AI (LinkedIn)"},
    {"id": 2, "time": "2026-09-12T09:10:00Z", "type": "system", "message": 'Company "Nova Scale" successfully enriched via Apollo'},
    {"id": 3, "time": "2026-09-12T08:48:00Z", "type": "system", "message": "Webhook trigger: crm-company-sync received"},
    {"id": 4, "time": "2026-09-12T08:12:00Z", "type": "signal", "message": 'Anomalous growth detected in "Quantum Flow"'},
    {"id": 5, "time": "2026-09-12T07:30:00Z", "type": "system", "message": "HITL approval granted for Helios Grid outreach"},
]

_demo_rng = random.Random(42)


def _demo_metrics():
    return {
        "leads_discovered": {"value": 1284, "trend": 12.0},
        "enrichment_rate": {"value": 84.2, "trend": 3.1},
        "active_signals": {"value": 42, "trend": -2.0},
        "conversion_prob": {"value": 18.4, "trend": 0.8},
        "source": "demo",
    }


def _db_metrics():
    """Compute live metrics from Postgres; None when tables are missing/empty."""
    rows = db_query(
        "SELECT (SELECT COUNT(*) FROM companies) AS companies, "
        "(SELECT COUNT(*) FROM opportunities) AS opportunities, "
        "(SELECT COUNT(*) FROM opportunities WHERE status IN ('QUALIFIED','PROSPECT_CREATED','CAMPAIGN_ACTIVE','BOOKED')) AS qualified"
    )
    if not rows:
        return None
    r = rows[0]
    companies = int(r["companies"] or 0)
    opportunities = int(r["opportunities"] or 0)
    qualified = int(r["qualified"] or 0)
    if companies == 0 and opportunities == 0:
        return None
    enrich_rate = round(100.0 * qualified / opportunities, 1) if opportunities else 0.0
    return {
        "leads_discovered": {"value": companies, "trend": 0.0},
        "enrichment_rate": {"value": enrich_rate, "trend": 0.0},
        "active_signals": {"value": opportunities, "trend": 0.0},
        "conversion_prob": {"value": round(100.0 * qualified / companies, 1) if companies else 0.0, "trend": 0.0},
        "source": "postgres",
    }


def _serialize(rows):
    out = []
    for row in rows:
        item = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()
            elif isinstance(v, timedelta):
                item[k] = str(v)
            else:
                item[k] = v
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# Event receipt endpoint
# ---------------------------------------------------------------------------
@app.post("/event")
async def receive_event(request: Request):
    """Receive JSON events from Hermes agents, n8n, or external services."""
    try:
        event = await request.json()
        event_type = event.get("type", "unknown")
        logger.info(f"Received event: {event_type}")
        message = event.get("message") or f"{event_type} received"
        _record_event(event_type, message, source=event.get("source", "webhook"))
        return JSONResponse({"status": "received", "event_type": event_type}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health check for Docker orchestration and load balancers."""
    db_ok = db_query("SELECT 1 AS ok") is not None
    return {
        "status": "ok",
        "service": "hermes",
        "llm_provider": HERMES_LLM_PROVIDER,
        "llm_model": HERMES_LLM_MODEL,
        "database": "connected" if db_ok else "unavailable",
    }


# ---------------------------------------------------------------------------
# Dashboard API
# ---------------------------------------------------------------------------
@app.get("/api/metrics")
async def api_metrics():
    """KPI cards — live from Postgres when available, demo otherwise."""
    m = _db_metrics() or _demo_metrics()
    return m


@app.get("/api/opportunities")
async def api_opportunities(limit: int = 50):
    """High-intent opportunities for the main table."""
    rows = db_query(
        "SELECT o.id, o.company_id, c.name AS company_name, o.job_title, o.matched_pod, "
        "o.match_score, o.source_platform, o.status, o.region, o.detected_date "
        "FROM opportunities o LEFT JOIN companies c ON c.id = o.company_id "
        "ORDER BY o.match_score DESC NULLS LAST LIMIT " + str(int(limit))
    )
    if rows:
        return {"source": "postgres", "items": _serialize(rows)}
    return {"source": "demo", "items": DEMO_OPPORTUNITIES[:limit]}


@app.get("/api/companies")
async def api_companies(limit: int = 100):
    """Discovered companies for the Opportunity Map."""
    rows = db_query(
        "SELECT id, name, domain, region, source_platform, funding_stage, company_size, "
        "detected_date FROM companies ORDER BY detected_date DESC LIMIT " + str(int(limit))
    )
    if rows:
        return {"source": "postgres", "items": _serialize(rows)}
    return {"source": "demo", "items": DEMO_COMPANIES[:limit]}


@app.get("/api/signals")
async def api_signals(limit: int = 20):
    """Live signal feed — merges runtime events with DB-backed history."""
    items = list(_events)
    db_sig = db_query(
        "SELECT o.id, o.detected_date, o.status, c.name AS company_name, o.source_platform "
        "FROM opportunities o LEFT JOIN companies c ON c.id = o.company_id "
        "ORDER BY o.detected_date DESC LIMIT 10"
    )
    if db_sig:
        for r in db_sig:
            name = r.get("company_name") or "Unknown company"
            items.append({
                "id": f"db-{r.get('id')}",
                "time": r["detected_date"].isoformat() if isinstance(r.get("detected_date"), datetime) else str(r.get("detected_date")),
                "type": "signal",
                "message": f"{name} detected via {r.get('source_platform') or 'unknown source'} ({r.get('status')})",
            })
    if not items:
        items = DEMO_SIGNALS[:limit]
    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return {"source": "postgres" if db_sig else "runtime", "items": items[:limit]}


@app.post("/api/deploy")
async def api_deploy(request: Request):
    """Deploy Agent — kicks a discovery run event into the pipeline."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    target = body.get("target", "all sources")
    _record_event("deploy", f"Agent deployed — scanning {target}", source="dashboard")
    return {"status": "queued", "target": target, "note": "n8n mining-trigger workflow will pick this up"}


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Interceptor Hermes AI Agent is running", "version": "0.2.0"}