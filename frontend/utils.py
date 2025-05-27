import os
from azure.servicebus.aio import ServiceBusClient       # This class is used to interact with queues asynchronously
from azure.servicebus import ServiceBusMessage          # This class ensures that a single message can be sent to the queue
import asyncio
import time
from dotenv import load_dotenv
from repeated_calls.streaming.settings import StreamingSettings
from repeated_calls.utils.loggers import Logger
import json


logger = Logger()



def get_sb_client(connection_string: str):
    client = ServiceBusClient.from_connection_string(
        conn_str=connection_string,
        logging_enable = True,
    )

    return client

async def _send_async(message: str, client: ServiceBusClient, queue: str):
    if queue == 'customercalls':
        queue_name = 'ingress queue'
    elif queue == 'agent_output_messages':
        queue_name = 'egress queue' 
    
    try:
        sb_message = ServiceBusMessage(message)
        sender = client.get_queue_sender(queue_name=queue)
        async with sender:
            await sender.send_messages(sb_message)
        logger.debug(f"Message sent to the {queue_name} of the servicebus")
    except Exception as e:
        logger.error(f"Failed to send message to the {queue_name} of the servicebus: {e}")


def send_servicebus_msg(message: str, client: ServiceBusClient, queue: str):
    """Send a service bus message from sync or async code (guaranteed delivery)."""

    try:
        loop = asyncio.get_running_loop()
        # Inside an existing event loop → schedule the task safely
        asyncio.create_task(_send_async(message, client, queue))
    except RuntimeError:
        # Not inside an event loop → safe to run synchronously
        asyncio.run(_send_async(message, client, queue))
    except Exception as e:
        # Fallback for rare edge cases (like nested loops in notebooks)
        def run_in_thread():
            asyncio.run(_send_async(message, client, queue))


def receive_servicebus_msg(client: ServiceBusClient, queue: str) -> str:

    if queue == 'customercalls':
        queue_name = 'ingress queue'
    elif queue == 'agent_output_messages':
        queue_name = 'egress queue' 


    async def run():
        receiver = client.get_queue_receiver(queue_name=queue)
        
        async with receiver:
            received_messages = await receiver.receive_messages(max_message_count=100, max_wait_time=15)
            
            i = 0
            for msg in received_messages:
                await receiver.complete_message(msg)
                i += 1                                    # This removes the message from the queue
            
            if i ==0:
                logger.debug(f"No messages received from the {queue_name} of the servicebus")
            else:
                logger.debug(f"received {i} messages from the {queue_name} of the servicebus") 
        
        return received_messages

    received_messages = asyncio.run(run())
    
    return received_messages


def create_one_message(messages: list[str]) -> str:
    return "\n".join(messages)


def transform_servicebus_msg_2_dict(received_msg: list):
    logger.debug(f"Transform sb msg 2 dict fu() --> message type inserted: {type(received_msg)} with length: {len(received_msg)}")
    msg = received_msg[0]
    body = msg.body

    logger.debug(f"Transform sb msg 2 dict fu() --> body type before processing: {type(body)}")

    if hasattr(body, "__iter__") and not isinstance(body, (str, bytes)):
        body = b"".join(body)
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    elif not isinstance(body, str):
        body = str(body)

    logger.debug(f"Transform sb msg 2 dict fu() --> body type after processing: {type(body)}")

    # Now parse the JSON
    dict_message = json.loads(body)

    logger.debug(f"Transform sb msg 2 dict fu() --> message type to return: {type(dict_message)}")

    return dict_message


def purge_servicebus_queue(client: ServiceBusClient, queue: str) -> None:
    """Remove all messages from the Service Bus queues."""
    if queue == 'customercalls':
        queue_name = 'ingress queue'
    elif queue == 'agent_output_messages':
        queue_name = 'egress queue' 
    
    while True:
        messages = receive_servicebus_msg(client, queue)
        logger.debug(f"Removed {len(messages)} messages from the {queue_name}")
        if not messages:
            logger.debug(f"{queue_name} of the servicebus was already empty")
            break  # Queue is empty
        # Messages are completed (removed) in receive_servicebus_msg



