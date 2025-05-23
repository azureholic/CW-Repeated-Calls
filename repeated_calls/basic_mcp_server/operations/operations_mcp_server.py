"""
Repeated Contact Handling – Operations MCP data service
"""

# ────────────────────────────── std-lib ──────────────────────────────
import sys
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Optional, AsyncIterator

# ────────────────────────────── 3rd-party ───────────────────────────
import psycopg_pool
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

# ────────────────────────────── project ─────────────────────────────
from repeated_calls.basic_mcp_server.common.db import create_pool
from repeated_calls.basic_mcp_server.operations.models import (
    # domain + response models
    SoftwareUpdate, SoftwareUpdateResponse
)
from repeated_calls.basic_mcp_server.operations.dao import (
    software_update as su_dao
)

# ────────────────────────────── runtime set-up ──────────────────────
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s | %(message)s",
)
logger = logging.getLogger("repeated_calls_operations_mcp")
logger.info("Starting Repeated Calls MCP server")

# ────────────────────────────── FastMCP lifespan ────────────────────
@dataclass
class AppContext:
    pool: psycopg_pool.AsyncConnectionPool


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[AppContext]:
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
    product_id: Annotated[Optional[int], "Optional product id filter"] = None,
    ctx: Context = None,
) -> SoftwareUpdateResponse:
    """Query public.software_update with optional product filter."""
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
            updates=[], count=0,
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
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.getLogger("repeated_calls_operations_mcp").setLevel(args.log_level.upper())

    logger.info("Starting Operations MCP server")
    mcp.run(transport=args.transport)
