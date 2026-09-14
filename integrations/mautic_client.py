"""
Mautic client stub for Interceptor.

Handles email sequence dispatch.
"""
import logging
from typing import Optional
from crl.crm import upsert_funnel, get_session

logger = logging.getLogger(__name__)

def send_email_sequence(opportunity_id: str, template_id: str = "welcome_series") -> bool:
    """
    Stub for sending an email sequence via Mautic.
    In reality, this would call the Mautic API.
    For now, logs and returns True.
    """
    logger.info(f"Sending email sequence for opportunity {opportunity_id} via Mautic (stub)")
    # Optionally, create a funnel record
    with get_session() as session:
        upsert_funnel(
            session,
            name=f"Mautic sequence for opportunity {opportunity_id}",
            description=f"Automated email sequence triggered by opportunity {opportunity_id}",
            channel="email",
            campaign_id=f"mautic_{opportunity_id}",
            sequence_json=[{"step": 1, "type": "email", "template": template_id}],
            status="active"
        )
    return True