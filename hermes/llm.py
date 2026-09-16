"""
LLM wrapper for generating personalized outreach messages.
Supports OpenAI-compatible endpoints (including DeepSeek).
"""

import os
import httpx
import logging
from hermes.config import settings

log = logging.getLogger("hermes.llm")

# LLM configuration from environment variables, with sensible defaults
LLM_ENDPOINT = getattr(settings, 'llm_endpoint', os.getenv("LLM_ENDPOINT", "https://api.deepseek.com/v1/chat/completions"))
LLM_MODEL = getattr(settings, 'llm_model', os.getenv("LLM_MODEL", "deepseek-chat"))
LLM_KEY = getattr(settings, 'llm_key', os.getenv("LLM_KEY", ""))

async def generate_message(company: dict, contact: dict) -> str:
    """
    Generate a personalized outreach message using an LLM.
    :param company: dict with keys like 'name', 'domain', 'industry', etc.
    :param contact: dict with keys like 'first_name', 'last_name', 'title', 'email', etc.
    :return: generated message string
    """
    if not LLM_KEY:
        # Fallback to a template if no API key is set
        return f"Hi {contact.get('first_name', 'there')},\n\nI came across {company.get('name', 'your company')} and was impressed by your work in {company.get('industry', 'the industry')}. I believe there's a great opportunity for us to collaborate. Let's schedule a quick chat to explore synergies.\n\nBest regards,\nThe Hermes Team"

    prompt = f"""
    You are a professional recruiter. Write a concise, personalized LinkedIn/email message
    to {contact.get('first_name', '')} {contact.get('last_name', '')} at {company.get('name', 'the company')}.
    Reference one specific detail from their profile or recent activity.
    Keep it under 150 words, friendly, and include a clear call‑to‑action (e.g., “Let’s schedule a 15‑min chat this week.”).
    """

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert recruitment copywriter."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 200,
    }

    headers = {
        "Authorization": f"Bearer {LLM_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(LLM_ENDPOINT, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            # Extract the generated text from the response (OpenAI/DeepSeek format)
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            log.error(f"LLM generation failed: {e}")
            # Fallback to a template on error
            return f"Hi {contact.get('first_name', 'there')},\n\nI came across {company.get('name', 'your company')} and was impressed by your work in {company.get('industry', 'the industry')}. I believe there's a great opportunity for us to collaborate. Let's schedule a quick chat to explore synergies.\n\nBest regards,\nThe Hermes Team"