"""
Repeated Contact Handling – Customer MCP data service
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
from repeated_calls.basic_mcp_server.customer.dao import call_event as call_event_dao
from repeated_calls.basic_mcp_server.common.db import create_pool
from repeated_calls.basic_mcp_server.common.auth import check_api_key
from repeated_calls.basic_mcp_server.customer.models import (
    # domain + response models
    CallEvent, CallEventResponse,
    HistoricCallEvent, HistoricCallEventResponse,
    Customer, CustomerResponse,
    Subscription, SubscriptionResponse,
    Product, ProductResponse,
    Discount, DiscountResponse
)
from repeated_calls.basic_mcp_server.customer.dao import (
    historic_call_event as hce_dao,
    customer as customer_dao,
    subscription as subscription_dao,
    product as product_dao,
    discount as discount_dao
)

# ────────────────────────────── runtime set-up ──────────────────────
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s | %(message)s",
)
logger = logging.getLogger("repeated_calls_customer_mcp")
logger.info("Starting Repeated Calls Customer MCP server")

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
mcp = FastMCP("Repeated Calls Customer Data Service", lifespan=lifespan)
app = mcp.sse_app

# ────────────────────────────── Tools  ──────────────────────────────
@mcp.tool(description="Return the latest call event for a customer")
async def get_call_event(
    customer_id: Annotated[int, "Customer ID, e.g. 42"],
    mcp_api_key: Annotated[str, "MCP API Key for authentication"],
    ctx: Context = None,
) -> CallEventResponse:
    """Fetch one most-recent row from public.call_event for the given customer."""
    check_api_key(mcp_api_key)
    start = time.time()
    pool = ctx.request_context.lifespan_context.pool
    try:
        events = await call_event_dao.latest_by_customer(pool, customer_id)
        return CallEventResponse(
            events=events,
            count=len(events),
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=None if events else f"No call event for customer {customer_id}",
        )
    except Exception as exc:
        logger.error("get_call_event failed", exc_info=True)
        return CallEventResponse(
            events=[], count=0,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=str(exc),
        )


@mcp.tool(description="List all historic call events for a customer")
async def get_historic_call_events(
    customer_id: Annotated[int, "Customer ID"],
    mcp_api_key: Annotated[str, "MCP API Key for authentication"],
    ctx: Context = None,
) -> HistoricCallEventResponse:
    """Return every historic call event row belonging to the customer."""
    check_api_key(mcp_api_key)
    start = time.time()
    pool = ctx.request_context.lifespan_context.pool
    try:
        events = await hce_dao.all_by_customer(pool, customer_id)
        return HistoricCallEventResponse(
            events=events,
            count=len(events),
            query_time_ms=round((time.time() - start) * 1000, 2),
        )
    except Exception as exc:
        logger.error("get_historic_call_events failed", exc_info=True)
        return HistoricCallEventResponse(
            events=[], count=0,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=str(exc),
        )


@mcp.tool(description="Return a single customer record by id")
async def get_customer_by_id(
    customer_id: Annotated[int, "Customer ID"],
    mcp_api_key: Annotated[str, "MCP API Key for authentication"],
    ctx: Context = None,
) -> CustomerResponse:
    """Look up one row in public.customer."""
    check_api_key(mcp_api_key)
    start = time.time()
    pool = ctx.request_context.lifespan_context.pool
    try:
        cust = await customer_dao.get_by_id(pool, customer_id)
        return CustomerResponse(
            customer=cust,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=None if cust else f"No customer {customer_id}",
        )
    except Exception as exc:
        logger.error("get_customer_by_id failed", exc_info=True)
        return CustomerResponse(
            customer=None,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=str(exc),
        )


@mcp.tool(description="List every subscription a customer currently owns")
async def get_subscriptions(
    customer_id: Annotated[int, "Customer ID"],
    mcp_api_key: Annotated[str, "MCP API Key for authentication"],
    ctx: Context = None,
) -> SubscriptionResponse:
    """Query public.subscription filtered by customer_id."""
    check_api_key(mcp_api_key)
    start = time.time()
    pool = ctx.request_context.lifespan_context.pool
    try:
        subs = await subscription_dao.by_customer(pool, customer_id)
        return SubscriptionResponse(
            subscriptions=subs,
            count=len(subs),
            query_time_ms=round((time.time() - start) * 1000, 2),
        )
    except Exception as exc:
        logger.error("get_subscriptions failed", exc_info=True)
        return SubscriptionResponse(
            subscriptions=[],
            count=0,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=str(exc),
        )


@mcp.tool(description="Return product catalogue or a single product")
async def get_products(
    mcp_api_key: Annotated[str, "MCP API Key for authentication"],
    product_id: Annotated[Optional[int], "Optional product id filter"] = None,
    ctx: Context = None,
) -> ProductResponse:
    """Uses the cached catalogue; if product_id is given, returns at most one item."""
    check_api_key(mcp_api_key)
    start = time.time()
    pool = ctx.request_context.lifespan_context.pool
    try:
        if product_id is None:
            items = await product_dao.get_all(pool)         
        else:
            p = await product_dao.get_by_id(pool, product_id)
            items = [p] if p else []
        return ProductResponse(
            products=items,
            count=len(items),
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=None if items else f"No product {product_id}" if product_id else None,
        )
    except Exception as exc:
        logger.error("get_products failed", exc_info=True)
        return ProductResponse(
            products=[], count=0,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=str(exc),
        )

@mcp.tool(description="Return active discount rules, optionally filtered by product")
async def get_discounts(
    mcp_api_key: Annotated[str, "MCP API Key for authentication"],
    product_id: Annotated[Optional[int], "Optional product id filter"] = None,
    ctx: Context = None,
) -> DiscountResponse:
    """Query public.discount with optional product filter."""
    check_api_key(mcp_api_key)
    start = time.time()
    pool = ctx.request_context.lifespan_context.pool
    try:
        discounts = await discount_dao.find(pool, product_id)
        return DiscountResponse(
            discounts=discounts,
            count=len(discounts),
            query_time_ms=round((time.time() - start) * 1000, 2),
        )
    except Exception as exc:
        logger.error("get_discounts failed", exc_info=True)
        return DiscountResponse(
            discounts=[], count=0,
            query_time_ms=round((time.time() - start) * 1000, 2),
            error=str(exc),
        )

# ────────────────────────────── CLI entrypoint ──────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Repeated Calls Customer MCP Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--transport", choices=["sse", "stdio"], default="sse")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.getLogger("repeated_calls_customer_mcp").setLevel(args.log_level.upper())

    logger.info("Starting Customer MCP server")
    mcp.run(transport=args.transport)
