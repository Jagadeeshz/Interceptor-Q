# Interceptor Architecture — README

## Event Flow & Component Responsibilities

### Overview

Interceptor is an autonomous opportunity-discovery and sales intelligence platform that:
1. **Scans** public job and business signals across target regions
2. **Matches** hiring needs against Quantocos pod capabilities
3. **Researches** hiring companies and identifies decision makers
4. **Qualifies** opportunities via AI-assisted scoring
5. **Supports** personalized outreach through human-approved sales funnels

### Event-Driven Architecture

All system components communicate via **Hermes webhook events** posted to `POST /event`. Each event carries a `type` field that dictates the downstream processing path.

### Event Types & Flow

| Event Type | Source | Processing | Next Event |
|---|---|---|---|
| `opportunity_created` | Hermes Job Discovery Agent | Parse JD, store in `job_opportunities` | `relevance_scored` |
| `relevance_scored` | Hermes Job Relevance Agent | Compute match_score against Quantocos pods | `company_researched` |
| `company_researched` | Hermes Company Research Agent | Enrich via Apollo/LinkedIn, write JSONB | `hitl_generated` |
| `hitl_generated` | Hermes Message Generator | Create message draft, store in `hitl` table | `hitl_approved` / `hitl_rejected` |
| `hitl_approved` | Human reviewer (frontend UI) | Approve message → trigger funnel | `funnel_triggered` |
| `hitl_rejected` | Human reviewer (frontend UI) | Discard → loop back to `hitl_generated` | (repeat) |
| `funnel_triggered` | n8n workflow | Dispatch Mautic email / Twilio SMS / WhatsApp | `response_received` |
| `response_received` | Twilio / Mautic webhook | Parse inbound reply, update sentiment | `booking_scheduled` / `opportunity_closed` |
| `booking_scheduled` | Calendly integration | Schedule meeting, update opportunity status | `client_converted` |
| `client_converted` | Opportunity closure | Mark won/lost, close loop | — |

### Component Responsibilities

| Component | Files / Directories | Key Responsibilities |
|---|---|---|
| **Hermes (Python/FastAPI)** | `hermes/` | Receive `/event` POSTs, dispatches to AI agents, manages HITL state in Postgres |
| **PostgreSQL** | `docker-compose.yml` → `db` service | Persistent storage for all schema tables (see migrations) |
| **Redis** | `docker-compose.yml` → `redis` service | Queue for async workflow processing (n8n, background workers) |
| **n8n** | `workflows/` | Visual automation: enrichment pipelines, funnel dispatch, booking triggers |
| **Twenty CRM** | `twenty_server` container | Core CRM system (exposed on port 3000), stores companies/opportunities/contacts |
| **Enrichment APIs** | `integrations/enrich_*.py` | Apollo, LinkedIn firmographic data → Postgres JSONB |
| **Mautic** | `integrations/mautic_client.py` | Email campaign dispatch, open/click tracking |
| **Twilio** | `integrations/twilio_webhook.py` | SMS inbound/outbound, status callbacks |
| **Calendly** | `integrations/calendly_client.py` | Meeting slot creation, calendar sync |
| **Frontend (React)** | `frontend/` | Dashboard: overview, HITL approval queue, funnel tracker, booking status |
| **DNS/Domains** | `.env` → `DOMAIN_TWENTY`, `DOMAIN_N8N` | Public-facing URLs for all services |

### Diagrams

#### High-Level Data Flow

```
Job Boards & OSINT
     │
     ▼
  Hermes (Job Discovery)
     │  POST /event type: opportunity_created
     ▼
  Postgres (job_opportunities)
     │
     ▼
  Hermes (Job Relevance)
     │  POST /event type: relevance_scored
     ▼
  Postgres (updates match_score, matched_pod)
     │
     ▼
  Hermes (Company Research)
     │  POST /event type: company_researched
     ▼
  Postgres (enrichment JSONB, contacts)
     │
     ▼
  Hermes (Message Generation)
     │  POST /hitl/generate
     ▼
  hitl table (status=pending)
     │  (human approves via UI)
     ▼
  Hermes (Funnel Trigger)
     │  POST /funnel/trigger
     ▼
  n8n → Mautic/Twilio/WhatsApp
     │
     ▼
  Prospect Response
     │
     ▼
  n8n → Calendly
     │
     ▼
  Postgres (bookings, responses)
     │
     ▼
  Opportunity → Converted / Closed
```

#### Service Dependencies

```
┌─────────────┐      ┌─────────────────────┐
│   Frontend  │      │    Hermes (API)    │
│  (React 3000)│◀────▶│   (Python 8000)    │
└──────┬──────┘      └───────┬─────────────┘
       │                │
       │                ▼
       │           ┌─────────────────────┐
       └──────────▶│  PostgreSQL (db)      │
                   │  (all schema tables)│
                   └───────┬─────────────┘
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │ (queue/async)│
                    └─────────────┘
                           ▲
                           │
                    ┌─────────────┐
                    │    n8n      │
                    │ (workflows) │
                    └─────────────┘
                           ▲
                           │
                    ┌─────────────┐
                    │Enrichment APIs│
                    │(Apollo, LI)   │
                    └─────────────┘
                           ▲
                           │
                    ┌─────────────┐
                    │  Twenty CRM │
                    │   (port 3000)│
                    └─────────────┘
```

### Quantocos Pod Mapping

| Pod | Primary Keywords/Job Titles | Secondary Signals |
|---|---|---|
| **Technology** | Developer, Engineer, QA, DevOps, Data, Cloud, Solutions Architect | React, Node.js, Python, AWS, Kubernetes, Scalability issues |
| **Marketing** | Marketing Manager, Digital Marketing, SEO, Content, Brand | Campaign scaling, Rebranding, Performance Marketing |
| **Sales** | Sales Manager, SDR, BDR, Account Executive, VP Sales | CRM migration, Pipeline growth, Enterprise sales push |
| **Growth** | Growth Manager, Growth Marketing, Performance, Conversion | Funnel optimization, User acquisition, Retention |
| **Design** | UI/UX, Product Designer, Graphic Designer, Design Lead | Design system creation, Product redesign, Figma |
| **Strategy** | Strategy Consultant, Business Analyst, Strategy Manager | Market expansion, M&A support, Operations overhaul |

### Development Phases (Roadmap)

| Phase | Deliverable |
|---|---|
| 1 | Project snapshot & architecture overview ✅ |
| 2 | Architecture files & updated docker-compose.yml |
| 3 | Hermes Python package (FastAPI, config, tests) |
| 4 | Database schema migrations + SQLAlchemy ORM |
| 5 | Integration stubs (n8n, Apollo, LinkedIn, Mautic, Twilio, Calendly) |
| 6 | AI/LLM layer (prompt engineering, message generation, HITL) |
| 7 | Front-end React dashboard (overview, HITL, funnels, booking) |
| 8 | n8n workflows (enrichment, funnel automation, booking) |
| 9 | Testing (unit, integration, e2e coverage ≥80%) |
| 10 | Deployment docs (Docker, Makefile, env vars) |