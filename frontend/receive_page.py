import streamlit as st
import os
from dotenv import load_dotenv
import asyncio                                          # For asynchronous execution in Python
from azure.servicebus.aio import ServiceBusClient       # This class is used to interact with queues asynchronously
from azure.servicebus import ServiceBusMessage          # This class ensures that a single message can be sent to the queue
import time


def streamlit_receivepage():

    name_of_queue = 'agent_output_messages'
    load_dotenv(dotenv_path = "webapp/secrets.env")
    connection_str = os.getenv("connection_str_azure_servicebus")


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







