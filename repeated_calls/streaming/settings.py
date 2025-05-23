"""Settings for connecting to the streaming service."""

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StreamingSettings(BaseSettings):
    """Settings for connecting to the streaming service.

    Pydantic will determine the values of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables (prefixed with `AZURE_SERVICEBUS_`)
    3. Variables in a .env file if present (prefixed with `AZURE_SERVICEBUS_`)

    Attributes:
        endpoint (str): The endpoint of the Azure Service Bus.
        key (SecretStr): The key to connect to the Azure Service Bus.
    """

    endpoint: str
    key: SecretStr
    queue: str = "customercalls"

    @computed_field
    @property
    def connection_string(self) -> str:
        """Constructs the connection string for Azure Service Bus."""
        return f"Endpoint=sb://{self.endpoint};SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey={self.key.get_secret_value()}"

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", env_prefix="AZURE_SERVICEBUS_", extra="ignore"
    )
