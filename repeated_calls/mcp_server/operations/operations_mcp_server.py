"""Module for managing operations-related MCP data services."""


import asyncio

# ────────────────────────────── std-lib ──────────────────────────────
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated, AsyncIterator, Optional

# ────────────────────────────── 3rd-party ───────────────────────────
import psycopg_pool
from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

from repeated_calls.mcp_server.common.auth import check_api_key

# ────────────────────────────── project ─────────────────────────────
from repeated_calls.mcp_server.common.db import create_pool
from repeated_calls.mcp_server.operations.dao import software_update as su_dao
from repeated_calls.mcp_server.operations.models import SoftwareUpdateResponse
from repeated_calls.utils.loggers import Logger

# ────────────────────────────── runtime set-up ──────────────────────
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

logger = Logger()
logger.info("Starting Repeated Calls MCP server")


# ────────────────────────────── FastMCP lifespan ────────────────────
@dataclass
class AppContext:
    """Holds shared resources for the application."""

    pool: psycopg_pool.AsyncConnectionPool


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[AppContext]:
    """Handle the lifespan of the application context."""
    pool = await create_pool()
    try:
        yield AppContext(pool=pool)
    finally:
        await pool.close()


# ────────────────────────────── FastMCP init ────────────────────────
mcp = FastMCP("Repeated Calls Operations Data Service", lifespan=lifespan)
app = mcp.sse_app


# ────────────────────────────── Tools  ──────────────────────────────
@mcp.tool(description="List software updates, optionally filtered by product")
async def get_software_updates(
    mcp_api_key: Annotated[str, "MCP API Key for authentication"],
    product_id: Annotated[Optional[int], "Optional product id filter"] = None,
    ctx: Context = None,
) -> SoftwareUpdateResponse:
    """Retrieve software updates, optionally filtered by product ID."""
    check_api_key(mcp_api_key)
    start = time.time()
    pool = ctx.request_context.lifespan_context.pool
    try:
        updates = await su_dao.find(pool, product_id)
        return SoftwareUpdateResponse(
            updates=updates,
            count=len(updates),
            query_time_ms=round((time.time() - start) * 1000, 2),
        )
    except Exception as exc:
        logger.error("get_software_updates failed", exc_info=True)
        return SoftwareUpdateResponse(
            updates=[],
            count=0,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=str(exc),
        )


# ────────────────────────────── CLI entrypoint ──────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Repeated Calls Operations MCP Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--transport", choices=["sse", "stdio"], default="sse")
    args = parser.parse_args()

    logger.info("Starting Operations MCP server")
    mcp.run(transport=args.transport)
