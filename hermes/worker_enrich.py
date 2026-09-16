"""
Enrichment worker – pulls raw leads, calls Apollo/Hunter/LinkedIn APIs,
and writes enriched Company & Contact rows.
"""

import os
import asyncio
import json
import httpx
import logging
from hermes.crm import SessionLocal, LeadRaw, Company, Contact
from hermes.config import settings

log = logging.getLogger("hermes.enrich")

# API keys from environment (set in .env)
APOLLO_KEY = getattr(settings, "apollo_key", os.getenv("APOLLO_KEY", ""))
HUNTER_KEY = getattr(settings, "hunter_key", os.getenv("HUNTER_KEY", ""))
LINKEDIN_TOKEN = getattr(settings, "linkedin_access_token", os.getenv("LINKEDIN_ACCESS_TOKEN", ""))


async def _retry_async(func, *args, max_retries=5, base_delay=1, **kwargs):
    """Retry an async function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                log.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                raise
            delay = base_delay * (2 ** attempt)
            log.warning(f"Attempt {attempt+1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)


async def enrich_lead(raw: LeadRaw):
    """
    Try Apollo → Hunter → LinkedIn (very simple; replace with real logic).
    Returns the company ID if enrichment succeeded, else None.
    """
    # Very naive company name extraction – improve with NLP / regex in production
    company_name = raw.title.split(" at ")[0] if " at " in raw.title else raw.title
    async with httpx.AsyncClient() as client:
        # -------- Apollo --------
        if APOLLO_KEY:
            try:
                resp = await _retry_async(
                    client.get,
                    "https://api.apollo.io/v1/organizations/search",
                    params={"q": company_name, "page": 1, "per_page": 1},
                    headers={"Api-Key": APOLLO_KEY},
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    data = resp.json().get("organizations", [])
                    if data:
                        org = data[0]
                        db = SessionLocal()
                        comp = Company(
                            name=org.get("name"),
                            domain=org.get("primary_domain"),
                            industry=org.get("industry"),
                            size=org.get("estimated_num_employees"),
                            location=org.get("headquarters_city"),
                            linkedin_url=org.get("linkedin_url"),
                            raw_apollo=org,
                        )
                        db.add(comp)
                        db.commit()
                        db.refresh(comp)
                        db.close()
                        # ----- contacts from Apollo (people) -----
                        for p in data.get("people", [])[:5]:
                            contact = Contact(
                                first_name=p.get("first_name"),
                                last_name=p.get("last_name"),
                                email=p.get("email"),
                                title=p.get("title"),
                                linkedin_url=p.get("linkedin_url"),
                                company_id=comp.id,
                                source="apollo",
                            )
                            db = SessionLocal()
                            db.add(contact)
                            db.commit()
                            db.close()
                        return comp.id
                else:
                    log.warning(f"Apollo returned non-200: {resp.status_code}")
            except Exception as e:
                log.error(f"Apollo enrichment error: {e}")

        # -------- Hunter fallback (domain search) --------
        if HUNTER_KEY:
            # Guess domain from company name (very naive)
            domain = (
                company_name.lower().replace(" ", "") + ".com"
                if "." not in company_name
                else company_name.split(" ")[0].lower() + ".com"
            )
            try:
                resp = await _retry_async(
                    client.get,
                    f"https://api.hunter.io/v2/domain-search",
                    params={"domain": domain, "limit": 10},
                    headers={"Api-Key": HUNTER_KEY},
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    emails = [
                        e["value"] for e in data.get("emails", []) if e.get("value")
                    ]
                    if emails:
                        db = SessionLocal()
                        comp = Company(
                            name=company_name.title(),
                            domain=domain,
                            industry="Unknown",
                            size=None,
                            location=None,
                            linkedin_url=None,
                            raw_hunter=data,
                        )
                        db.add(comp)
                        db.commit()
                        db.refresh(comp)
                        db.close()
                        for email in emails:
                            contact = Contact(
                                email=email,
                                source="hunter",
                                company_id=comp.id,
                            )
                            db = SessionLocal()
                            db.add(contact)
                            db.commit()
                            db.close()
                        return comp.id
                else:
                    log.warning(f"Hunter returned non-200: {resp.status_code}")
            except Exception as e:
                log.error(f"Hunter enrichment error: {e}")

        # -------- LinkedIn placeholder (if you have a partner API) --------
        # TODO: implement real LinkedIn enrichment if you have access
        log.warning(
            "LinkedIn enrichment not implemented – skipping (no LINKEDIN_ACCESS_TOKEN)."
        )
    return None


async def worker_loop():
    """Continuously poll for raw leads and enrich them."""
    while True:
        db = SessionLocal()
        batch = (
            db.query(LeadRaw)
            .filter(LeadRaw.enriched_at.is_(None))
            .limit(10)
            .all()
        )
        db.close()
        if not batch:
            await asyncio.sleep(5)
            continue
        for raw in batch:
            try:
                await enrich_lead(raw)
                # Mark raw as processed
                db = SessionLocal()
                raw.enriched_at = func.now()
                db.merge(raw)
                db.commit()
                db.close()
            except Exception as e:
                log.error(f"Enrichment failed for lead {raw.id}: {e}")


def start_worker():
    """Launch the enrichment worker as a daemon thread."""
    import threading

    thread = threading.Thread(target=lambda: asyncio.run(worker_loop()), daemon=True)
    thread.start()
    log.info("Enrichment worker started")