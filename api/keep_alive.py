import os
from datetime import datetime, timezone
from functools import lru_cache

import anyio
from supabase import Client, create_client


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


@lru_cache(maxsize=1)
def get_supabase_anon_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    supabase_key = supabase_anon_key or supabase_service_role_key
    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Missing SUPABASE_URL and one of SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY"
        )
    if supabase_anon_key:
        print(f"[{_ts()}] keepalive: using SUPABASE_ANON_KEY")
    else:
        print(f"[{_ts()}] keepalive: SUPABASE_ANON_KEY not set, using SUPABASE_SERVICE_ROLE_KEY")
    print(f"[{_ts()}] keepalive: creating Supabase anon client")
    return create_client(supabase_url, supabase_key)


def _run_count_query(table: str) -> int | None:
    client = get_supabase_anon_client()
    response = client.table(table).select("*", count="exact", head=True).execute()
    return response.count


def _detect_table_or_fallback() -> str:
    env_table = os.getenv("SUPABASE_KEEPALIVE_TABLE", "").strip()
    candidates = [
        env_table,
        "registrations",
        "sponsor_inquiries",
        "users",
    ]
    seen: set[str] = set()

    for table in candidates:
        if not table or table in seen:
            continue
        seen.add(table)
        try:
            count = _run_count_query(table)
            print(f"[{_ts()}] keepalive: table '{table}' is reachable (count={count})")
            return table
        except Exception as exc:
            print(f"[{_ts()}] keepalive: table '{table}' failed during detection: {exc}")

    print(f"[{_ts()}] keepalive: no table detected, using fallback 'users'")
    return "users"


def _keep_alive_query() -> dict[str, object]:
    try:
        table = _detect_table_or_fallback()
        count = _run_count_query(table)
        print(f"[{_ts()}] keepalive: SELECT COUNT(*) on '{table}' succeeded (count={count})")
        return {"ok": True, "table": table, "count": count}
    except Exception as exc:
        print(f"[{_ts()}] keepalive: query failed: {exc}")
        return {"ok": False, "error": str(exc)}


async def run_keep_alive() -> dict[str, object]:
    print(f"[{_ts()}] keepalive: run started")
    result = await anyio.to_thread.run_sync(_keep_alive_query)
    print(f"[{_ts()}] keepalive: run finished -> {result}")
    return result
