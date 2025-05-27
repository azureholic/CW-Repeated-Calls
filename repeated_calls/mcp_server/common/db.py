from repeated_calls.utils.loggers import Logger
from typing import Any, Iterable, List, Dict

import psycopg_pool
from repeated_calls.database.settings import DatabaseSettings

logger = Logger()
settings = DatabaseSettings()

async def create_pool() -> psycopg_pool.AsyncConnectionPool:
    """Create a global async connection-pool with retry policy."""
    logger.info("Opening PostgreSQL connection-pool")
    pool = psycopg_pool.AsyncConnectionPool(
        conninfo=(
            f"host={settings.host} "
            f"port={settings.port} "
            f"dbname={settings.database} "
            f"user={settings.user} "
            f"password={settings.password.get_secret_value()}"
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