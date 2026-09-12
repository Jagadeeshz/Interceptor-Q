"""Tests for Interceptor Hermes AI Agent."""

import pytest
from fastapi.testclient import TestClient
from hermes.app import app

client = TestClient(app)


def test_health_endpoint():
    """GET /health should return ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "llm_provider" in data


def test_root_endpoint():
    """GET / should return welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Interceptor Hermes AI Agent is running"


def test_post_event_valid():
    """POST /event with valid JSON should return 200."""
    response = client.post(
        "/event",
        json={"type": "opportunity_created", "company_name": "Test Corp", "job_title": "Developer"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["event_type"] == "opportunity_created"


def test_post_event_missing_type():
    """POST /event without type should still accept (lenient)."""
    response = client.post(
        "/event",
        json={"company_name": "Test Corp"}
    )
    # The endpoint is lenient — it just logs and returns received
    assert response.status_code == 200