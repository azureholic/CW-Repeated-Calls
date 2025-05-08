from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Settings for connecting to PostgreSQL.

    Pydantic will determine the values of all fields in the following order of precedence
    (descending order of priority):
    1. Arguments passed to the class constructor
    2. Environment variables (prefixed with `POSTGRES_`)
    3. Variables in a .env file if present (prefixed with `POSTGRES_`)

    Attributes:
        host (str): The hostname of the PostgreSQL server.
        user (str): The username to connect to the PostgreSQL server.
        password (SecretStr): The password to connect to the PostgreSQL server.
        database (str): The name of the database to connect to.
        port (int): The port number of the PostgreSQL server. Defaults to 5432.
    """

    host: str
    user: str
    password: SecretStr
    database: str
    port: int = 5432

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", env_file=".env", env_prefix="POSTGRES_"
    )
