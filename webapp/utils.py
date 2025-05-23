import json

import streamlit as st
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from repeated_calls.utils.loggers import Logger
from repeated_calls.database.tables import CallEvent as CallEventRow
from repeated_calls.database.schemas import CallEvent

logger = Logger()

@st.cache_resource
def get_sb_client(connection_string: str) -> ServiceBusClient:
    client = ServiceBusClient.from_connection_string(connection_string)
    logger.info(f"ServiceBusClient created with endpoint: sb://{client.fully_qualified_namespace}")

    return client


@st.cache_resource
def get_sql_client() -> Engine:
    from repeated_calls.database import engine

    return engine


@st.cache_data
def load_scenarios(path: str) -> list[dict]:
    with open(path, "r") as file:
        data = json.load(file)
    logger.info(f"Loaded {len(data)} scenarios from {path}")

    return data

def send_msg(id: int, client: ServiceBusClient, queue: str, engine: Engine) -> None:
    # Retrieve scenario from database
    q = select(CallEventRow).where(CallEventRow.id == id)
    with Session(engine) as session:
        res = session.execute(q).scalar()

    if res is None:
        raise ValueError(f"CallEvent with ID {id} not found in the database.")
    else:
        # Validate the data using Pydantic
        event = CallEvent(**res.__dict__)

    # Send the message to the queue
    with client:
        with client.get_queue_sender(queue) as sender:
            msg = ServiceBusMessage(body=json.dumps(event.model_dump(mode="json")))
            sender.send_messages(msg)

    log = f"Message sent to queue {queue} with CallEvent ID {event.id}"
    logger.info(log)
    st.toast(log)
    
    