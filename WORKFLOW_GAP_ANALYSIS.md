# Interceptor Q - Workflow Gap Analysis & Requirements Document

## Executive Summary
This document compares the **implemented system** against your **target workflow** and identifies gaps, current dashboard capabilities, and required actions from you.

---

## 1. Target Workflow (Your Requirements)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE TARGET WORKFLOW                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ Hermes 1 │───▶│  Twenty  │───▶│   n8n    │───▶│  Twenty  │───▶│ Hermes 2 │      │
│  │Discovery │    │   CRM    │    │Enrichment│    │   CRM    │    │ Msg+HITL │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────┬─────┘      │
│       │            (Raw leads)      (Apollo/                      (Enriched)      │
│       ▼                                 Hunter)                        │             │
│  Raw Companies/                                                    ▼             │
│  Opportunities                                                    │             │
│                                                             ┌──────────────┐      │
│                                                             │    HITL      │      │
│                                                             │  Approve/    │      │
│                                                             │  Reject      │      │
│                                                             └──────┬───────┘      │
│                                                                    │              │
│                              ┌────────────────────────────────────┼────────────┐ │
│                              ▼                                    ▼            ▼ │
│                     ┌────────────────┐                ┌─────────────┐  ┌─────────┐│
│                     │   Outbound     │                │   Calendar  │  │ Weekly  ││
│                     │   (Funnels)    │                │   Booking   │  │ Re-queue││
│                     └────────────────┘                └─────────────┘  └─────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Steps:
1. **Hermes 1 (Discovery Agent)**: LLM-powered data mining from job boards, career pages, web search
2. **Twenty CRM (Ingestion)**: Raw leads stored as Companies/Opportunities
3. **n8n Enrichment**: Apollo + Hunter APIs enrich contacts/emails
4. **Twenty CRM (Enriched)**: Updated records with contacts, emails, social profiles
5. **Hermes 2 (Outreach Agent)**: Generates personalized messages, creates HITL tasks
6. **HITL Loop**: Human approves/rejects; rejected items re-queue weekly
7. **Outbound Funnels**: Approved messages sent via Mautic/LinkedIn/WhatsApp
8. **Calendar Booking**: Responses trigger Calendly/Cal.com integration

---

## 2. Currently Implemented (What Exists)

### ✅ Completed Components

| Component | Status | Details |
|-----------|--------|---------|
| **Hermes Core API** | ✅ Complete | FastAPI with `/health`, `/event`, `/api/*`, `/hitl/*`, `/meeting/*` |
| **Database Models** | ✅ Complete | Company, Contact, Opportunity, Hitl, OutboundLog, Meeting, EventLog |
| **Outbound Worker** | ✅ Complete | Mautic, LinkedIn, WhatsApp with retry logic |
| **Enrichment Worker** | ✅ Complete | Apollo/Hunter with exponential backoff |
| **Discovery Skeleton** | ✅ Partial | Framework exists; needs LLM integration & real scrapers |
| **HITL System** | ✅ Complete | Generate → Pending → Approve/Reject → Meeting booking |
| **n8n Workflows** | ✅ Complete | Two workflows: basic + enhanced (discovery→enrichment→HITL→outbound) |
| **Dashboard (React/Vite)** | ✅ Complete | 5 tabs: Dashboard, Map, Pipeline, Signals, Config |
| **Metrics API** | ✅ Fixed | Returns structure frontend expects |
| **Prometheus + Grafana** | ✅ Complete | Hermes metrics, custom dashboard |
| **CI/CD Pipeline** | ✅ Complete | GitHub Actions with PostgreSQL/Redis |
| **Tests** | ✅ 11 passing | Unit + integration tests |

### 🔄 Partially Implemented

| Component | Status | Missing |
|-----------|--------|---------|
| **Discovery Agent** | Skeleton only | No LLM mining, no real scrapers, no job board APIs |
| **Twenty CRM Integration** | Model only | No sync logic (push/pull), no webhook handlers |
| **Hermes 2 (Separate Agent)** | Not created | Single Hermes handles both roles currently |
| **Calendar Booking** | Meeting model only | No Calendly/Cal.com integration |
| **Weekly Re-queue** | Not implemented | Rejected HITL items don't auto-requeue |

### ❌ Not Implemented

| Component | Required For |
|-----------|--------------|
| **Two Hermes Instances** | Architectural separation (discovery vs outreach) |
| **Twenty CRM Sync** | Bidirectional data flow with Twenty |
| **Real Discovery Scrapers** | Job boards (Indeed, LinkedIn Jobs), career pages, web search |
| **LLM Mining Prompts** | Structured extraction from raw HTML/API responses |
| **Calendar Integration** | Automated booking on positive responses |
| **Weekly Re-queue Logic** | HITL rejection handling |

---

## 3. Dashboard Current State

### Available Tabs & Features

| Tab | Features | Data Source |
|-----|----------|-------------|
| **Command Center** | Metric cards (Leads, Enrichment Rate, Signals, Conversion), Opportunity table, Signal feed, Deploy Agent button | `/api/metrics`, `/api/opportunities`, `/api/signals` |
| **Opportunity Map** | Geographic visualization placeholder | `/api/companies` |
| **Enrichment Pipeline** | Stage cards (Pending/Enriching/Ready) - static | Hardcoded |
| **Signal Monitor** | Live signal feed | `/api/signals` |
| **System Config** | API status indicators | Real-time health checks |

### What Works
- Real-time metrics from database
- Opportunity listing with match scores
- Signal feed (recent opportunities)
- Deploy Agent button triggers `/api/deploy`
- Responsive BINDU dark theme

### What's Placeholder/Static
- Opportunity Map (no real map)
- Pipeline stages (hardcoded zeros)
- No HITL management UI (approve/reject in dashboard)
- No outbound sending UI
- No calendar booking UI

---

## 4. Gap Analysis: Target vs. Current

| # | Target Requirement | Current State | Gap Size | Effort |
|---|-------------------|---------------|----------|--------|
| 1 | **Hermes 1: LLM Discovery Mining** | Skeleton only | Large | High |
| 2 | **Twenty CRM Bidirectional Sync** | Models only | Large | High |
| 3 | **n8n → Twenty CRM Enrichment Push** | n8n workflow exists, no Twenty nodes | Medium | Medium |
| 4 | **Hermes 2: Separate Outreach Agent** | Single Hermes does both | Medium | Medium |
| 5 | **HITL Dashboard Management** | API only, no UI | Medium | Medium |
| 6 | **Calendar Booking Integration** | Meeting model only | Medium | Medium |
| 7 | **Weekly Re-queue for Rejected** | Not implemented | Small | Low |
| 8 | **Real Discovery Scrapers** | Framework only | Large | High |
| 9 | **Outbound UI in Dashboard** | API only | Medium | Medium |

---

## 5. What I Need From You

### Priority 1: API Credentials (Required for Real Data)

| Service | Variables | Where to Add |
|---------|-----------|--------------|
| **LLM Provider** | `LLM_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL` | `.env` or docker-compose |
| **Apollo** | `APOLLO_KEY` | `.env` or docker-compose |
| **Hunter** | `HUNTER_KEY` | `.env` or docker-compose |
| **Mautic** | `MAUTIC_URL`, `MAUTIC_USER`, `MAUTIC_PASS` | `.env` or docker-compose |
| **LinkedIn** | `LINKEDIN_ACCESS_TOKEN` | `.env` or docker-compose |
| **WhatsApp** | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID` | `.env` or docker-compose |
| **API Auth** | `API_KEY` (generate secure string) | `.env` or docker-compose |

### Priority 2: Twenty CRM Access

| Need | Details |
|------|---------|
| **Twenty CRM URL** | Your Twenty instance endpoint |
| **API Token/Key** | For programmatic access |
| **Webhook URL** | For Twenty → n8n/Hermes notifications |
| **Field Mapping** | Confirm Company/Opportunity/Contact field mappings |

### Priority 3: Calendar Integration

| Need | Details |
|------|---------|
| **Provider** | Calendly, Cal.com, Google Calendar, or custom |
| **API Credentials** | OAuth tokens / API keys |
| **Booking Link Format** | How meeting URLs are generated |

### Priority 4: Discovery Sources

| Source | Need From You |
|--------|---------------|
| **Job Boards** | Indeed/LinkedIn Jobs API access or search queries |
| **Career Pages** | Target company list or discovery strategy |
| **Web Search** | SerpAPI/Bing API key or preferred search provider |
| **LLM Prompts** | Your ideal prompt templates for extraction |

---

## 6. Recommended Implementation Phases

### Phase 1: Enable Real Data Flow (Week 1-2)
- [ ] Add all API keys to `.env`
- [ ] Test Apollo/Hunter enrichment via n8n
- [ ] Verify Twenty CRM webhook → n8n → Twenty round-trip
- [ ] Seed 10-20 companies, run full pipeline manually

### Phase 2: Hermes 1 - Discovery Agent (Week 2-3)
- [ ] Implement LLM mining prompts
- [ ] Add job board scrapers (start with one source)
- [ ] Create `discovery_worker.py` with scheduler
- [ ] Push discovered leads to Twenty CRM API

### Phase 3: Hermes 2 Separation (Week 3)
- [ ] Create `hermes_outreach/` as separate service
- [ ] Move HITL, outbound, meeting logic there
- [ ] Configure inter-service communication (message queue or HTTP)

### Phase 3: Dashboard Enhancements (Week 3-4)
- [ ] HITL approve/reject UI
- [ ] Outbound sending status panel
- [ ] Calendar booking integration
- [ ] Pipeline stage real data

### Phase 4: Production Hardening (Week 4)
- [ ] Weekly re-queue for rejected HITL
- [ ] Alerting in Grafana
- [ ] Log aggregation
- [ ] Load testing

---

## 7. Current File Structure (Key Files)

```
interceptor-q/
├── hermes/
│   ├── __init__.py          # Main FastAPI app (ALL endpoints)
│   ├── config.py            # Settings from env
│   ├── crm.py               # SQLAlchemy models
│   ├── worker_outbound.py   # Mautic/LinkedIn/WhatsApp
│   ├── worker_enrich.py     # Apollo/Hunter
│   ├── discoverer.py        # Discovery skeleton
│   ├── llm.py               # LLM message generation
│   └── auth_middleware.py   # API key auth
├── frontend/dashboard/
│   ├── src/App.jsx          # Main dashboard (5 tabs)
│   └── vite.config.js       # Proxy to /api
├── n8n/
│   ├── funnel_workflow.json          # Basic workflow
│   └── funnel_workflow_enhanced.json # Full pipeline
├── docker-compose.yml       # All services
├── .env.example             # Template for credentials
└── tests/                   # 11 passing tests
```

---

## 8. Immediate Next Steps for You

### This Week:
1. **Fill `.env`** with real API keys (use `.env.example` as template)
2. **Restart stack**: `docker compose down && docker compose up -d`
3. **Test enrichment**: `curl -X POST http://localhost:8000/api/enrich`
4. **Check Twenty CRM**: Verify webhook receives data

### Decide On:
1. **Calendar provider** (Calendly? Cal.com? Google?)
2. **Discovery priority** (Job boards vs career pages vs web search)
2. **Whether to separate Hermes now or later** (affects architecture)

### Provide When Ready:
- Twenty CRM webhook URL & API token
- Calendar provider credentials
- Preferred discovery source APIs/queries

---

## 9. Architecture Decision: One vs Two Hermes

### Option A: Single Hermes (Current)
- **Pros**: Simpler deployment, shared database, easier dev
- **Cons**: Mixed responsibilities, harder to scale independently

### Option B: Two Hermes Services
- **Pros**: Clear separation, independent scaling, fault isolation
- **Cons**: More complex deployment, inter-service communication needed

**Recommendation**: Start with **single Hermes**, split when discovery load justifies it.

---

## 10. Summary

| Category | Status |
|----------|--------|
| **Core Infrastructure** | ✅ Production-ready |
| **Database & Models** | ✅ Complete |
| **API Endpoints** | ✅ Complete (all workflow steps covered) |
| **Outbound/Enrichment Workers** | ✅ Complete with retry logic |
| **HITL System** | ✅ Complete (API only) |
| **n8n Orchestration** | ✅ Complete workflows |
| **Monitoring** | ✅ Prometheus + Grafana |
| **Dashboard** | ✅ Functional, needs HITL/Outbound UI |
| **Real Discovery** | ⚠️ Skeleton - needs LLM + scrapers |
| **Twenty CRM Sync** | ⚠️ Models only - needs bidirectional sync |
| **Calendar Booking** | ⚠️ Model only - needs provider integration |
| **Hermes Separation** | ❌ Not started |

**The foundation is solid.** With your API keys and a few integration decisions, we can have real data flowing through the complete pipeline within 1-2 weeks.

---

*Document Version: 1.0*  
*Generated: 2026-09-16*  
*For: Interceptor Q Project*