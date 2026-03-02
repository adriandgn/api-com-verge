from supabase import Client, create_client

from api.settings import get_settings


def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


async def insert_registration(
    profile: str,
    data: dict,
    email: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None
):
    supabase = get_supabase_client()
    result = (
        supabase.table("registrations")
        .insert(
            {
                "profile": profile,
                "data": data,
                "email": email,
                "ip_address": ip,
                "user_agent": user_agent
            }
        )
        .execute()
    )
    return result.data[0] if result.data else None


async def get_registrations(profile: str | None = None, limit: int = 100):
    supabase = get_supabase_client()
    query = supabase.table("registrations").select("*")
    if profile:
        query = query.eq("profile", profile)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data
