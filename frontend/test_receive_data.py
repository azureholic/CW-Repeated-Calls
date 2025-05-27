

import json
import asyncio
import os
from azure.servicebus.aio import ServiceBusClient
from repeated_calls.streaming.settings import StreamingSettings
import frontend.utils as us
from repeated_calls.database.schemas import CallEvent
from datetime import datetime


config = StreamingSettings(queue = 'customercalls')
client = us.get_sb_client(config.connection_string)
received_msg = us.receive_servicebus_msg(client, config.queue)

print(type(received_msg))

msg = received_msg[0]
body = msg.body

print(f"body type before processing: {type(body)}")

if hasattr(body, "__iter__") and not isinstance(body, (str, bytes)):
    body = b"".join(body)
if isinstance(body, bytes):
    body = body.decode("utf-8")
elif not isinstance(body, str):
    body = str(body)

print(f"body type after processing: {type(body)}")

# Now parse the JSON
data = json.loads(body)

print(f"data = {data}")
print(f"type of data: {type(data)}")
