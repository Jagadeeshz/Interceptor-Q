"""
Twilio webhook stub for Interceptor.

Handles inbound SMS/WhatsApp messages and posts type: response_received to Hermes.
"""
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
import httpx

logger = logging.getLogger(__name__)

# We'll create a simple FastAPI app for the webhook, but in reality, this would be deployed separately.
webhook_app = FastAPI(title="Twilio Webhook")

@webhook_app.post("/webhook/twilio")
async def twilio_webhook(request: Request):
    """
    Handle inbound Twilio webhook (SMS, WhatsApp, etc.)
    Extract message and post to Hermes as a response_received event.
    """
    try:
        form = await request.form()
        message_body = form.get("Body", "")
        from_number = form.get("From", "")
        to_number = form.get("To", "")
        logger.info(f"Received Twilio message from {from_number}: {message_body}")

        # Prepare event for Hermes
        event = {
            "type": "response_received",
            "source": "twilio",
            "from": from_number,
            "to": to_number,
            "message": message_body,
            # In a real system, we would look up opportunity by phone number
            # For now, we leave it to the enrichment step to match.
        }

        # Post to Hermes event endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post("http://hermes:8000/event", json=event)
            if response.status_code != 200:
                logger.error(f"Failed to post event to Hermes: {response.text}")
                raise HTTPException(status_code=500, detail="Hermes endpoint error")

        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))