import pytest
from hermes.__init__ import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_create_company():
    response = client.post(
        "/api/companies/",
        json={"name": "Test Co", "domain": "test.com", "region": "NAC"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Co"
    assert data["id"] == 1


def test_get_companies():
    response = client.get("/api/companies/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 0