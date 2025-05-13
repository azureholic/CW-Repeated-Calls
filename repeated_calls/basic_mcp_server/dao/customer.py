from typing import Optional
from ..db import fetch_dicts
from ..models import Customer


async def get_by_id(pool, customer_id: int) -> Optional[Customer]:
    sql = """
        SELECT id, name, clv, relation_start_date
        FROM public.customer
        WHERE id = %s
    """
    rows = await fetch_dicts(pool, sql, (customer_id,))
    return Customer(**rows[0]) if rows else None