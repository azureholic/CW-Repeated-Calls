

import json
import asyncio
import os
from azure.servicebus.aio import ServiceBusClient
from dotenv import load_dotenv
import os
from dotenv import load_dotenv


name_of_queue = 'agent_output_messages'
# name_ofthe_queue = 'customercalls'
load_dotenv(dotenv_path = "webapp/secrets.env")
connection_str = os.getenv("connection_str_azure_servicebus")


async def run():
    # Creating a ServiceBusClient class
    async with ServiceBusClient.from_connection_string(
        conn_str = connection_str,
        logging_enable = True) as servicebus_client:                                        # Defining the servicebusclient class
        receiver = servicebus_client.get_queue_receiver(queue_name = name_of_queue)  # Defining the receiver (linking it to the queue)
        async with receiver:                                                            
            received_messages = await receiver.receive_messages(max_wait_time = 5, max_message_count = 100)     # Storing all the received messages in this variable
            for msg in received_messages:     
                print(f"\n\n---MODELS OUTPUT--- \
                    \n {str(msg)}\
                    ") 
                await receiver.complete_message(msg)                                    # This removes the message from the queue
            if not received_messages:
                print('No messages in queue')
            


asyncio.run(run())



