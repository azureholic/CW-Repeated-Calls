from typing import List
from repeated_calls.mcp_server.common.db import fetch_dicts
from repeated_calls.mcp_server.customer.models import CallEvent


async def latest_by_customer(pool, customer_id: int) -> List[CallEvent]:
    """Return max-1 latest call event for a customer."""
    sql = """
        SELECT id, customer_id, sdc, timestamp
        FROM public.call_event
        WHERE customer_id = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """
    rows = await fetch_dicts(pool, sql, (customer_id,))
    return [CallEvent(**r) for r in rows]