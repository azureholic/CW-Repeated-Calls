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

def streamlit_receivepage():
    st.title("Output of the model")
    max_iter_seconds = 15  # How long to poll for messages

    start_polling = st.button("Start polling for messages")
    placeholder = st.empty()

    if start_polling:
        with st.spinner("Pending ..."):
            time.sleep(2)  # (shorter wait for demo)
            start_time = time.time()
            shown_bodies = set()
            all_messages = []
            while True:
                iter_start = time.time()
                new_messages = us.receive_servicebus_msg(client, config.queue)
                for msg in new_messages:
                    body = msg.body
                    if hasattr(body, "__iter__") and not isinstance(body, (str, bytes)):
                        body = b"".join(body)
                    if isinstance(body, bytes):
                        body = body.decode("utf-8")
                    else:
                        body = str(body)
                    if body not in shown_bodies:
                        shown_bodies.add(body)
                        all_messages.append(body)
                # Optionally sort all_messages here if you have a timestamp or sequence number
                with placeholder.container():
                    for i, body in enumerate(all_messages):
                        st.write(f"Message {i+1}: {body}")
                time.sleep(1)
                iter_end = time.time()
                if (iter_end - iter_start) > max_iter_seconds:
                    st.warning(f"Stopped: One polling iteration took longer than {max_iteration_seconds} seconds.")
                    break
            st.success("Polling finished.")



# def streamlit_receivepage():

#     st.title("Receiving output of the agent")
#     st.write("")
#     received_messages = []

#     # Receive data button
#     if st.button("Receive data output from the model", key='receive_model_output_btn'):
#         with st.spinner('Pending...'):
#             subprocess.run(["python","/home/burgh512/Python_files/Agentic-AI/CW-Repeated-Calls/repeated_calls/orchestrator/main.py"])
#             found_messages = False
#             start_time = time.time()
#             while time.time() - start_time < 30:
#                 time.sleep(0.5)
#                 new_messages = us.receive_servicebus_msg(client, config.queue)
#                 if new_messages:
#                     found_messages = True
#                     for i, msg in enumerate(new_messages):
#                         # Convert generator to bytes if needed
#                         body = msg.body
#                         if hasattr(body, "__iter__") and not isinstance(body, (str, bytes)):
#                             # Convert generator to bytes, then decode
#                             body = b"".join(body)
#                         if isinstance(body, bytes):
#                             body = body.decode("utf-8")
#                         else:
#                             body = str(body)

#                         num_lines = body.count('\n') + 1
#                         unique_key = f"receive_model_data_text_area_{i}_{uuid.uuid4()}"
#                         height = min(max(45 * num_lines, 150), 500)
#                         st.text_area('', value=body, height=height, key=unique_key)            
                                
#             if not found_messages:
#                 st.info('No data retrieved from the model')
















    # # Receive data button
    # if st.button("Receive data output from the model"):
    #     with st.spinner('Pending...'):
    #         start_time = time.time()
    #         while not received_messages:
    #             async def run():
    #                 # Creating a ServiceBusClient class
    #                 async with ServiceBusClient.from_connection_string(
    #                     conn_str = config.connection_string,
    #                     logging_enable = True) as servicebus_client:                                        # Defining the servicebusclient class
    #                     receiver = servicebus_client.get_queue_receiver(queue_name = config.queue)  # Defining the receiver (linking it to the queue)
    #                     async with receiver:                                                            
    #                         received_messages = await receiver.receive_messages(max_wait_time = 5, max_message_count = 100)     # Storing all the received messages in this variable
    #                         for msg in received_messages:       	                                    # printing all the messages in the queue        
    #                             await receiver.complete_message(msg)                                    # This removes the message from the queue
    #                 return received_messages
                
    #             received_messages = asyncio.run(run()) 

    #             if time.time() - start_time > 5:
    #                 break
        
    #     if received_messages:
    #         for i, models_output in enumerate(received_messages):
    #             st.write(models_output)
    #     else:
    #         st.info('No data retrieved from the model')







