import json

import streamlit as st
import utils as su

from repeated_calls.database.schemas import CallEvent
from repeated_calls.streaming.settings import StreamingSettings
from repeated_calls.utils.loggers import Logger

logger = Logger()
config = StreamingSettings()

st.set_page_config(page_title="Process Customer Calls", page_icon=":material/call:", layout="wide")

# Load (cached) ServiceBusClient
client = su.get_sb_client(config.connection_string)

# TODO: read message queueu

# TODO: process message queue messages
# Convert to Pydantic model using event = CallEvent(**json.loads(mesage))
# Call orchestrator
# Display results