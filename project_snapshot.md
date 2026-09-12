# Project Snapshot — Interceptor System

**Created:** Phase 1 — Understand the Project  
**Repository:** `C:\Users\jagad\OneDrive\Desktop\interceptor Q`

---

## 1. Architecture Diagram

The existing architecture is illustrated in `total running flow.png` (attached context) which shows the end-to-end workflow:

```
Job Description ──> Service Match (Quantocos Pod) ──> Identify Company ──> Research & Qualify
                                         │                    │
                                         ▼                    ▼
                                    Twenty CRM          AI Classification
                                         │                    │
                                         ▼                    ▼
                               Message Draft          HITL (Human-in-the-Loop)
                                         │
                                         ▼
                                          Funnels
                                   (Email / Social / WhatsApp / VOIP)
                                         │
                                         ▼
                                  Prospect Response
                                         │
                                         ▼
                                          Booking
                                         │
                                         ▼
                                  Sales Pitch
                                         │
                                         ▼
                                   Opportunity
                                         │
                                         ▼
                                  Client
```

**Key components visible in the diagram:**

| Stage | Description |
|---|---|
| **MINING** | OSINT job search across regions (APAC, MENA, EU, NAC, LATAM) |
| **ENRICHMENT** | Company research via Apollo/LinkedIn, decision maker discovery |
| **HITL** | Human approval queue for generated messages |
| **FUNNELS** | Multi-touch outbound: Mautic email, social, WhatsApp, VOIP |
| **BOOKING** | Calendar scheduling via Calendly |
| **SALES** | Opportunity creation & client conversion |

---

## 2. Modules & Responsibilities

| Module | File(s) | Responsibility |
|---|---|---|
| **Twenty CRM** | `Interceptor/`, `docker-compose.yml` | Core CRM system (exposed via `twenty_server` & `twenty_worker` containers) |
| **Database** | `docker-compose.yml`, `.env` | Postgres (twenty_db, n8n_db) + Redis (queue) |
| **n8n** | `docker-compose.yml` | Workflow automation (Node-based) |
| **Hermes AI** | Not yet in repo | Agentic system for parsing, matching, generation |
| **Enrichment** | Not yet in repo | Apollo + LinkedIn API integration |
| **Funnels** | Not yet in repo | Mautic / Twilio / WhatsApp / VOIP outbound |
| **Calendly** | Not yet in repo | Meeting booking orchestration |
| **Frontend** | `total running flow.png` | React dashboard (mockup in architecture diagram) |
| **Config** | `.env` | Environment variables for all services |

---

## 3. Integration Points

| Integration | Direction | Details |
|---|---|---|
| **n8n → Twenty CRM** | n8n writes to Postgres via Docker volume | n8n_db mapped to Postgres |
| **Twenty CRM → Hermes** | Webhook / POST | Not yet implemented — `docker-compose.yml` has `twenty_server` on port 3000 |
| **Hermes → n8n** | Hermes webhook → n8n trigger | Not yet implemented |
| **Enrichment APIs → CRM** | External (Apollo, LinkedIn) → Postgres | Not yet in repo |
| **Funnels → CRM** | Mautic / Twilio / Calendly → Postgres | Not yet in repo |
| **Frontend → Backend** | React → FastAPI/Flask | Not yet in repo |

---

## 4. Current Functionality (Assumed Working)

Based on repo inspection:

- ✅ **Docker Comfile** — `docker-compose.yml` defines 5 services: postgres, redis, twenty_server, twenty_worker, n8n
- ✅ **Environment config** — `.env` has all required keys (POSTGRES_USER, encryption keys, timezones)
- ✅ **Twenty CRM** — Official image `twentycrm/twenty:latest` running on port 3000
- ✅ **Init script** — `init-multiple-dbs.sh` creates multiple databases
- ✅ **Git repo** — Initial commit in `Interceptor/` directory (empty, just .git scaffolding)
- ✅ **Architecture visual** — `20crm & n8n.png` provides high-level workflow diagram

**Not yet implemented in repo:**
- Hermes AI agent core
- Database schema migrations
- n8n workflow definitions
- Enrichment integrations (Apollo/LinkedIn)
- Funnel/Mautic/Twilio/Calendly clients
- Frontend React application
- API endpoints or webhook handlers

---

## 5. Next Steps (Phase 2 onward)

See the phase specification in the prompt. The immediate task is to:

1. Create `project_snapshot.md` ✅ (done)
2. Add architecture files (`interceptor_overview.md`, `README-Architecture.md`, updated `docker-compose.yml`)
3. Build Hermes Python package with FastAPI
4. Create database migrations & ORM
5. Build integration stubs
6. ... and follow the 10-phase plan