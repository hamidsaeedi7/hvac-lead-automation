import os

os.environ["HVAC_DATABASE_PATH"] = "data/test_hvac_demo.db"

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_lead_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("HVAC_DATABASE_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        response = client.post(
            "/api/leads",
            json={
                "full_name": "Test Homeowner",
                "email": "homeowner@example.com",
                "phone": "+1 613 555 0101",
                "service_type": "emergency_repair",
                "postal_code": "K1A 0B1",
                "message": "No heat and the furnace is not working.",
                "preferred_contact": "phone",
                "consent": True,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["priority"] == "urgent"

        detail = client.get(f"/api/leads/{body['id']}")
        assert detail.status_code == 200
        assert len(detail.json()["events"]) >= 6

        dashboard = client.get("/api/dashboard")
        assert dashboard.status_code == 200
        assert dashboard.json()["total"] >= 1


def test_consent_is_required(tmp_path, monkeypatch):
    monkeypatch.setenv("HVAC_DATABASE_PATH", str(tmp_path / "consent.db"))
    with TestClient(app) as client:
        payload = {
            "full_name": "Test Homeowner",
            "email": "homeowner@example.com",
            "phone": "+1 613 555 0101",
            "service_type": "maintenance",
            "postal_code": "K1A 0B1",
            "message": "Annual maintenance request.",
            "preferred_contact": "email",
        }
        missing = client.post("/api/leads", json=payload)
        assert missing.status_code == 422

        refused = client.post("/api/leads", json={**payload, "consent": False})
        assert refused.status_code == 422
