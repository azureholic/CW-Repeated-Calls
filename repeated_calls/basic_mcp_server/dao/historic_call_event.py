from typing import List
from ..db import fetch_dicts
from ..models import HistoricCallEvent


async def all_by_customer(pool, customer_id: int) -> List[HistoricCallEvent]:
    sql = """
        SELECT id, customer_id, sdc, call_summary, start_time, end_time
        FROM public.historic_call_event
        WHERE customer_id = %s
        ORDER BY start_time DESC
    """
    rows = await fetch_dicts(pool, sql, (customer_id,))
    return [HistoricCallEvent(**r) for r in rows]