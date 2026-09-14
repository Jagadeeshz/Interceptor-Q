"""
LinkedIn enrichment stub for Interceptor.

Accepts company_id, returns normalized dict, writes via crl.upsert_enrichment.
"""
import logging
from typing import Dict, Any
from crl.crm import upsert_enrichment, get_session

logger = logging.getLogger(__name__)

def enrich_company_with_linkedin(company_id: str) -> Dict[str, Any]:
    """
    Stub for LinkedIn enrichment.
    In reality, this would scrape or call LinkedIn API.
    For now, returns mock data.
    """
    logger.info(f"Enriching company {company_id} with LinkedIn (stub)")
    # Mock data
    data = {
        "company_size": "51-200",
        "industry": "Software",
        "linkedin_followers": 5000,
        "recent_hires": 5,
        "linkedin_id": "li_67890"
    }
    # Write to CRM
    with get_session() as session:
        upsert_enrichment(session, company_id, data, source="linkedin")
    return data