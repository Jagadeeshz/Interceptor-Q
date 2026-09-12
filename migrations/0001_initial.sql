-- Migration: 0001_initial.sql
-- Interceptor Platform — Initial database schema
-- PostgreSQL 16+

-- Create the database (run via: psql -U interceptor_admin -d hermes_db -f 0001_initial.sql)
-- CREATE DATABASE hermes_db;
-- GRANT ALL PRIVILEGES ON DATABASE hermes_db TO interceptor_admin;

-- ------------------------------------------------------
-- Extension: UUID generation
-- ------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------
-- Table: companies
-- ------------------------------------------------------
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    region VARCHAR(50) CHECK (region IN ('APAC', 'MENA', 'EU', 'NAC', 'LATAM')),
    tech_stack JSONB DEFAULT '{}',
    funding_stage VARCHAR(50),
    company_size VARCHAR(50),
    source_url TEXT,
    source_platform VARCHAR(100),
    detected_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_enriched DATE
);

-- ------------------------------------------------------
-- Table: opportunities
-- ------------------------------------------------------
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_platform VARCHAR(100),
    region VARCHAR(50) CHECK (region IN ('APAC', 'MENA', 'EU', 'NAC', 'LATAM')),
    posted_date TIMESTAMP WITH TIME ZONE,
    detected_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    matched_pod VARCHAR(100) NOT NULL,
    match_score NUMERIC(5, 2) CHECK (match_score >= 0 AND match_score <= 100),
    hiring_signal_summary TEXT,
    status VARCHAR(50) DEFAULT 'DISCOVERED'
        CHECK (status IN ('DISCOVERED', 'QUALIFIED', 'REJECTED', 'PROSPECT_CREATED', 'CAMPAIGN_ACTIVE', 'BOOKED')),
    enrichment_jsonb JSONB DEFAULT '{}'
);

-- ------------------------------------------------------
-- Table: contacts (decision makers)
-- ------------------------------------------------------
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    title VARCHAR(150),
    email VARCHAR(255),
    linkedin_url TEXT,
    phone VARCHAR(50),
    relevance_score NUMERIC(5, 2) DEFAULT 0,
    discovery_source VARCHAR(100), -- 'apollo', 'linkedin', 'manual'
    discovered_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------
-- Table: enrichment (per-company cached data)
-- ------------------------------------------------------
CREATE TABLE enrichment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}',
    enriched_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100) NOT NULL, -- 'apollo', 'linkedin', 'manual'
    UNIQUE(company_id, source)
);

-- ------------------------------------------------------
-- Table: hitl (Human-in-the-Loop approval queue)
-- ------------------------------------------------------
CREATE TABLE hitl (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    message_text TEXT NOT NULL,
    generated_by VARCHAR(100) NOT NULL, -- 'hermes_outreach_agent'
    status VARCHAR(50) DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------
-- Table: funnels
-- ------------------------------------------------------
CREATE TABLE funnels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    campaign_id VARCHAR(255), -- Mautic campaign ID
    channel VARCHAR(50) NOT NULL
        CHECK (channel IN ('email', 'sms', 'whatsapp', 'voip')),
    sequence_json JSONB DEFAULT '[]', -- ordered steps/conditions
    status VARCHAR(50) DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------
-- Table: responses (inbound replies from prospects)
-- ------------------------------------------------------
CREATE TABLE responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    source VARCHAR(50) NOT NULL, -- 'email', 'sms', 'whatsapp', 'voip'
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sentiment VARCHAR(50) DEFAULT 'neutral'
        CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    message_text TEXT,
    action_taken VARCHAR(100), -- 'booked', 'replied', 'qualified', 'closed'
    status VARCHAR(50) DEFAULT 'open'
        CHECK (status IN ('open', 'resolved'))
);

-- ------------------------------------------------------
-- Table: bookings (calendar meetings)
-- ------------------------------------------------------
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    calendly_id VARCHAR(255), -- Calendly meeting UUID
    slot_start TIMESTAMP WITH TIME ZONE,
    slot_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
    calendar_title VARCHAR(255),
    calendar_description TEXT,
    booked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------
-- Indexes for common query patterns
-- ------------------------------------------------------
CREATE INDEX idx_opportunities_company ON opportunities(company_id);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_pod ON opportunities(matched_pod);
CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_hitl_status ON hitl(status);
CREATE INDEX idx_responses_opportunity ON responses(opportunity_id);
CREATE INDEX idx_bookings_opportunity ON bookings(opportunity_id);
CREATE INDEX idx_enrichment_company ON enrichment(company_id);

-- ------------------------------------------------------
-- Row-level security (optional — enable if needed)
-- ------------------------------------------------------
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO interceptor_admin;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO interceptor_admin;