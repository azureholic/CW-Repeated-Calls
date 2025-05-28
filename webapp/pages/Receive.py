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

    st.subheader("Incoming Call")
    st.markdown(f"""
    - **Call ID**: `{event.id}`
    - **Customer ID**: `{event.customer_id}`
    - **SDC**: `{event.sdc}`
    - **Timestamp**: `{event.timestamp}`
    """
    )

    # Process the message in the orchestrator
    status.update(label="Processing message...", state="running")
    res = asyncio.run(run_sequence(event))

    if res.call_history:
        with st.expander("**Call history**"):
            st.subheader("Call History")
            st.dataframe([c.model_dump(mode="json") for c in res.call_history], use_container_width=True)

    if res.repeated_call_result:
        with st.expander("**Repeated call**"):
            st.subheader("Repeated Call Analysis")
            st.write(f"**Analysis**: {res.repeated_call_result.analysis}")
            st.write(f"**Conclusion**: {res.repeated_call_result.conclusion}")
            st.write(f"**Repeated call?**: `{res.repeated_call_result.is_repeated_call}`")

    if res.cause_result:
        with st.expander("**Cause analysis**"):
            st.subheader("Cause Analysis")
            st.write(f"**Customer ID**: `{res.cause_result.customer_id}`")
            st.write(f"**Product ID**: `{res.cause_result.product_id}`")
            st.write(f"**Analysis**: {res.cause_result.analysis}")
            st.write(f"**Conclusion**: {res.cause_result.conclusion}")
            st.write(f"**Is relevant?**: `{res.cause_result.is_relevant}`")

    if res.offer_result:
        with st.expander("**Advice**"):
            st.subheader("Advice")
            st.write(f"**Customer ID**: {res.offer_result.customer_id}")
            st.write(f"**Product ID**: {res.offer_result.product_id}")
            for i, c in enumerate(res.offer_result.conversation):
                with st.chat_message(name="human" if i % 2 == 0 else "ai"):
                    st.write(c)

    # Publish the advice to the Service Bus queue
    status.update(label="Publishing advice...", state="running")
    with client:
        with client.get_queue_sender(config.advice_queue) as sender:
            msg = ServiceBusMessage(body=json.dumps(res.model_dump(mode="json")))
            sender.send_messages(msg) # TODO: determine what we want to send here
        
    status.update(label="Advice published!", state="complete")