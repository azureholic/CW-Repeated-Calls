

import json
import asyncio
import os
from azure.servicebus.aio import ServiceBusClient
from repeated_calls.streaming.settings import StreamingSettings
import frontend.utils as us

config = StreamingSettings(queue = 'agent_output_messages')
client = us.get_sb_client(config.connection_string)
us.receive_servicebus_msg(client, config.queue)

# foo = 'a'
# bar = 'b'

# list_var = []

# list_var.append(foo)

# print(list_var)

# list_var.append(bar)

# print(list_var)

# foo = [f"bar_{i}" for i in range(0,5)]

# print(foo)