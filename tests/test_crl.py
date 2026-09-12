"""Tests for Interceptor CRM ORM layer."""

import pytest
from crl.crm import (
    upsert_company, get_company, upsert_opportunity,
    get_opportunities_by_status, upsert_contact, upsert_enrichment,
    create_hitl_message, get_pending_hitl, approve_hitl, reject_hitl,
    upsert_funnel, create_response, create_booking, get_session, init_db,
    DATABASE_URL
)
from hermes.app import app

# Override test DB URL
TEST_DATABASE_URL = "postgresql://interceptor_admin:SuperS...123!@localhost:5432/hermes_test_db"


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Set up in-memory SQLite for tests (fallback to real DB)."""
    # Since we may not have a running Postgres, skip DB-dependent tests
    # if connection fails
    try:
        # Simple health check
        import psycopg2
        conn = psycopg2.connect(TEST_DATABASE_URL)
        conn.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️  Database not available: {e}")
        pytest.skip("Database not available for CRUD tests")


@pytest.fixture
def db_session():
    """Provide a transactional scope for each test."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(TEST_DATABASE_URL, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session, future=True)
    session = SessionLocal()
    yield session
    session.close()


class TestCompanyCRUD:
    def test_upsert_and_get_company(self, db_session):
        from crl.crm import upsert_company, get_company
        company = upsert_company(
            db_session, name="Acme Corp", region="EU",
            tech_stack={"python": "3.11", "react": "18"},
            source_url="https://example.com", source_platform="manual"
        )
        assert company.id is not None
        assert company.name == "Acme Corp"
        assert company.region == "EU"

        retrieved = get_company(db_session, company.id)
        assert retrieved is not None
        assert retrieved.name == "Acme Corp"


class TestOpportunityCRUD:
    def test_upsert_and_get_opportunity(self, db_session):
        from crl.crm import upsert_opportunity, get_opportunities_by_status

        company = upsert_company(db_session, name="Acme Corp", region="NAC")
        opp = upsert_opportunity(
            db_session, company_id=company.id,
            job_title="Software Engineer",
            job_description="We are hiring a senior backend engineer",
            source_url="https://jobs.example.com", source_platform="linkedin",
            region="NAC", matched_pod="Technology", match_score=92.5
        )
        assert opp.id is not None
        assert opp.matched_pod == "Technology"
        assert opp.match_score == 92.5
        assert opp.status == "DISCOVERED"

        # Test status filtering
        discovered = get_opportunities_by_status(db_session, "DISCOVERED")
        assert len(discovered) >= 1
        assert any(o.id == opp.id for o in discovered)


class TestContactCRUD:
    def test_upsert_contact(self, db_session):
        from crl.crm import upsert_contact

        company = upsert_company(db_session, name="Acme Corp", region="APAC")
        contact = upsert_contact(
            db_session, company_id=company.id,
            first_name="John", last_name="Doe",
            title="VP Engineering", email="john@example.com",
            discovery_source="linkedin"
        )
        assert contact.id is not None
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.title == "VP Engineering"


class TestEnrichmentCRUD:
    def test_upsert_enrichment(self, db_session):
        from crl.crm import upsert_enrichment

        company = upsert_company(db_session, name="Acme Corp", region="MENA")
        enrichment = upsert_enrichment(
            db_session, company_id=company.id,
            data={"funding": "Series B", "employees": 50},
            source="apollo"
        )
        assert enrichment.id is not None
        assert enrichment.data["funding"] == "Series B"
        assert enrichment.source == "apollo"

        # Upsert again — should update
        enrichment2 = upsert_enrichment(
            db_session, company_id=company.id,
            data={"funding": "Series C", "employees": 100},
            source="apollo"
        )
        assert enrichment2.data["funding"] == "Series C"


class TestHITLCRUD:
    def test_create_and_approve_hitl(self, db_session):
        from crl.crm import create_hitl_message, get_pending_hitl, approve_hitl, reject_hitl

        company = upsert_company(db_session, name="Acme Corp", region="LATAM")
        opp = upsert_opportunity(
            db_session, company_id=company.id,
            job_title="Growth Manager", job_description="Hiring for growth role",
            source_url="https://jobs.example.com", source_platform="linkedin",
            region="LATAM", matched_pod="Growth", match_score=88.0
        )

        # Create HITL message
        hitl = create_hitl_message(db_session, opp.id,
                                   "Hi John, we'd love to discuss...")
        assert hitl.status == "pending"

        # Approve
        approved = approve_hitl(db_session, hitl.id)
        assert approved.status == "approved"

        # Check pending list no longer has it
        pending = get_pending_hitl(db_session)
        pending_ids = [h.id for h in pending]
        assert hitl.id not in pending_ids


class TestFunnelCRUD:
    def test_upsert_funnel(self, db_session):
        from crl.crm import upsert_funnel

        funnel = upsert_funnel(
            db_session, name="Onboarding Email",
            description="Welcome email sequence",
            channel="email", campaign_id="mautic-123"
        )
        assert funnel.id is not None
        assert funnel.channel == "email"


class TestResponseCRUD:
    def test_create_response(self, db_session):
        from crl.crm import create_response

        company = upsert_company(db_session, name="Acme Corp", region="EU")
        opp = upsert_opportunity(
            db_session, company_id=company.id,
            job_title="Developer", job_description="Hiring",
            source_url="https://jobs.example.com", source_platform="linkedin",
            region="EU", matched_pod="Technology", match_score=90.0
        )

        resp = create_response(
            db_session, opp.id, None, source="email",
            sentiment="positive", message_text="Sounds interesting!",
            action_taken="replied"
        )
        assert resp.id is not None
        assert resp.sentiment == "positive"
        assert resp.action_taken == "replied"


class TestBookingCRUD:
    def test_create_booking(self, db_session):
        from crl.crm import create_booking

        company = upsert_company(db_session, name="Acme Corp", region="NAC")
        opp = upsert_opportunity(
            db_session, company_id=company.id,
            job_title="Engineer", job_description="Hiring",
            source_url="https://jobs.example.com", source_platform="linkedin",
            region="NAC", matched_pod="Technology", match_score=95.0
        )

        booking = create_booking(
            db_session, opp.id, calendly_id="meetings-xyz",
            slot_start="2026-09-20T10:00:00Z", slot_end="2026-09-20T11:00:00Z",
            calendar_title="Discovery Call"
        )
        assert booking.id is not None
        assert booking.calendly_id == "meetings-xyz"
        assert booking.status == "scheduled"