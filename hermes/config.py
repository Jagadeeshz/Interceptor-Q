"""
Configuration module for Hermes.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env from the repository root (no-op if already provided as env vars)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

class Settings:
    def __init__(self):
        # Database
        self.postgres_database_url = os.getenv(
            "POSTGRES_DATABASE_URL",
            "postgresql://interceptor_admin:***@postgres:5432/hermes_db",
        )
        # LLM provider (OpenAI-compatible endpoint, e.g. NVIDIA NIM)
        self.llm_provider = os.getenv("LLM_PROVIDER", "nvidia")
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-ai/deepseek-v4-flash-0731")
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_base_url = os.getenv(
            "LLM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        )
        # Outbound credentials
        self.mautic_url = os.getenv("MAUTIC_URL", "")
        self.mautic_user = os.getenv("MAUTIC_USER", "")
        self.mautic_pass = os.getenv("MAUTIC_PASS", "")
        self.linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN", "")
        self.whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
        # Enrichment credentials
        self.apollo_key = os.getenv("APOLLO_KEY", "")
        self.hunter_key = os.getenv("HUNTER_KEY", "")
        # Auth
        self.api_key = os.getenv("API_KEY", "")
        # Feature flags
        self.enable_discovery = os.getenv("ENABLE_DISCOVERY", "false").lower() == "true"
        self.outbound_channel = os.getenv("OUTBOUND_CHANNEL", "mautic").lower()

# Create a singleton instance
settings = Settings()