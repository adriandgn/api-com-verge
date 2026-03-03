import logging
import os
from functools import lru_cache

import anyio
from supabase import Client, create_client

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_anon_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not supabase_url or not supabase_anon_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY")
    return create_client(supabase_url, supabase_anon_key)


def _keep_alive_query() -> None:
    table = os.getenv("SUPABASE_KEEPALIVE_TABLE", "registrations").strip() or "registrations"
    client = get_supabase_anon_client()
    client.table(table).select("*", count="exact", head=True).execute()


async def run_keep_alive() -> None:
    await anyio.to_thread.run_sync(_keep_alive_query)

