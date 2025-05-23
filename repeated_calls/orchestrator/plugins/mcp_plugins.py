from dotenv import load_dotenv       
import os
from contextlib import asynccontextmanager
from semantic_kernel.connectors.mcp import MCPSsePlugin

load_dotenv()                             

# URLs must be supplied via environment variables / .env
CUSTOMER_MCP_URL   = os.getenv("CUSTOMER_MCP_URL")
OPERATIONS_MCP_URL = os.getenv("OPERATIONS_MCP_URL")

if not CUSTOMER_MCP_URL or not OPERATIONS_MCP_URL:
    raise RuntimeError(
        "CUSTOMER_MCP_URL and OPERATIONS_MCP_URL must be set in the environment "
        "or in an .env file"
    )


@asynccontextmanager
async def customer_plugin():
    async with MCPSsePlugin(
        name="CustomerDataPlugin",
        description="Customer domain data and product related data",
        url=CUSTOMER_MCP_URL,
    ) as plug:
        yield plug


@asynccontextmanager
async def operations_plugin():
    async with MCPSsePlugin(
        name="OperationsDataPlugin",
        description="Operations data",
        url=OPERATIONS_MCP_URL,
    ) as plug:
        yield plug