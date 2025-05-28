from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureOpenAISettings(BaseSettings):
    """Settings for Azure OpenAI.

    Pydantic will determine the values of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables (prefixed with `AZURE_OPENAI_`)
    3. Variables in a .env file if present (prefixed with `AZURE_OPENAI_`)

    Attributes:
        endpoint (str): The endpoint URL for the Azure OpenAI service.
        api_key (SecretStr | None): The API key for the Azure OpenAI service. Set to `None` to use
            identity-based authentication (requires correctly assigned IAM roles). Defaults to
            `None`.
        deployment (str): Deployment name of the Chat Completion model.
    """

    endpoint: str
    api_key: SecretStr | None = None
    deployment: str

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", env_prefix="AZURE_OPENAI_", extra="ignore"
    )


class AzureAIFoundrySettings(BaseSettings):
    """Settings for Azure AI Foundry.

    Pydantic will determine the values of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables (prefixed with `AZURE_AI_FOUNDRY_`)
    3. Variables in a .env file if present (prefixed with `AZURE_AI_FOUNDRY_`)

    Attributes:
        endpoint (str): The endpoint for the Azure AI Foundry project.

    """

    endpoint: str
    model_deployment_name: str
   
    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", env_prefix="AZURE_AI_FOUNDRY_", extra="ignore"
    )
    

class AppInsightsSettings(BaseSettings):
    """Settings for Azure Application Insights.

    Pydantic will determine the values of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables (prefixed with `APPLICATIONINSIGHTS_`)
    3. Variables in a .env file if present (prefixed with `APPLICATIONINSIGHTS_`)

    Attributes:
        connection_string (str): The connection string for Azure Application Insights.

    """

    connection_string: str

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", env_prefix="APPLICATIONINSIGHTS_", extra="ignore"
    )
    

class McpApiKeySettings(BaseSettings):
    """Settings for the MCP API Key.

    Pydantic will determine the value of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables (no prefix by default)
    3. Variables in a .env file if present (no prefix by default)

    Attributes:
        mcpapikey (SecretStr): The MCP API key used to authenticate with the MCP server.
    """

    mcpapikey: SecretStr = SecretStr("")

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", extra="ignore"
    )

class McpApiSettings(BaseSettings):
    """Settings for the MCP Key.

    Pydantic will determine the value of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables (no prefix by default)
    3. Variables in a .env file if present (no prefix by default)

    Attributes:
        customer_url (str): The URL for the customer MCP service.
        operations_url (str): The URL for the operations MCP service.
    """

    customer_url: str
    operations_url: str

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", env_prefix="MCP_",extra="ignore"
    )