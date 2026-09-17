# Changelog

All notable changes to the Interceptor project will be documented in this file.

## [Unreleased] - 2026-09-13

### Added
- `project_snapshot.md` – added – Initial project overview and architecture understanding (Phase 1)
- `architecture/interceptor_overview.md` – added – Diagram linking the five business stages to Twenty CRM and Hermes (Phase 2)
- `architecture/README-Architecture.md` – added – Description of event flow and component responsibilities (Phase 2)
- `docker-compose.yml` – modified – Added Hermes service, updated Postgres to include hermes_db, and adjusted service dependencies (Phase 2)
- `hermes/__init__.py` – added – Hermes FastAPI application with event receipt and health check endpoints (Phase 3)
- `hermes/app.py` – added – Entrypoint exposing the Hermes FastAPI app (Phase 3)
- `tests/test_hermes.py` – added – Unit tests for Hermes health and event endpoints (Phase 3)
- `migrations/0001_initial.sql` – added – Initial database schema for companies, opportunities, contacts, enrichment, HITL, funnels, responses, bookings (Phase 4)
- `crl/crm.py` – added – SQLAlchemy ORM layer with CRUD functions for all entities (Phase 4)
- `tests/test_crl.py` – added – Unit tests for CRM ORM layer (Phase 4)
- `integrations/n8n/workflows/mining-trigger.yml` – added – n8n workflow to trigger enrichment on mining events (Phase 5)
- `integrations/enrich_apollo.py` – added – Stub for Apollo enrichment that writes to CRM (Phase 5)
- `integrations/enrich_linkedin.py` – added – Stub for LinkedIn enrichment that writes to CRM (Phase 5)
- `integrations/mautic_client.py` – added – Stub for Mautic email sequence dispatch (Phase 5)
- `integrations/twilio_webhook.py` – added – Stub for Twilio webhook that posts responses to Hermes (Phase 5)
- `integrations/calendly_client.py` – added – Stub for Calendly meeting creation (Phase 5)
- `frontend/placeholder/app.js` – added – Placeholder React frontend (Phase 5)
- `tests/test_integrations.py` – added – Unit tests for integration stubs (Phase 5)

### Modified
- `docker-compose.yml` – modified – Added Hermes service and updated Postgres to include hermes_db (Phase 2)

### Deleted
- None

## Todo
- Phase 6: Build AI / Agent layer (LLM wrapper, message generation, HITL worker)
- Phase 7: Build Front-end / Dashboard (Create-React-App, overview, HITL, funnels, booking pages)
- Phase 8: Build Workflows (n8n enrichment, funnel automation, booking workflows)
- Phase 9: Testing (unit, integration, e2e, coverage ≥80%)
- Phase 10: Deployment instructions (Docker, Makefile, env vars, install.md)

Note: The Hermes webhook subscription for n8n integration (crm-company-sync) was configured in the active Hermes profile (interceptor) and is not part of this repository's versioned files. It is configured via `hermes config set` commands and persists in the profile's config.yaml.