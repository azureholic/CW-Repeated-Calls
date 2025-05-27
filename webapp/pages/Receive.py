import asyncio
import json

import streamlit as st
import utils as su
from azure.servicebus import ServiceBusMessage

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

    event = su.receive_msg(client, config.calls_queue)

    if event is None:
        status.update(label="No messages found!", state="error")
        st.stop()

    st.subheader("CallEvent")
    st.write(event.model_dump(mode="json"))  # TODO: format nicely

    # Process the message in the orchestrator
    status.update(label="Processing message...", state="running")
    res = asyncio.run(run_sequence(event))

    st.subheader("Results")
    st.write(res.model_dump(mode="json"))  # TODO: format nicely

    # Publish the advice to the Service Bus queue
    status.update(label="Publishing advice...", state="running")
    with client:
        with client.get_queue_sender(config.advice_queue) as sender:
            msg = ServiceBusMessage(body=json.dumps(res.model_dump(mode="json")))
            sender.send_messages(msg) # TODO: determine what we want to send here
        
    status.update(label="Advice published!", state="complete")