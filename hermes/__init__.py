"""Interceptor Hermes — AI Agent Core

Provides:
- FastAPI application with /event, /health, and dashboard REST endpoints
- Event logging to Postgres
- Config-driven LLM provider
- Live data: companies, opportunities, signals, metrics
"""

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import logging
import os
import json

# Import SQLAlchemy and our models from crm
import hermes.crm as crm
from sqlalchemy import text, func

# Import workers
from hermes.worker_enrich import start_worker as start_enrichment_worker
from hermes.worker_outbound import start_outbound_worker as start_outbound_worker
from hermes.discoverer import start_discovery_scheduler, run_discovery_once

# Import LLM
from hermes.llm import generate_message

# Import config for settings
from hermes.config import settings

# Prometheus instrumentation
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes")

# ---------------------------------------------------------------------------
# Database availability flag
# ---------------------------------------------------------------------------
try:
    # Test connection
    with crm.engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    _db_available = True
    logger.info("Database connection successful.")
except Exception as e:
    _db_available = False
    logger.warning(f"Database initialization failed: {e}")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Interceptor Hermes starting — dashboard API live")
    # Start discovery worker if enabled
    if os.getenv("ENABLE_DISCOVERY", "false").lower() == "true":
        start_discovery_scheduler()
        logger.info("Discovery scheduler started")
    # Start enrichment worker
    start_enrichment_worker()
    logger.info("Enrichment worker started")
    # Start outbound worker
    start_outbound_worker()
    logger.info("Outbound worker started")
    yield

app = FastAPI(title="Interceptor Hermes", version="0.2.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Prometheus instrumentation
# ---------------------------------------------------------------------------
Instrumentator().instrument(app).expose(app)

# ---------------------------------------------------------------------------
# Authentication middleware (API Key)
# ---------------------------------------------------------------------------
API_KEY = os.getenv("API_KEY")
if API_KEY:
    @app.middleware("http")
    async def api_key_middleware(request: Request, call_next):
        # Skip auth for health check and root endpoint
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        key = request.headers.get("X-API-Key")
        if key == API_KEY:
            return await call_next(request)
        raise HTTPException(status_code=401, detail="Invalid API Key")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "hermes",
        "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
        "llm_model": os.getenv("LLM_MODEL", "deepseek-coder-v1.5"),
        "database": "connected" if _db_available else "unavailable",
    }

# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Interceptor Hermes API is running"}

# ---------------------------------------------------------------------------
# Event endpoint (for external sources to feed raw leads)
# ---------------------------------------------------------------------------
@app.post("/event")
async def post_event(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = await request.body()
    # Log the event
    db = crm.SessionLocal()
    event_log = crm.EventLog(
        type=payload.get("type") if isinstance(payload, dict) else "unknown",
        time=datetime.now(timezone.utc),
        payload=payload if isinstance(payload, dict) else {"raw": str(payload)},
    )
    db.add(event_log)
    db.commit()
    db.close()
    # If it's a raw lead, we could trigger enrichment, but we rely on the worker polling.
    return {"status": "received", "payload": payload}

# ---------------------------------------------------------------------------
# Dashboard endpoints (proxy to CRM queries)
# ---------------------------------------------------------------------------
@app.get("/api/companies")
async def get_companies():
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    companies = db.query(crm.Company).order_by(crm.Company.detected_date.desc()).limit(100).all()
    db.close()
    return [
        {
            "id": c.id,
            "name": c.name,
            "domain": c.domain,
            "region": c.region,
            "source_platform": c.source_platform,
            "funding_stage": c.funding_stage,
            "company_size": c.company_size,
            "detected_date": c.detected_date.isoformat() if c.detected_date else None,
            "status": c.status,
        }
        for c in companies
    ]

@app.post("/api/companies")
async def create_company(company: dict):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    db_company = crm.Company(
        name=company.get("name"),
        domain=company.get("domain"),
        region=company.get("region"),
        source_platform=company.get("source_platform"),
        funding_stage=company.get("funding_stage"),
        company_size=company.get("company_size"),
        status=company.get("status"),
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    db.close()
    return {
        "id": db_company.id,
        "name": db_company.name,
        "domain": db_company.domain,
        "region": db_company.region,
        "source_platform": db_company.source_platform,
        "funding_stage": db_company.funding_stage,
        "company_size": db_company.company_size,
        "detected_date": db_company.detected_date.isoformat() if db_company.detected_date else None,
        "status": db_company.status,
    }

@app.get("/api/opportunities")
async def get_opportunities():
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    opportunities = db.query(crm.Opportunity).order_by(crm.Opportunity.detected_date.desc()).limit(100).all()
    db.close()
    return [
        {
            "id": o.id,
            "company_id": o.company_id,
            "job_title": o.job_title,
            "matched_pod": o.matched_pod,
            "match_score": o.match_score,
            "source_platform": o.source_platform,
            "status": o.status,
            "region": o.region,
            "detected_date": o.detected_date.isoformat() if o.detected_date else None,
        }
        for o in opportunities
    ]

@app.post("/api/opportunities")
async def create_opportunity(opportunity: dict):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    db_opportunity = crm.Opportunity(
        company_id=opportunity.get("company_id"),
        job_title=opportunity.get("job_title"),
        matched_pod=opportunity.get("matched_pod"),
        match_score=opportunity.get("match_score"),
        source_platform=opportunity.get("source_platform"),
        status=opportunity.get("status"),
        region=opportunity.get("region"),
    )
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    db.close()
    return {
        "id": db_opportunity.id,
        "company_id": db_opportunity.company_id,
        "job_title": db_opportunity.job_title,
        "matched_pod": db_opportunity.matched_pod,
        "match_score": db_opportunity.match_score,
        "source_platform": db_opportunity.source_platform,
        "status": db_opportunity.status,
        "region": db_opportunity.region,
        "detected_date": db_opportunity.detected_date.isoformat() if db_opportunity.detected_date else None,
    }

@app.get("/api/signals")
async def get_signals():
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    # For simplicity, we'll return recent opportunities as signals
    signals = db.query(crm.Opportunity).order_by(crm.Opportunity.detected_date.desc()).limit(50).all()
    db.close()
    return [
        {
            "id": s.id,
            "company_id": s.company_id,
            "job_title": s.job_title,
            "matched_pod": s.matched_pod,
            "match_score": s.match_score,
            "source_platform": s.source_platform,
            "status": s.status,
            "region": s.region,
            "detected_date": s.detected_date.isoformat() if s.detected_date else None,
        }
        for s in signals
    ]

@app.get("/api/metrics")
async def get_metrics():
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    try:
        # Leads discovered: total opportunities
        leads_discovered = db.query(func.count(crm.Opportunity.id)).scalar() or 0
        # Enrichment rate: percentage of opportunities that have approved HITL
        total_opps = leads_discovered
        approved_hitl = db.query(func.count(crm.Hitl.id)).filter(crm.Hitl.status == "approved").scalar() or 0
        enrichment_rate = (approved_hitl / total_opps * 100) if total_opps > 0 else 0
        # Active signals: opportunities with status READY (or just total opportunities? We'll use READY)
        active_signals = db.query(func.count(crm.Opportunity.id)).filter(crm.Opportunity.status == "READY").scalar() or 0
        # Conversion probability: percentage of approved HITL that resulted in a meeting
        total_meetings = db.query(func.count(crm.Meeting.id)).scalar() or 0
        conversion_prob = (total_meetings / approved_hitl * 100) if approved_hitl > 0 else 0
        # For simplicity, trends are set to 0 (no change)
        metrics = {
            "leads_discovered": {"value": leads_discovered, "trend": 0},
            "enrichment_rate": {"value": round(enrichment_rate, 2), "trend": 0},
            "active_signals": {"value": active_signals, "trend": 0},
            "conversion_prob": {"value": round(conversion_prob, 2), "trend": 0}
        }
    finally:
        db.close()
    return metrics
@app.post("/hitl/generate")
async def hitl_generate(request: Request):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    company_id = payload.get("company_id")
    contact_id = payload.get("contact_id")
    if not company_id or not contact_id:
        raise HTTPException(status_code=400, detail="company_id and contact_id required")
    db = crm.SessionLocal()
    company = db.query(crm.Company).filter(crm.Company.id == company_id).first()
    contact = db.query(crm.Contact).filter(crm.Contact.id == contact_id).first()
    if not company or not contact:
        db.close()
        raise HTTPException(status_code=404, detail="Company or contact not found")
    # Generate a message using the LLM
    message_text = generate_message(company.name, contact.first_name, contact.last_name, contact.title or "")
    hitl = crm.Hitl(
        company_id=company_id,
        contact_id=contact_id,
        message_text=message_text,
        status="pending",
    )
    db.add(hitl)
    db.commit()
    db.refresh(hitl)
    db.close()
    return {
        "id": hitl.id,
        "company_id": hitl.company_id,
        "contact_id": hitl.contact_id,
        "message_text": hitl.message_text,
        "status": hitl.status,
        "created_at": hitl.created_at.isoformat() if hitl.created_at else None,
    }

@app.get("/hitl/pending")
async def hitl_pending():
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    hitls = db.query(crm.Hitl).filter(crm.Hitl.status == "pending").order_by(crm.Hitl.created_at.desc()).limit(50).all()
    db.close()
    return [
        {
            "id": h.id,
            "company_id": h.company_id,
            "contact_id": h.contact_id,
            "message_text": h.message_text,
            "status": h.status,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in hitls
    ]

@app.post("/hitl/approve/{hitl_id}")
async def hitl_approve(hitl_id: int):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    hitl = db.query(crm.Hitl).filter(crm.Hitl.id == hitl_id).first()
    if not hitl:
        db.close()
        raise HTTPException(status_code=404, detail="HITL not found")
    hitl.status = "approved"
    hitl.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.close()
    return {"status": "approved", "hitl_id": hitl_id}

@app.post("/hitl/reject/{hitl_id}")
async def hitl_reject(hitl_id: int):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    db = crm.SessionLocal()
    hitl = db.query(crm.Hitl).filter(crm.Hitl.id == hitl_id).first()
    if not hitl:
        db.close()
        raise HTTPException(status_code=404, detail="HITL not found")
    hitl.status = "rejected"
    db.commit()
    db.close()
    return {"status": "rejected", "hitl_id": hitl_id}

# ---------------------------------------------------------------------------
# HITL admin endpoints (dashboard queue) – /api prefix for the React dashboard
# ---------------------------------------------------------------------------
@app.get("/api/hitl/pending")
async def api_hitl_pending():
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Service unavailable"})
    db = crm.SessionLocal()
    hitls = (
        db.query(crm.Hitl)
        .filter(crm.Hitl.status == "pending")
        .order_by(crm.Hitl.created_at.desc())
        .limit(50)
        .all()
    )
    result = [
        {
            "id": h.id,
            "company_id": h.company_id,
            "contact_id": h.contact_id,
            "company_name": h.company.name if h.company else None,
            "contact_name": (
                f"{h.contact.first_name} {h.contact.last_name}"
                if h.contact
                else None
            ),
            "message_text": h.message_text,
            "status": h.status,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in hitls
    ]
    db.close()
    return result

@app.post("/api/hitl/approve/{hitl_id}")
async def api_hitl_approve(hitl_id: int):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Service unavailable"})
    db = crm.SessionLocal()
    hitl = db.query(crm.Hitl).filter(crm.Hitl.id == hitl_id).first()
    if not hitl:
        db.close()
        raise HTTPException(status_code=404, detail="HITL not found")
    hitl.status = "approved"
    hitl.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.close()
    return {"status": "approved", "hitl_id": hitl_id}

@app.post("/api/hitl/reject/{hitl_id}")
async def api_hitl_reject(hitl_id: int):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Service unavailable"})
    db = crm.SessionLocal()
    hitl = db.query(crm.Hitl).filter(crm.Hitl.id == hitl_id).first()
    if not hitl:
        db.close()
        raise HTTPException(status_code=404, detail="HITL not found")
    hitl.status = "rejected"
    db.commit()
    db.close()
    return {"status": "rejected", "hitl_id": hitl_id}

# ---------------------------------------------------------------------------
# Meeting booking endpoint
# ---------------------------------------------------------------------------
@app.post("/meeting/booked")
async def meeting_booked(request: Request):
    if not _db_available:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    hitl_id = payload.get("hitl_id")
    platform = payload.get("platform", "unknown")
    meet_url = payload.get("meet_url")
    notes = payload.get("notes")
    if not hitl_id:
        raise HTTPException(status_code=400, detail="hitl_id required")
    db = crm.SessionLocal()
    hitl = db.query(crm.Hitl).filter(crm.Hitl.id == hitl_id).first()
    if not hitl:
        db.close()
        raise HTTPException(status_code=404, detail="HITL not found")
    meeting = crm.Meeting(
        hitl_id=hitl_id,
        platform=platform,
        meet_url=meet_url,
        notes=notes,
    )
    db.add(meeting)
    # Optionally mark hitl as having a meeting? We'll keep status as approved.
    db.commit()
    db.close()
    return {"status": "meeting booked", "meeting_id": meeting.id}

# ---------------------------------------------------------------------------
# Deploy endpoint (to trigger a new discovery run)
# ---------------------------------------------------------------------------
@app.post("/api/deploy")
async def deploy(background_tasks: BackgroundTasks):
    # Trigger the discovery scheduler to run once
    background_tasks.add_task(run_discovery_once)
    return {"status": "deployment queued"}

# ---------------------------------------------------------------------------
# Additional endpoint to trigger enrichment manually (optional)
# ---------------------------------------------------------------------------
@app.post("/api/enrich")
async def enrich_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(lambda: logger.info("Manual enrichment trigger not implemented in this endpoint"))
    return {"status": "enrichment queued"}

# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return JSONResponse(status_code=404, content={"detail": "Not found"})

@app.exception_handler(500)
async def internal_error(request: Request, exc: HTTPException):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})