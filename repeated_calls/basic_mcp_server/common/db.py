import logging
from typing import Any, Iterable, List, Dict

import psycopg_pool
from repeated_calls.basic_mcp_server.common.settings import settings

log = logging.getLogger(__name__)


async def create_pool() -> psycopg_pool.AsyncConnectionPool:
    """Create a global async connection-pool with retry policy."""
    log.info("Opening PostgreSQL connection-pool")
    pool = psycopg_pool.AsyncConnectionPool(
        conninfo=(
            f"host={settings.pghost} "
            f"port={settings.pgport} "
            f"dbname={settings.pgdatabase} "
            f"user={settings.pguser} "
            f"password={settings.pgpassword.get_secret_value()}"
        ),
        min_size=5,
        max_size=20,
        timeout=30,

    )
    await pool.open()           # first connect happens at start-up
    return pool


async def fetch_dicts(
    pool: psycopg_pool.AsyncConnectionPool,
    sql: str,
    params: Iterable[Any] | tuple = (),
) -> List[Dict[str, Any]]:
    """Run a query and return every row as a dict (column-name → value)."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = await cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]