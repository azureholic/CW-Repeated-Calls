from typing import List, Optional
from ..db import fetch_dicts
from ..models import Discount


async def find(pool, product_id: Optional[int] = None) -> List[Discount]:
    where = "WHERE product_id = %s" if product_id else ""
    params = (product_id,) if product_id else ()
    rows = await fetch_dicts(
        pool,
        f"""
        SELECT id, product_id, minimum_clv, percentage, duration_months
        FROM public.discount
        {where}
        """,
        params,
    )
    return [Discount(**r) for r in rows]