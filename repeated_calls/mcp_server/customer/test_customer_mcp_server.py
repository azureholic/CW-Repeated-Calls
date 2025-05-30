"""Module for testing customer-related MCP server tools."""

import argparse
import asyncio
import json
import sys
from pprint import pprint

from mcp import ClientSession
from mcp.client.sse import sse_client
from psycopg_pool import AsyncConnectionPool

from repeated_calls.database.settings import DatabaseSettings
from repeated_calls.mcp_server.common.settings import MCPSettings

mcpsettings = MCPSettings()
dbsettings = DatabaseSettings()


async def invoke_tool(session, name: str, params: dict) -> dict:
    """Invoke an MCP tool with the given parameters."""
    print(f"\n─── {name} {params} ───")
    mcp_api_key = mcpsettings.mcpapikey.get_secret_value()
    params = dict(params)
    params["mcp_api_key"] = mcp_api_key
    try:
        resp = await session.call_tool(name, params)
        print(f"  {name} response: {resp}")
        if resp.isError and "Invalid or missing MCP API Key" in resp.content[0].text:
            print(f"  {name} failed: {resp.content[0].text}")
            sys.exit(1)
        if not resp.content or resp.content[0].type != "text":
            raise RuntimeError("Unexpected response payload (no text content)")

        data = json.loads(resp.content[0].text)
        pprint(data)
        if data.get("error"):
            print(f"  {name} returned error: {data['error']}")
            sys.exit(1)
        return data
    except Exception as exc:
        print(f"  {name} failed: {exc}")
        sys.exit(1)


async def create_pool() -> AsyncConnectionPool:
    """Create and return a PostgreSQL connection pool."""
    print("Opening PostgreSQL connection-pool")

    conninfo = (
        f"host={dbsettings.host} "
        f"port={dbsettings.port} "
        f"dbname={dbsettings.database} "
        f"user={dbsettings.user} "
        f"password={dbsettings.password.get_secret_value()}"
    )

    return AsyncConnectionPool(
        conninfo=conninfo,
        min_size=1,
        max_size=10,
        timeout=30,
    )


async def main(host: str, customer_id: int, product_id: int):
    """Run the main test plan for MCP server tools."""
    async with sse_client(f"https://{host}/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            available = {t.name for t in (await session.list_tools()).tools}
            print("Tools exposed by server:", sorted(available))

            # One list with (tool_name, params) we want to run
            test_plan = [
                ("get_historic_call_events", {"customer_id": customer_id}),
                ("get_customer_by_id", {"customer_id": customer_id}),
                ("get_call_event", {"customer_id": customer_id}),
                ("get_subscriptions", {"customer_id": customer_id}),
                ("get_products", {}),  # catalogue (cached)
                ("get_products", {"product_id": product_id}),
                ("get_discounts", {}),  # all discounts
                ("get_discounts", {"product_id": product_id}),
            ]

            for name, params in test_plan:
                if name not in available:
                    print(f"  Skipping {name}: not implemented on the server yet")
                    continue
                await invoke_tool(session, name, params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Quick Customer MCP tool sanity-check")
    parser.add_argument("--host", default="localhost:8000", help="`hostname:port` of MCP server")
    parser.add_argument("--customer", type=int, default=7, help="Customer ID used in tests")
    parser.add_argument("--product", type=int, default=101, help="Product ID used in tests")
    args = parser.parse_args()

    asyncio.run(main(args.host, args.customer, args.product))
