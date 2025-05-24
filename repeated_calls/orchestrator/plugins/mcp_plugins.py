from dotenv import load_dotenv       
import os
from contextlib import asynccontextmanager
from semantic_kernel.connectors.mcp import MCPSsePlugin
from semantic_kernel.functions import kernel_function
from typing import Annotated
from repeated_calls.orchestrator.settings import McpApiKeySettings


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


class McpKeyPlugin:
    """Plugin to provide the MCP API key."""

    @kernel_function
    def get_mcp_api_key(self) -> Annotated[str, "Returns the MCP API key for authenticating with the MCP server."]:
        """Retrieve the MCP API key from environment variables."""
        mcp_api_key = McpApiKeySettings().mcpapikey.get_secret_value()
        if not mcp_api_key:
            return "MCP API key not found in environment."
        return mcp_api_key

