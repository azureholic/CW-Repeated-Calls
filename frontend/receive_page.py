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


config = StreamingSettings(queue='agent_output_messages')
client = us.get_sb_client(config.connection_string)

def purge_servicebus_queue(client, queue):
    """Remove all messages from the Service Bus queue."""
    while True:
        messages = us.receive_servicebus_msg(client, queue)
        if not messages:
            break  # Queue is empty
        # Messages are completed (removed) in receive_servicebus_msg

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
        # Purge the queue before starting with main.py
        purge_servicebus_queue(client, config.queue)
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
                new_messages = us.receive_servicebus_msg(client, config.queue)
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

                if iter_duration > max_iter_seconds:
                    st.warning(f"Stopped: One polling iteration took longer than {max_iter_seconds} seconds.")
                    st.session_state.polling_active = False
                    st.session_state.polling = False
                    break

                # Sleep a bit before next poll (optional)
                time.sleep(1)
                st.rerun()

# def streamlit_receivepage():
#     st.title("Output of the model")
#     max_iter_seconds = 15  # How long to poll for messages

#     start_polling = st.button("Start polling for messages")
#     placeholder = st.empty()

#     if start_polling:
#         with st.spinner("Pending ..."):
#             subprocess.Popen(["python","/home/burgh512/Python_files/Agentic-AI/CW-Repeated-Calls/repeated_calls/orchestrator/main.py"])
#             time.sleep(2)  # (shorter wait for demo)
#             start_time = time.time()
#             shown_bodies = set()
#             all_messages = []
#             while True:
#                 iter_start = time.time()
#                 new_messages = us.receive_servicebus_msg(client, config.queue)
#                 for msg in new_messages:
#                     body = msg.body
#                     if hasattr(body, "__iter__") and not isinstance(body, (str, bytes)):
#                         body = b"".join(body)
#                     if isinstance(body, bytes):
#                         body = body.decode("utf-8")
#                     else:
#                         body = str(body)
#                     if body not in shown_bodies:
#                         shown_bodies.add(body)
#                         all_messages.append(body)
#                 # Optionally sort all_messages here if you have a timestamp or sequence number
#                 with placeholder.container():
#                     for i, body in enumerate(all_messages):
#                         st.write(f"Message {i+1}: {body}")
#                 time.sleep(1)
#                 iter_end = time.time()
#                 if (iter_end - iter_start) > max_iter_seconds:
#                     st.warning(f"Stopped: One polling iteration took longer than {max_iteration_seconds} seconds.")
#                     break
#             st.success("Polling finished.")
