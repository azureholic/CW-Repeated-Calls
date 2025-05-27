from typing import List, Optional
from repeated_calls.mcp_server.common.db import fetch_dicts
from repeated_calls.mcp_server.operations.models import SoftwareUpdate


async def find(pool, product_id: Optional[int] = None) -> List[SoftwareUpdate]:
    where = "WHERE product_id = %s" if product_id else ""
    params = (product_id,) if product_id else ()
    rows = await fetch_dicts(
        pool,
        f"""
        SELECT id, product_id, rollout_date, type
        FROM public.software_update
        {where}
        """,
        params,
    )
    return [SoftwareUpdate(**r) for r in rows]