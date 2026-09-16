"""Autonomous lead discovery service.
Periodically runs searches on job boards, career pages, and web search,
and stores raw leads in the database for enrichment.
"""

import os
import time
import requests
import logging
from hermes import app
from hermes.crm import SessionLocal, LeadRaw

log = logging.getLogger("hermes.discoverer")

# Configuration from environment variables with sensible defaults
DISCOVER_SOURCES = os.getenv(
    "DISCOVER_SOURCES",
    "jooble,indeed,linkedin,google"
).split(",")

DISCOVER_KEYWORDS = os.getenv(
    "DISCOVER_KEYWORDS",
    "senior engineer,product manager,data scientist,devops engineer,data analyst"
).split(",")

DISCOVER_LOCATIONS = os.getenv(
    "DISCOVER_LOCATIONS",
    "USA,Canada,UK,Germany,France,Australia,India"
).split(",")

DISCOVER_INTERVAL = int(os.getenv("DISCOVER_INTERVAL", "1800"))  # seconds, default 30 minutes


def _store_lead(source: str, keyword: str, location: str) -> int:
    """
    Store a raw lead in the database.
    In a real implementation, this would be the result of an actual search.
    For now we generate a placeholder lead.
    """
    payload = {
        "source": source,
        "keyword": keyword,
        "location": location,
        "url": f"https://example.com/{source}/{keyword.replace(' ', '-')}/{location.replace(' ', '-')}",
        "title": f"{keyword} at {location}",
        "snippet": f"Placeholder lead for {keyword} in {location} from {source}.",
        "raw_json": {
            "source": source,
            "keyword": keyword,
            "location": location,
            "timestamp": time.time()
        }
    }
    db = SessionLocal()
    lr = LeadRaw(**payload)
    db.add(lr)
    db.commit()
    db.refresh(lr)
    db.close()
    log.info(f"Stored raw lead: {lr.id} - {lr.title}")
    return lr.id


def run_discovery_cycle():
    """Run one cycle of discovery across all sources, keywords, and locations."""
    inserted = 0
    for source in DISCOVER_SOURCES:
        for keyword in DISCOVER_KEYWORDS:
            for location in DISCOVER_LOCATIONS:
                try:
                    _store_lead(source, keyword, location)
                    inserted += 1
                except Exception as e:
                    log.error(f"Failed to store lead for {source} {keyword} {location}: {e}")
    log.info(f"Discovery cycle complete. Inserted {inserted} raw leads.")
    return inserted


def run_discovery_once():
    """Run a single discovery cycle (for manual triggering)."""
    return run_discovery_cycle()


def start_discovery_scheduler():
    """Start a background scheduler that runs discovery periodically."""
    import threading

    def worker():
        while True:
            try:
                run_discovery_cycle()
            except Exception as e:
                log.error(f"Discovery worker error: {e}")
            time.sleep(DISCOVER_INTERVAL)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    log.info(f"Discovery scheduler started with interval {DISCOVER_INTERVAL} seconds.")


# If this module is run directly, run a single cycle (useful for testing)
if __name__ == "__main__":
    run_discovery_cycle()