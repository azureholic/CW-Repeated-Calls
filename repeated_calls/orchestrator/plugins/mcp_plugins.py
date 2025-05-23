import os
from contextlib import asynccontextmanager
from semantic_kernel.connectors.mcp import MCPSsePlugin

# Allow overriding from the shell
CUSTOMER_MCP_URL = os.getenv(
    "CUSTOMER_MCP_URL",
    "https://ca-mcp-server-codewith-customer.agreeabletree-63db5af3.westeurope.azurecontainerapps.io/sse",
)
OPERATIONS_MCP_URL = os.getenv(
    "OPERATIONS_MCP_URL",
    "https://ca-mcp-server-codewith-operation.agreeabletree-63db5af3.westeurope.azurecontainerapps.io/sse",
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