import json

import streamlit as st
from azure.servicebus import ServiceBusClient

from repeated_calls.utils.loggers import Logger

logger = Logger()

@st.cache_resource
def get_sb_client(fqn: str, key: str) -> ServiceBusClient:
    client = ServiceBusClient(
        fully_qualified_namespace=fqn,
        credential=key,
    )
    logger.info(f"ServiceBusClient created with endpoint: sb://{client.fully_qualified_namespace}")

    return client

@st.cache_data
def load_scenarios(path: str) -> list[dict]:
    with open(path, "r") as file:
        data = json.load(file)
    logger.info(f"Loaded {len(data)} scenarios from {path}")

    return data