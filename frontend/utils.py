import os
from azure.servicebus.aio import ServiceBusClient       # This class is used to interact with queues asynchronously
from azure.servicebus import ServiceBusMessage          # This class ensures that a single message can be sent to the queue
import asyncio
import time
from dotenv import load_dotenv
from repeated_calls.streaming.settings import StreamingSettings




def get_sb_client(connection_string: str):
    client = ServiceBusClient.from_connection_string(
        conn_str=connection_string,
        logging_enable = True,
    )

    return client


def send_servicebus_msg(message: str, client: ServiceBusClient, queue: str) -> None:
    # Defining the service bus message
    servicebus_msg = ServiceBusMessage(message)

    # Sending the message to the queue
    async def run():    
        sender = client.get_queue_sender(queue_name=queue)
        async with sender:
            await sender.send_messages(servicebus_msg)
        print('\n \
                ---MESSAGE SENT---')  

    asyncio.run(run())


def receive_servicebus_msg(client: ServiceBusClient, queue: str):

    async def run():
        receiver = client.get_queue_receiver(queue_name=queue)
        
        async with receiver:
            received_messages = await receiver.receive_messages(max_message_count=100, max_wait_time=5)
            for msg in received_messages:
                print(f"\n\n---MODELS OUTPUT--- \
                    \n {str(msg)}\
                    ") 
                await receiver.complete_message(msg)                                    # This removes the message from the queue
            if not received_messages:
                print('No messages in queue') 

    asyncio.run(run())








