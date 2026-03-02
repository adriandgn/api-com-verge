from supabase import create_client

from api.settings import get_settings


async def check_db() -> dict:
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    result = client.table("registrations").select("id").limit(1).execute()
    return {"ok": True, "count": len(result.data) if result.data else 0}


async def check_smtp() -> dict:
    # Minimal check: confirm config present
    settings = get_settings()
    required = [settings.mail_username, settings.mail_password, settings.mail_from]
    ok = all(required)
    return {"ok": ok}
