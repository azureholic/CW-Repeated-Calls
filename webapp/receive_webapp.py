import streamlit as st
import os
from dotenv import load_dotenv
import asyncio                                          # For asynchronous execution in Python
from azure.servicebus.aio import ServiceBusClient       # This class is used to interact with queues asynchronously
from azure.servicebus import ServiceBusMessage          # This class ensures that a single message can be sent to the queue
import time

name_of_queue = 'agent_output_messages'
load_dotenv(dotenv_path = "webapp/secrets.env")
connection_str = os.getenv("connection_str_azure_servicebus")


st.set_page_config(page_title="Receiving output of the agent", page_icon='📞', layout="wide")
st.title("Receiving output of the agent")
st.write("")
received_messages = []


# Header
if st.button("Receive data output from the model"):
    with st.spinner('Pending...'):
        start_time = time.time()
        while not received_messages:
            async def run():
                # Creating a ServiceBusClient class
                async with ServiceBusClient.from_connection_string(
                    conn_str = connection_str,
                    logging_enable = True) as servicebus_client:                                        # Defining the servicebusclient class
                    receiver = servicebus_client.get_queue_receiver(queue_name = name_of_queue)  # Defining the receiver (linking it to the queue)
                    async with receiver:                                                            
                        received_messages = await receiver.receive_messages(max_wait_time = 5, max_message_count = 100)     # Storing all the received messages in this variable
                        for msg in received_messages:       	                                    # printing all the messages in the queue        
                            await receiver.complete_message(msg)                                    # This removes the message from the queue
                return received_messages
            
            received_messages = asyncio.run(run()) 

            if time.time() - start_time > 5:
                break
    
    if received_messages:
        for i, models_output in enumerate(received_messages):
            st.write(models_output)
    else:
        st.info('No data retrieved from the model')







        # try:
        #     message_text = str(models_output)
        #     # If the message has a .body attribute, use it (common for ServiceBusReceivedMessage)
        #     if hasattr(models_output, "body"):
        #         # For most cases, body is bytes, so decode it
        #         message_text = models_output.body
        #         if isinstance(message_text, bytes):
        #             message_text = message_text.decode("utf-8")
        #     st.write(message_text)
        # except Exception as e:
        #     st.write(f"Error displaying message: {e}")



# import streamlit as st
# import os
# from dotenv import load_dotenv
# import asyncio
# from azure.servicebus.aio import ServiceBusClient

# # Load environment variables
# name_of_queue = 'agent_output_messages'
# load_dotenv(dotenv_path="webapp/secrets.env")
# connection_str = os.getenv("connection_str_azure_servicebus")

# st.set_page_config(page_title="Receiving output of the agent", page_icon='📞', layout="wide")
# st.title("Receiving output of the agent")
# st.write("")

# async def receive_messages():
#     messages = []
#     try:
#         async with ServiceBusClient.from_connection_string(
#             conn_str=connection_str,
#             logging_enable=False) as servicebus_client:
#             receiver = servicebus_client.get_queue_receiver(queue_name=name_of_queue)
#             async with receiver:
#                 received = await receiver.receive_messages(max_wait_time=5, max_message_count=100)
#                 for msg in received:
#                     # Extract message body
#                     body = msg.body
#                     if isinstance(body, bytes):
#                         body = body.decode("utf-8")
#                     elif isinstance(body, list) and all(isinstance(b, bytes) for b in body):
#                         body = b"".join(body).decode("utf-8")
#                     messages.append(body)
#                     await receiver.complete_message(msg)
#     except Exception as e:
#         messages.append(f"Error: {e}")
#     return messages

# if st.button("Receive data output from the model"):
#     with st.spinner("Receiving messages..."):
#         messages = asyncio.run(receive_messages())
#         if messages:
#             for i, msg in enumerate(messages):
#                 st.markdown(f"**Message {i+1}:**")
#                 st.write(msg)
#         else:
#             st.info("No new messages in queue.")