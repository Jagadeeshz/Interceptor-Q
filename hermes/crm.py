from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import text
import os

# Database URL from environment (same as in __init__.py)
DATABASE_URL = os.getenv(
    "POSTGRES_DATABASE_URL",
    "postgresql://interceptor_admin:***@postgres:5432/hermes_db",
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
Base.query = None

# Helper for queries
def db_query(sql: str):
    """Run a read-only query; return list of dict rows or None when DB is down."""
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result]
    except Exception as e:
        # In __init__.py we have our own db_query that logs; we can just return None here
        return None

# Tables
class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), nullable=False)
    domain = Column(String(250), nullable=True)
    region = Column(String(50), nullable=True)
    source_platform = Column(String(50), nullable=True)
    funding_stage = Column(String(50), nullable=True)
    company_size = Column(Integer, nullable=True)
    detected_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=True)
    # relationships
    opportunities = relationship("Opportunity", back_populates="company")
    contacts = relationship("Contact", back_populates="company")
    hitl_entries = relationship("Hitl", back_populates="company")

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    job_title = Column(String(250), nullable=False)
    matched_pod = Column(String(100), nullable=True)
    match_score = Column(Integer, nullable=True)
    source_platform = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    region = Column(String(50), nullable=True)
    detected_date = Column(DateTime(timezone=True), server_default=func.now())
    # relationships
    company = relationship("Company", back_populates="opportunities")
    contacts = relationship("Contact", secondary="opportunity_contacts")  # optional

class OpportunityContact(Base):
    __tablename__ = "opportunity_contacts"
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(250), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(250), nullable=True)
    title = Column(String(250), nullable=True)
    source = Column(String(50), nullable=True)
    # relationships
    company = relationship("Company", back_populates="contacts")
    opportunities = relationship("Opportunity", secondary="opportunity_contacts")
    hitl_entries = relationship("Hitl", back_populates="contact")

class Hitl(Base):
    __tablename__ = "hitl"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    message_text = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending | approved | rejected
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    outbound_sent = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # relationships
    company = relationship("Company", back_populates="hitl_entries")
    contact = relationship("Contact", back_populates="hitl_entries")
    meetings = relationship("Meeting", back_populates="hitl")

class Meeting(Base):
    __tablename__ = "meeting"
    id = Column(Integer, primary_key=True, index=True)
    hitl_id = Column(Integer, ForeignKey("hitl.id"))
    booked_at = Column(DateTime(timezone=True), server_default=func.now())
    platform = Column(String(20))  # linkedin | whatsapp | mautic | calendar
    meet_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    # relationships
    hitl = relationship("Hitl", back_populates="meetings")

class OutboundLog(Base):
    __tablename__ = "outbound_log"
    id = Column(Integer, primary_key=True, index=True)
    hitl_id = Column(Integer, ForeignKey("hitl.id"))
    channel = Column(String(20))
    status = Column(String(10))  # sent | failed
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LeadRaw(Base):
    __tablename__ = "lead_raw"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), index=True)
    keyword = Column(String(100), index=True)
    location = Column(String(100), index=True)
    url = Column(String(500))
    title = Column(String(250))
    snippet = Column(Text)
    raw_json = Column(JSON, nullable=True)
    enriched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EventLog(Base):
    __tablename__ = "event_log"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50))
    time = Column(DateTime(timezone=True))
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create all tables
Base.metadata.create_all(bind=engine)