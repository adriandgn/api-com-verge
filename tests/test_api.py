import pytest

try:
    from fastapi.testclient import TestClient
    from api.index import app
    from api.routes import registrations as registrations_routes
except Exception:  # pragma: no cover - allow running before implementation exists
    app = None


if app is None:  # pragma: no cover
    pytest.skip("API code not present yet; tests are a template.", allow_module_level=True)


client = TestClient(app)


@pytest.fixture(autouse=True)
def _patch_db_and_email(monkeypatch):
    async def _fake_insert_registration(*args, **kwargs):
        return {"uuid": "test-uuid-123"}

    async def _fake_get_registrations(*args, **kwargs):
        return []

    async def _fake_send_confirmation_email(*args, **kwargs):
        return None

    async def _fake_send_admin_notification(*args, **kwargs):
        return None

    monkeypatch.setattr(registrations_routes, "insert_registration", _fake_insert_registration)
    monkeypatch.setattr(registrations_routes, "get_registrations", _fake_get_registrations)
    monkeypatch.setattr(registrations_routes, "send_confirmation_email", _fake_send_confirmation_email)
    monkeypatch.setattr(registrations_routes, "send_admin_notification", _fake_send_admin_notification)


def test_health_root():
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "healthy"


def test_health_router():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "healthy"


def test_create_creator_registration_ok():
    payload = {
        "profile": "creator",
        "name": "Test Creator",
        "email": "test@example.com",
        "studio_brand": "Test Studio",
        "city": "Berlin",
        "practice_description": "This is a test registration",
        "podcast_interest": False
    }
    resp = client.post("/api/registrations/creator", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["registration_id"] == "test-uuid-123"


def test_invalid_profile_in_path():
    payload = {
        "profile": "creator",
        "name": "Test Creator",
        "email": "test@example.com",
        "studio_brand": "Test Studio",
        "city": "Berlin",
        "practice_description": "This is a test registration",
        "podcast_interest": False
    }
    resp = client.post("/api/registrations/invalid", json=payload)
    assert resp.status_code == 400


def test_mismatched_profile_body_vs_path():
    payload = {
        "profile": "expert",
        "name": "Test Expert",
        "email": "test@example.com",
        "field_expertise": "Testing",
        "city": "Berlin",
        "bio_links": "https://example.com"
    }
    resp = client.post("/api/registrations/creator", json=payload)
    assert resp.status_code == 400


def test_participant_invalid_interests():
    payload = {
        "profile": "participant",
        "name": "Test User",
        "email": "test@example.com",
        "city_country": "Berlin, DE",
        "interests": ["Invalid Interest"]
    }
    resp = client.post("/api/registrations/participant", json=payload)
    assert resp.status_code == 422
