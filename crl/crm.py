"""Interceptor CRM — SQLAlchemy ORM layer.

Provides CRUD functions for companies, opportunities, contacts,
enrichment, HITL, funnels, responses, and bookings.
"""

from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Boolean, inspect
from sqlalchemy.orm import declarative_base, Session, relationship
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
import uuid

# ---------------------------------------------------------------------------
# Engine & Base
# ---------------------------------------------------------------------------
DATABASE_URL = "postgresql://interceptor_admin:SuperS...123!@localhost:5432/hermes_db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
metadata = MetaData()

Base = declarative_base()  # type: ignore


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    region = Column(String(50), nullable=False)  # APAC, MENA, EU, NAC, LATAM
    tech_stack = Column(JSON, default={})
    funding_stage = Column(String(50))
    company_size = Column(String(50))
    source_url = Column(Text)
    source_platform = Column(String(100))
    detected_date = Column(DateTime(timezone=True), server_default=func.now())
    last_enriched = Column(DateTime(timezone=True))

    opportunities = relationship("Opportunity", back_populates="company", cascade="all, delete-orphan")
    enrichment = relationship("Enrichment", back_populates="company", uselist=False, cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    source_platform = Column(String(100))
    region = Column(String(50), nullable=False)  # APAC, MENA, EU, NAC, LATAM
    posted_date = Column(DateTime(timezone=True))
    detected_date = Column(DateTime(timezone=True), server_default=func.now())
    matched_pod = Column(String(100), nullable=False)
    match_score = Column(Float, nullable=False)  # 0–100
    hiring_signal_summary = Column(Text)
    status = Column(String(50), nullable=False, default="DISCOVERED")
    enrichment_jsonb = Column(JSON, default={})

    company = relationship("Company", back_populates="opportunities")
    responses = relationship("Response", back_populates="opportunity", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="opportunity", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(150))
    email = Column(String(255))
    linkedin_url = Column(Text)
    phone = Column(String(50))
    relevance_score = Column(Float, default=0)
    discovery_source = Column(String(100))  # apollo, linkedin, manual
    discovered_date = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="contacts")


class Enrichment(Base):
    __tablename__ = "enrichment"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, unique=True)
    data = Column(JSON, nullable=False, default={})
    enriched_date = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(100), nullable=False)  # apollo, linkedin, manual

    company = relationship("Company", back_populates="enrichment")


class Hitl(Base):
    __tablename__ = "hitl"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="SET NULL"))
    message_text = Column(Text, nullable=False)
    generated_by = Column(String(100), nullable=False)  # hermes_outreach_agent etc.
    status = Column(String(50), nullable=False, default="pending")
    approved_by = Column(String(100))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="hitl_entries")  # we'll add later


# Add back_populates for Hitl opportunity after definition
Hitl.opportunity = relationship("Opportunity", back_populates="hitl_entries")  # type: ignore


class Funnel(Base):
    __tablename__ = "funnels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    campaign_id = Column(String(255))  # Mautic campaign ID
    channel = Column(String(50), nullable=False)  # email, sms, whatsapp, voip
    sequence_json = Column(JSON, default=[])
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Response(Base):
    __tablename__ = "responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="SET NULL"))
    contact_id = Column(String(36), ForeignKey("contacts.id", ondelete="SET NULL"))
    source = Column(String(50), nullable=False)  # email, sms, whatsapp, voip
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    sentiment = Column(String(50), nullable=False, default="neutral")
    message_text = Column(Text)
    action_taken = Column(String(100))  # booked, replied, qualified, closed
    status = Column(String(50), nullable=False, default="open")

    opportunity = relationship("Opportunity", back_populates="responses")
    contact = relationship("Contact", back_populates="responses")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="SET NULL"))
    contact_id = Column(String(36), ForeignKey("contacts.id", ondelete="SET NULL"))
    calendly_id = Column(String(255))
    slot_start = Column(DateTime(timezone=True))
    slot_end = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False, default="scheduled")
    calendar_title = Column(String(255))
    calendar_description = Column(Text)
    booked_at = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="bookings")
    contact = relationship("Contact", back_populates="bookings")


# ---------------------------------------------------------------------------
# Helper: create tables
# ---------------------------------------------------------------------------
def init_db():
    """Create all tables defined above in the target database."""
    Base.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Session helper
# ---------------------------------------------------------------------------
def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine, class_=Session, future=True)
    return SessionLocal()


# ---------------------------------------------------------------------------
# CRUD functions
# ---------------------------------------------------------------------------

# --- Companies ---

def upsert_company(session: Session, name: str, domain: Optional[str] = None,
                   region: str = "APAC", tech_stack: Optional[Dict] = None,
                   funding_stage: Optional[str] = None, company_size: Optional[str] = None,
                   source_url: Optional[str] = None, source_platform: Optional[str] = None) -> Company:
    """Insert or update a company; return the Company instance."""
    tech_stack = tech_stack or {}
    company = session.query(Company).filter_by(name=name).first()
    if company:
        company.domain = domain
        company.region = region
        company.tech_stack = tech_stack
        company.funding_stage = funding_stage
        company.company_size = company_size
        company.source_url = source_url
        company.source_platform = source_platform
        company.last_enriched = func.now()
    else:
        company = Company(
            id=str(uuid.uuid4()),
            name=name,
            domain=domain,
            region=region,
            tech_stack=tech_stack,
            funding_stage=funding_stage,
            company_size=company_size,
            source_url=source_url,
            source_platform=source_platform,
        )
        session.add(company)
    session.commit()
    session.refresh(company)
    return company


def get_company(session: Session, company_id: str) -> Optional[Company]:
    return session.query(Company).get(company_id)


# --- Opportunities ---

def upsert_opportunity(session: Session, company_id: str, job_title: str,
                       job_description: str, source_url: str,
                       source_platform: str, region: str,
                       matched_pod: str, match_score: float,
                       hiring_signal_summary: Optional[str] = None,
                       status: str = "DISCOVERED") -> Opportunity:
    """Insert or update an opportunity; return the Opportunity instance."""
    opp = session.query(Opportunity).filter_by(company_id=company_id, job_title=job_title).first()
    if opp:
        opp.job_description = job_description
        opp.source_url = source_url
        opp.source_platform = source_platform
        opp.region = region
        opp.matched_pod = matched_pod
        opp.match_score = match_score
        opp.hiring_signal_summary = hiring_signal_summary
        opp.status = status
    else:
        opp = Opportunity(
            id=str(uuid.uuid4()),
            company_id=company_id,
            job_title=job_title,
            job_description=job_description,
            source_url=source_url,
            source_platform=source_platform,
            region=region,
            matched_pod=matched_pod,
            match_score=match_score,
            hiring_signal_summary=hiring_signal_summary,
            status=status,
        )
        session.add(opp)
    session.commit()
    session.refresh(opp)
    return opp


def get_opportunities_by_status(session: Session, status: str) -> List[Opportunity]:
    return session.query(Opportunity).filter(Opportunity.status == status).all()


# --- Contacts ---

def upsert_contact(session: Session, company_id: str, first_name: str,
                   last_name: str, title: Optional[str] = None,
                   email: Optional[str] = None, linkedin_url: Optional[str] = None,
                   phone: Optional[str] = None, discovery_source: str = "manual") -> Contact:
    contact = session.query(Contact).filter_by(company_id=company_id, email=email).first() if email else None
    if contact:
        contact.first_name = first_name
        contact.last_name = last_name
        contact.title = title
        contact.linkedin_url = linkedin_url
        contact.phone = phone
        contact.discovery_source = discovery_source
    else:
        contact = Contact(
            id=str(uuid.uuid4()),
            company_id=company_id,
            first_name=first_name,
            last_name=last_name,
            title=title,
            email=email,
            linkedin_url=linkedin_url,
            phone=phone,
            discovery_source=discovery_source,
        )
        session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


# --- Enrichment ---

def upsert_enrichment(session: Session, company_id: str, data: Dict[str, Any],
                      source: str = "apollo") -> Enrichment:
    enrichment = session.query(Enrichment).filter_by(company_id=company_id, source=source).first()
    if enrichment:
        enrichment.data = data
        enrichment.enriched_date = func.now()
    else:
        enrichment = Enrichment(
            id=str(uuid.uuid4()),
            company_id=company_id,
            data=data,
            source=source,
        )
        session.add(enrichment)
    session.commit()
    session.refresh(enrichment)
    return enrichment


# --- HITL ---

def create_hitl_message(session: Session, opportunity_id: str,
                        message_text: str, generated_by: str = "hermes_outreach_agent") -> Hitl:
    hitl = Hitl(
        id=str(uuid.uuid4()),
        opportunity_id=opportunity_id,
        message_text=message_text,
        generated_by=generated_by,
        status="pending",
    )
    session.add(hitl)
    session.commit()
    session.refresh(hitl)
    return hitl


def get_pending_hitl(session: Session) -> List[Hitl]:
    return session.query(Hitl).filter(Hitl.status == "pending").all()


def approve_hitl(session: Session, hitl_id: str, approved_by: str = "human") -> Hitl:
    hitl = session.query(Hitl).get(hitl_id)
    if hitl:
        hitl.status = "approved"
        hitl.approved_by = approved_by
        hitl.approved_at = func.now()
    session.commit()
    session.refresh(hitl)
    return hitl


def reject_hitl(session: Session, hitl_id: str) -> Hitl:
    hitl = session.query(Hitl).get(hitl_id)
    if hitl:
        hitl.status = "rejected"
    session.commit()
    session.refresh(hitl)
    return hitl


# --- Funnels ---

def upsert_funnel(session: Session, name: str, description: Optional[str] = None,
                  campaign_id: Optional[str] = None, channel: str = "email",
                  sequence_json: Optional[List] = None, status: str = "active") -> Funnel:
    seq = sequence_json or []
    funnel = session.query(Funnel).filter_by(name=name).first()
    if funnel:
        funnel.description = description
        funnel.campaign_id = campaign_id
        funnel.channel = channel
        funnel.sequence_json = seq
        funnel.status = status
    else:
        funnel = Funnel(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            campaign_id=campaign_id,
            channel=channel,
            sequence_json=seq,
            status=status,
        )
        session.add(funnel)
    session.commit()
    session.refresh(funnel)
    return funnel


# --- Responses ---

def create_response(session: Session, opportunity_id: str, contact_id: Optional[str],
                    source: str, sentiment: str = "neutral", message_text: Optional[str] = None,
                    action_taken: Optional[str] = None) -> Response:
    resp = Response(
        id=str(uuid.uuid4()),
        opportunity_id=opportunity_id,
        contact_id=contact_id,
        source=source,
        sentiment=sentiment,
        message_text=message_text,
        action_taken=action_taken,
        status="open",
    )
    session.add(resp)
    session.commit()
    session.refresh(resp)
    return resp


# --- Bookings ---

def create_booking(session: Session, opportunity_id: str, contact_id: Optional[str],
                   calendly_id: Optional[str] = None, slot_start=None, slot_end=None,
                   calendar_title: Optional[str] = None, calendar_description: Optional[str] = None) -> Booking:
    booking = Booking(
        id=str(uuid.uuid4()),
        opportunity_id=opportunity_id,
        contact_id=contact_id,
        calendly_id=calendly_id,
        slot_start=slot_start,
        slot_end=slot_end,
        status="scheduled",
        calendar_title=calendar_title,
        calendar_description=calendar_description,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking