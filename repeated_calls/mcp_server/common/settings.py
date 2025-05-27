from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class MCPSettings(BaseSettings):
    """Settings for MCP API Key.

    Pydantic will determine the values of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables
    3. Variables in a .env file if present

    Attributes:
        mcpapikey (str): The MCP API key to connect to the MCP server.
    """
    mcpapikey: SecretStr = SecretStr("")

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", extra="ignore"
    )
