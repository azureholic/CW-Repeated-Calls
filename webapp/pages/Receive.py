import asyncio

import streamlit as st
import utils as su

from repeated_calls.orchestrator.main import run_sequence
from repeated_calls.streaming.settings import StreamingSettings
from repeated_calls.utils.loggers import Logger

logger = Logger()
config = StreamingSettings()

st.set_page_config(page_title="Process Customer Calls", page_icon=":material/call:", layout="wide")

st.title("Process call scenarios")

# Load (cached) ServiceBusClient
client = su.get_sb_client(config.connection_string)

if st.button("Process message", use_container_width=True):
    status = st.status("Receiving message...", expanded=True)

    event = su.receive_msg(client, config.queue)

    if event is None:
        status.update(label="No messages found!", state="error")
        st.stop()

    st.subheader("CallEvent")
    st.write(event.model_dump(mode="json"))  # TODO: format nicely

    # Process the message in the orchestrator
    status.update(label="Processing message...", state="running")
    res = asyncio.run(run_sequence(event))

    status.update(label="Message processed successfully!", state="complete")
    st.subheader("Results")
    st.write(res.model_dump(mode="json"))  # TODO: format nicely
