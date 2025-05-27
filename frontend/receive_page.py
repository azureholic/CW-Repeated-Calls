import streamlit as st
import os
from dotenv import load_dotenv
import asyncio                                          # For asynchronous execution in Python
from azure.servicebus.aio import ServiceBusClient       # This class is used to interact with queues asynchronously
from azure.servicebus import ServiceBusMessage          # This class ensures that a single message can be sent to the queue
import time
from repeated_calls.streaming.settings import StreamingSettings
import frontend.utils as us 
import uuid
import subprocess
from repeated_calls.utils.loggers import Logger
import json

logger = Logger()

config_ingressqueue = StreamingSettings(queue='customercalls')
config_egressqueue = StreamingSettings(queue='agent_output_messages')
client = us.get_sb_client(config_ingressqueue.connection_string)

def streamlit_receivepage():
    st.title("Output of the model")
    max_iter_seconds = 20

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "shown_bodies" not in st.session_state:
        st.session_state.shown_bodies = set()
    if "polling" not in st.session_state:
        st.session_state.polling = False

    if st.button("Start polling for messages") and not st.session_state.polling:
        with st.spinner("Polling for messages..."):
            # Purge the egress queue before starting with main.py
            us.purge_servicebus_queue(client, config_egressqueue.queue)

            # Start main.py in the background
            subprocess.Popen(["python", "/home/burgh512/Python_files/Agentic-AI/CW-Repeated-Calls/repeated_calls/orchestrator/main.py"])
            st.session_state.polling = True
            st.session_state.start_time = time.time()
            st.rerun()

    if st.session_state.polling:
        with st.spinner("Polling for messages..."):
            # Only run the polling loop if still active
            if "polling_active" not in st.session_state:
                st.session_state.polling_active = True
            
            while st.session_state.polling_active:
                iter_start = time.time()
                new_messages = us.receive_servicebus_msg(client, config_egressqueue.queue)
                iter_end = time.time()
                iter_duration = iter_end - iter_start

                for msg in new_messages:
                    body = msg.body
                    if hasattr(body, "__iter__") and not isinstance(body, (str, bytes)):
                        body = b"".join(body)
                    if isinstance(body, bytes):
                        body = body.decode("utf-8")
                    else:
                        body = str(body)
                    if body not in st.session_state.shown_bodies:
                        st.session_state.shown_bodies.add(body)
                        st.session_state.messages.append(body)

                for i, body in enumerate(st.session_state.messages):
                    st.write(f"Message {i+1}: {body}")
                
                # Stop if more than 6 messages and no new messages
                if len(st.session_state.messages) > 6 and not new_messages:
                    st.info("Stopped: Service Bus is empty")
                    st.session_state.polling_active = False
                    st.session_state.polling = False
                    break

                # Stop of the iteration takes longer than 15 seconds
                if iter_duration > max_iter_seconds:
                    st.warning(f"Stopped: One polling iteration took longer than {max_iter_seconds} seconds.")
                    st.session_state.polling_active = False
                    st.session_state.polling = False
                    break


                # Sleep a bit before next poll (optional)
                time.sleep(3)
                st.rerun()
