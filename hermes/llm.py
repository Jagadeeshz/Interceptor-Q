"""
LLM wrapper for generating personalized outreach messages.
Routes all requests through the OpenAI-compatible Python SDK
against any compatible endpoint (default: NVIDIA NIM).
"""

import logging
from typing import Optional

from openai import AsyncOpenAI

from hermes.config import settings

log = logging.getLogger("hermes.llm")

LLM_KEY: str = settings.llm_api_key
LLM_BASE_URL: str = settings.llm_base_url
LLM_MODEL: str = settings.llm_model

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    """Lazily initialise a reusable AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=LLM_KEY, base_url=LLM_BASE_URL)
    return _client


_FALLBACK_TEMPLATE = (
    "Hi {first_name},\n\n"
    "I came across {company_name} and was impressed by your work in "
    "{industry}. I believe there is a great opportunity for us to "
    "collaborate. Let us schedule a quick chat to explore synergies.\n\n"
    "Best regards,\nThe Hermes Team"
)


async def generate_message(company: dict, contact: dict) -> str:
    """
    Generate a personalised outreach message using the configured LLM.

    :param company: dict with keys ``name``, ``domain``, ``industry`` etc.
    :param contact: dict with keys ``first_name``, ``last_name``, ``title`` etc.
    :return: generated message string
    """
    first_name = contact.get("first_name", "there")
    company_name = company.get("name", "your company")
    industry = company.get("industry", "the industry")

    if not LLM_KEY:
        log.warning("LLM_API_KEY not set – using fallback template")
        return _FALLBACK_TEMPLATE.format(
            first_name=first_name,
            company_name=company_name,
            industry=industry,
        )

    prompt = (
        "You are a professional recruiter. Write a concise, personalised "
        f"LinkedIn/email message to {contact.get('first_name', '')} "
        f"{contact.get('last_name', '')} at {company_name}. "
        "Reference one specific detail from their profile or recent activity. "
        "Keep it under 150 words, friendly, and include a clear call-to-action "
        '(e.g., "Let us schedule a 15-min chat this week.").'
    )

    try:
        response = await _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert recruitment copywriter."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("LLM generation failed: %s", e)
        return _FALLBACK_TEMPLATE.format(
            first_name=first_name,
            company_name=company_name,
            industry=industry,
        )
