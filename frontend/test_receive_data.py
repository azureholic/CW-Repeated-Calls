

import json
import asyncio
import os
from azure.servicebus.aio import ServiceBusClient
from repeated_calls.streaming.settings import StreamingSettings
import frontend.utils as us
from repeated_calls.database.schemas import CallEvent
from datetime import datetime


config = StreamingSettings(queue = 'agent_output_messages')
client = us.get_sb_client(config.connection_string)
received_msg = us.receive_servicebus_msg(client, config.queue)

print(type(received_msg))
print(type(received_msg[0]))
print(received_msg)


# # Extract the body as a string (handle bytes/generator if needed)
# body = received_msg.body
# if hasattr(body, "__iter__") and not isinstance(body, (str, bytes)):
#     body = b"".join(body)
# if isinstance(body, bytes):
#     body = body.decode("utf-8")
# else:
#     body = str(body)

# # Convert JSON string to dictionary
# message = json.loads(body)

# ## Sending a message to the servicebus
# message = CallEvent(id = message['id'], 
#     customer_id = message['customer_id'],
#     sdc = message['sdc'],
#     timestamp =  datetime.fromisoformat(message['timestamp']))

