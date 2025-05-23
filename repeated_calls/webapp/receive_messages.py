

import json
import asyncio
import os
from azure.servicebus.aio import ServiceBusClient
from dotenv import load_dotenv

from dotenv import load_dotenv
import os

name_ofthe_queue = 'customercalls'
load_dotenv(dotenv_path='connection-string-servicebus.env')
connection_str = os.getenv('AZURE_SERVICEBUS_CONNECTION_STRING')

async def run():
    # Creating a ServiceBusClient class
    async with ServiceBusClient.from_connection_string(
        conn_str = connection_str,
        logging_enable = True) as servicebus_client:                                        # Defining the servicebusclient class
        receiver = servicebus_client.get_queue_receiver(queue_name = name_ofthe_queue)  # Defining the receiver (linking it to the queue)
        async with receiver:                                                            
            received_messages = await receiver.receive_messages(max_wait_time = 5, max_message_count = 100)     # Storing all the received messages in this variable
            for msg in received_messages:       	                                    # printing all the messages in the queue        
                print(f"---NEW INCOMING CALL--- \
                       \n {str(msg)}\
                       ") 
                await receiver.complete_message(msg)                                    # This removes the message from the queue
            if not received_messages:
                print('No messages in queue')

asyncio.run(run())

