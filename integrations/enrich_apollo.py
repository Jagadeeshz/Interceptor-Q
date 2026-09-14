"""
Apollo enrichment stub for Interceptor.

Accepts company_id, returns normalized dict, writes via crl.upsert_enrichment.
"""
import logging
from typing import Dict, Any
from crl.crm import upsert_enrichment, get_session

logger = logging.getLogger(__name__)

def enrich_company_with_apollo(company_id: str) -> Dict[str, Any]:
    """
    Stub for Apollo enrichment.
    In reality, this would call the Apollo API.
    For now, returns mock data.
    """
    logger.info(f"Enriching company {company_id} with Apollo (stub)")
    # Mock data
    data = {
        "funding_stage": "Series B",
        "employee_count": 150,
        "technologies": ["Python", "React", "AWS"],
        "revenue": "$10M",
        "apollo_id": "apo_12345"
    }
    # Write to CRM
    with get_session() as session:
        upsert_enrichment(session, company_id, data, source="apollo")
    return data