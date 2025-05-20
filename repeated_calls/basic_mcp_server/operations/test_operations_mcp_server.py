import argparse
import asyncio
import json
import sys
from pprint import pprint
from mcp import ClientSession
from mcp.client.sse import sse_client
from psycopg_pool import AsyncConnectionPool
from repeated_calls.basic_mcp_server.common.settings import settings  


async def invoke_tool(session, name: str, params: dict) -> dict:
    """Generic wrapper to call an MCP tool and pretty-print the result."""
    print(f"\n─── {name} {params} ───")
    try:
        resp = await session.call_tool(name, params)
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
    """Create a PostgreSQL connection-pool with retry policy."""
    log.info("Opening PostgreSQL connection-pool")

    conninfo = (
        f"host={settings.pghost} "    
        f"port={settings.pgport} "
        f"dbname={settings.pgdatabase} "
        f"user={settings.pguser} "
        f"password={settings.pgpassword}"
    )

    return AsyncConnectionPool(
        conninfo=conninfo,
        min_size=1,
        max_size=10,
        timeout=30,                 
    )


async def main(host: str, product_id: int):
    async with sse_client(f"https://{host}/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            available = {t.name for t in (await session.list_tools()).tools}
            print("Tools exposed by server:", sorted(available))

            # One list with (tool_name, params) we want to run
            test_plan = [
                ("get_software_updates",     {}),                       # all updates
                ("get_software_updates",     {"product_id": product_id}),
            ]

            for name, params in test_plan:
                if name not in available:
                    print(f"  Skipping {name}: not implemented on the server yet")
                    continue
                await invoke_tool(session, name, params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Quick Operations MCP tool sanity-check")
    parser.add_argument("--host", default="localhost:8000", help="`hostname:port` of MCP server")
    parser.add_argument("--product",  type=int, default=101, help="Product ID used in tests")
    args = parser.parse_args()

    asyncio.run(main(args.host, args.product))
