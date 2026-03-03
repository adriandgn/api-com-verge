import pytest

try:
    from fastapi.testclient import TestClient
    from api.index import app
    from api.routes import sponsors as sponsors_routes
except Exception:  # pragma: no cover
    app = None


if app is None:  # pragma: no cover
    pytest.skip("API code not present yet; tests are a template.", allow_module_level=True)


client = TestClient(app)


@pytest.fixture(autouse=True)
def _patch_db_and_email(monkeypatch):
    async def _fake_insert_sponsor_inquiry(*args, **kwargs):
        return {"uuid": "sponsor-uuid-123"}

    async def _fake_send_sponsor_confirmation_email(*args, **kwargs):
        return None

    async def _fake_send_sponsor_admin_notification(*args, **kwargs):
        return None

    monkeypatch.setattr(sponsors_routes, "insert_sponsor_inquiry", _fake_insert_sponsor_inquiry)
    monkeypatch.setattr(
        sponsors_routes,
        "send_sponsor_confirmation_email",
        _fake_send_sponsor_confirmation_email
    )
    monkeypatch.setattr(
        sponsors_routes,
        "send_sponsor_admin_notification",
        _fake_send_sponsor_admin_notification
    )


def test_create_sponsor_inquiry_ok():
    payload = {
        "name": "Test Sponsor",
        "company": "Test Company",
        "phone": "+1 555 123 4567",
        "email": "test@example.com",
        "message": "We want to sponsor the event."
    }
    resp = client.post("/api/sponsors", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["sponsor_id"] == "sponsor-uuid-123"


def test_create_sponsor_inquiry_missing_required():
    resp = client.post("/api/sponsors", json={})
    assert resp.status_code == 422


def test_create_sponsor_inquiry_invalid_email():
    payload = {
        "name": "Test Sponsor",
        "company": "Test Company",
        "phone": None,
        "email": "not-an-email",
        "message": "We want to sponsor the event."
    }
    resp = client.post("/api/sponsors", json=payload)
    assert resp.status_code == 422

