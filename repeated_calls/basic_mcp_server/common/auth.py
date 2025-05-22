from repeated_calls.basic_mcp_server.common.settings import settings

API_KEY = settings.mcpapikey.get_secret_value()

def check_api_key(api_key: str):
    """
    Validates the provided API key against the configured server API key.

    Args:
        api_key (str): The API key provided by the client.

    Raises:
        Exception: If the API key is missing or does not match the configured value.
    """
    if api_key != API_KEY:
        raise Exception("401: Invalid or missing API Key")