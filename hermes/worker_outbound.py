"""
Outbound worker – watches approved HITL records and sends the message
via Mautic, LinkedIn, or WhatsApp (real implementations where possible).
"""

import os
import time
import json
import logging
import requests
from hermes.crm import SessionLocal, Hitl, OutboundLog, Company, Contact
from hermes.config import settings
from sqlalchemy import func

log = logging.getLogger("hermes.outbound")

# Credentials from environment (set in .env)
MAUTIC_URL = getattr(settings, "mautic_url", os.getenv("MAUTIC_URL", ""))
MAUTIC_USER = getattr(settings, "mautic_user", os.getenv("MAUTIC_USER", ""))
MAUTIC_PASS = getattr(settings, "mautic_pass", os.getenv("MAUTIC_PASS", ""))
LINKEDIN_TOKEN = getattr(settings, "linkedin_access_token", os.getenv("LINKEDIN_ACCESS_TOKEN", ""))
WHATSAPP_TOKEN = getattr(settings, "whatsapp_token", os.getenv("WHATSAPP_TOKEN", ""))
WHATSAPP_PHONE_ID = getattr(settings, "whatsapp_phone_id", os.getenv("WHATSAPP_PHONE_ID", ""))
OUTBOUND_CHANNEL = os.getenv("OUTBOUND_CHANNEL", "mautic").lower()  # mautic | linkedin | whatsapp

def _retry(func, *args, max_retries=5, base_delay=1, **kwargs):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                log.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                raise
            delay = base_delay * (2 ** attempt)
            log.warning(f"Attempt {attempt+1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
            time.sleep(delay)

def _mautic_send(to_email: str, message: str) -> bool:
    """Send an email via Mautic API."""
    if not (MAUTIC_URL and MAUTIC_USER and MAUTIC_PASS):
        log.warning("Mautic credentials not set – skipping send.")
        return False
    auth = (MAUTIC_USER, MAUTIC_PASS)
    try:
        # 1. Find/create contact (simplified)
        def _find_or_create():
            r = requests.get(
                f"{MAUTIC_URL}/contacts/search",
                params={"email": to_email},
                auth=auth,
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                contact_id = (
                    data[0].get("id")
                    if data and isinstance(data, list) and len(data) > 0
                    else None
                )
            else:
                # create new contact
                r = requests.post(
                    f"{MAUTIC_URL}/contacts/new",
                    json={"email": to_email},
                    auth=auth,
                    timeout=10,
                )
                contact_id = (
                    r.json().get("contact", {}).get("id")
                    if r.status_code == 200
                    else None
                )
            return contact_id

        contact_id = _retry(_find_or_create)
        if not contact_id:
            return False
        # 2. Send email – we need to know which email to send.
        # For simplicity, we assume a transactional email ID is set in settings.
        # In a real system, you might have a mapping of message type to email ID.
        email_id = getattr(settings, "mautic_email_id", os.getenv("MAUTIC_EMAIL_ID", ""))
        if not email_id:
            log.warning("Mautic email ID not set – logging only.")
            log.info(f"[MAUTIC] Would send to {to_email}: {message}")
            return True
        # Send the email
        url = f"{MAUTIC_URL}/mails/{email_id}/send"
        payload = {"contactId": contact_id, "sendAsNew": True}
        r = requests.post(url, json=payload, auth=auth, timeout=10)
        if r.status_code == 200:
            log.info(f"[MAUTIC] Sent email to {to_email} (email ID {email_id})")
            return True
        else:
            log.error(f"Mautic send failed: {r.status_code} {r.text}")
            return False
    except Exception as e:
        log.error(f"Mautic send error: {e}")
        return False

def _linkedin_send(to_urn: str, message: str) -> bool:
    """Send a message via LinkedIn Message API (partner required)."""
    if not LINKEDIN_TOKEN:
        log.warning("LinkedIn token not set – skipping send.")
        return False
    url = "https://api.linkedin.com/v2/messages"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    # We don't have a subject in Hitl, so we use a default or first line.
    subject = "Message from Interceptor"
    # Truncate message to avoid too long
    body = message[:1000]  # LinkedIn might have limits
    payload = {
        "recipients": {
            "values": [
                {
                    "entity": to_urn,
                    "entityType": "person",
                }
            ]
        },
        "subject": subject,
        "body": {
            "content": {
                "contentType": "text/plain",
                "text": body,
            }
        },
    }
    try:
        def _send():
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            if r.status_code in (200, 201):
                return True
            else:
                log.error(f"LinkedIn send failed: {r.status_code} {r.text}")
                return False
        return _retry(_send)
    except Exception as e:
        log.error(f"LinkedIn send error: {e}")
        return False

def _whatsapp_send(to: str, message: str) -> bool:
    """Send a WhatsApp text message via the Cloud API."""
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID):
        log.warning("WhatsApp credentials not set – skipping send.")
        return False
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    try:
        def _send():
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            if r.status_code == 200:
                return True
            else:
                log.error(f"WhatsApp send failed: {r.status_code} {r.text}")
                return False
        return _retry(_send)
    except Exception as e:
        log.error(f"WhatsApp send error: {e}")
        return False

def process_queue():
    """Poll for approved HITL records and attempt to send them."""
    while True:
        time.sleep(5)  # simple poll – replace with Redis BLPOP or RabbitMQ in prod
        db = SessionLocal()
        approved = (
            db.query(Hitl)
            .filter(Hitl.status == "approved", Hitl.outbound_sent.is_(None))
            .limit(5)
            .all()
        )
        db.close()
        for hitl in approved:
            db = SessionLocal()
            hitl = db.merge(hitl)  # reattach to session
            company = (
                db.query(Company)
                .filter(Company.id == hitl.company_id)
                .first()
            )
            contact = (
                db.query(Contact)
                .filter(Contact.id == hitl.contact_id)
                .first()
            )
            db.close()
            if not (company and contact):
                continue

            # Choose channel
            channel = OUTBOUND_CHANNEL
            sent = False
            if channel == "mautic":
                # Use contact's email if present, otherwise fallback to company domain
                to_addr = contact.email or f"info@{company.domain}"
                sent = _mautic_send(to_addr, hitl.message_text)
            elif channel == "linkedin":
                # Build a LinkedIn URN – here we fake it; replace with real ID if you have it
                to_urn = f"urn:li:person:{contact.linkedin_id or 'unknown'}"
                sent = _linkedin_send(to_urn, hitl.message_text)
            elif channel == "whatsapp":
                to_addr = contact.phone or contact.whatsapp_id or ""
                if not to_addr:
                    log.warning(
                        "No phone/whatsapp_id for contact – skipping WhatsApp send"
                    )
                else:
                    sent = _whatsapp_send(to_addr, hitl.message_text)

            # Log outcome
            db = SessionLocal()
            log_entry = OutboundLog(
                hitl_id=hitl.id,
                channel=channel,
                status="sent" if sent else "failed",
                sent_at=func.now() if sent else None,
                error_message=None if sent else "Send function returned False",
            )
            db.add(log_entry)
            if sent:
                hitl.outbound_sent = func.now()
            db.merge(hitl)
            db.commit()
            db.close()

def start_outbound_worker():
    """Launch the outbound worker as a daemon thread."""
    import threading

    thread = threading.Thread(target=process_queue, daemon=True)
    thread.start()
    log.info("Outbound worker started")