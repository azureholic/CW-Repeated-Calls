from functools import lru_cache
from typing import List, Optional
from repeated_calls.basic_mcp_server.common.db import fetch_dicts
from ..models import Product


@lru_cache(maxsize=1)           # catalogue rarely changes
async def get_all(pool) -> List[Product]:
    rows = await fetch_dicts(
        pool,
        "SELECT id, name, type, listing_price FROM public.product",
    )
    return [Product(**r) for r in rows]


async def get_by_id(pool, product_id: int) -> Optional[Product]:
    rows = await fetch_dicts(
        pool,
        """
        SELECT id, name, type, listing_price
        FROM public.product WHERE id = %s
        """,
        (product_id,),
    )
    return Product(**rows[0]) if rows else None