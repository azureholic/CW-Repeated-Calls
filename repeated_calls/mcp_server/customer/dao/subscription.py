from typing import List
from repeated_calls.mcp_server.common.db import fetch_dicts
from repeated_calls.mcp_server.customer.models import Subscription


async def by_customer(pool, customer_id: int) -> List[Subscription]:
    sql = """
        SELECT id, customer_id, product_id,
               contract_duration_months, price_per_month,
               start_date, end_date
        FROM public.subscription
        WHERE customer_id = %s
    """
    rows = await fetch_dicts(pool, sql, (customer_id,))
    return [Subscription(**r) for r in rows]