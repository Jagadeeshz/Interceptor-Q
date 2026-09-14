"""
Calendly client stub for Interceptor.

Handles meeting creation.
"""
import logging
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

def create_meeting(opportunity_id: str, slot_start: str, slot_end: str,
                   event_type: str = "30min", invitee_email: Optional[str] = None) -> str:
    """
    Stub for creating a meeting via Calendly.
    In reality, this would call the Calendly API.
    For now, returns a mock calendar ID.
    """
    logger.info(f"Creating Calendly meeting for opportunity {opportunity_id} from {slot_start} to {slot_end}")
    # Generate a mock Calendly UUID
    calendar_id = str(uuid.uuid4())
    return calendar_id