# Interceptor Platform Overview

**Links the five business stages to Twenty CRM and Hermes**

```
┌─────────────────────────────────────────────────────────────────┐
│                      INTERCEPTOR PLATFORM                       │
├─────────────────────┬─────────────────────┬───────────────────┤
│   MINING            │   ENRICHMENT        │   HITL            │
│  (Job Discovery)    │  (OSINT + APIs)     │  (Human Approval) │
│                     │                     │                 │
│     └───────┬───────┘                     └───────┬───────┘
│           ▼                                 ▼
│      JOB OPPORTUNITIES               MESSAGE CANDIDATES
│           │                                 │
│           ▼                                 ▼
│     AI MATCH                            HITL REVIEW
│           │                                 │
│           ▼                                 ▼
│     QUALIFIED OPPs                   APPROVED MESSAGES
└───────────────┴───────────────┴───────────────┘
              │                   │
              ▼                   ▼
     ┌─────────────────┐  ┌─────────────────┐
     │    FUNNELS      │  │    BOOKING      │
     │ (Email/Social/WA/VOIP) │  │ (Calendly)    │
     └───────┬─────────┘  └───────┬─────────┘
             ▼                   ▼
      PROSPECT RESPONSE    MEETING BOOKED
             │                   │
             ▼                   ▼
      OPPORTUNITY        CLIENT CONVERSION
```

---

## Five Business Stages

| Stage | Description | Key Outputs |
|---|---|---|
| **1. MINING** | Scrape regional job boards, career pages, OSINT for active job descriptions | `job_opportunities` table rows |
| **2. ENRICHMENT** | Enrich each opportunity with company data (firmographics, tech stack, funding), decision makers, hiring signals | `enrichment` JSONB, `contacts` (decision makers) |
| **3. HITL** | Present generated messages to human for review/approval | `hitl` table with `status='pending'` → `'approved'`/`'rejected'` |
| **4. FUNNELS** | Upon approval, dispatch multi-touch outbound via Mautic, Twilio SMS, WhatsApp, VOIP | Funnel campaigns, `responses` tracked |
| **5. BOOKING** | When prospect shows interest, schedule meeting via Calendly → opportunity becomes booked | `bookings` table, calendar IDs |

---

## Integration with Twenty CRM

| CRM Entity | Source | Purpose |
|---|---|---|
| **companies** | Extracted from job descriptions + enrichment | System of record for target companies |
| **opportunities** | Matched job descriptions + pod alignment | Tracks sales pipeline (DISCOVERED → QUALIFIED → PROSPECT_CREATED → CAMPAIGN_ACTIVE → CONVERTED) |
| **contacts/decision_makers** | Enrichment (Apollo/LinkedIn) | Verified emails, LinkedIn profiles, titles |
| **funnels** | Mautic campaign IDs + sequence configs | Outbound email/social/VOIP sequences |
| **bookings** | Calendly meeting links + slots | Calendar-integrated opportunity closure |
| **responses** | Inbound replies (email, WhatsApp, VOIP) | Sentiment + action flag |

---

## Hermes Integration Points

| Hermes Role | API Endpoint | Data Flow |
|---|---|---|
| **Job Discovery Agent** | `POST /event type: opportunity_created` | Receives raw job data → stores in Postgres |
| **Job Relevance Agent** | `POST /event type: relevance_scored` | Parses JD, computes match_score → updates opportunity |
| **Company Research Agent** | `POST /event type: company_researched` | Enrichment data → writes to CRM enrichment JSONB |
| **HITL Agent** | `POST /hitl/generate` | Generates message → stores pending → UI reviews |
| **Outreach Agent** | `POST /funnel/trigger` | Approved message → Mautic/Webhook → sends sequence |
| **Booking Agent** | `POST /booking/schedule` | Calendly slot → creates booking → updates opportunity status |

---

## Event Flow

```
1. MINING:     Job Discovery → POST /event type: opportunity_created
              │
              ▼
2. ENRICHMENT: Company Research Agent → POST /event type: company_researched
              │
              ▼
3. MATCH:      Job Relevance Agent → POST /event type: relevance_scored
              │
              ▼
4. HITL:       Message Generation → POST /hitl/generate → stores in hitl table
              │
              ▼ (human approves)
5. FUNNELS:    POST /funnel/trigger (after HITL approval) → Mautic / Twilio / WhatsApp
              │
              ▼
6. BOOKING:    Prospect responds → POST /booking/schedule → Calendly → opportunity status → 'booked'
```

---

## Responsibilities Summary

| Component | Responsibility |
|---|---|
| **Twenty CRM** | Core customer data, pipeline tracking, company profiles |
| **PostgreSQL** | Persistent storage for all entities (companies, opportunities, contacts, enrichment, hitl, funnels, responses, bookings) |
| **Redis** | Message queue for async workflow processing |
| **n8n** | Visual workflow orchestration (enrichment pipelines, funnel automation, booking flows) |
| **Hermes (AI)** | LLM-powered parsing, matching, message generation, HITL orchestration |
| **Enrichment APIs** (Apollo, LinkedIn) | Firmographic data, tech stack, decision maker info |
| **Mautic** | Email marketing campaigns & automation |
| **Twilio** | SMS & voice communications |
| **WhatsApp** | Messaging channel |
| **Calendly** | Meeting scheduling & calendar integration |
| **Frontend React** | Dashboard UI for HITL approval, funnel tracking, booking status |