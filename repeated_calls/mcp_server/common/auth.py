"""Module for handling authentication and API key validation."""

from repeated_calls.mcp_server.common.settings import MCPSettings

mcp_settings = MCPSettings()
MCP_API_KEY = mcp_settings.mcpapikey.get_secret_value()


def check_api_key(mcp_api_key: str):
    """
    Validate the provided MCP API key against the configured server MCP API key.

    Args:
        mcp_api_key (str): The MCP API key provided by the client.

    Raises:
        Exception: If the MCP API key is missing or does not match the configured value.
    """
    if mcp_api_key != MCP_API_KEY:
        raise Exception("401: Invalid or missing MCP API Key")
