from typing import List
from ..db import fetch_dicts
from ..models import CallEvent


async def latest_by_customer(pool, customer_id: int) -> List[CallEvent]:
    """Return max-1 latest call event for a customer."""
    sql = """
        SELECT id, customer_id, sdc, time_stamp
        FROM public.call_event
        WHERE customer_id = %s
        ORDER BY time_stamp DESC
        LIMIT 1
    """
    rows = await fetch_dicts(pool, sql, (customer_id,))
    return [CallEvent(**r) for r in rows]