
## Importing data and packages
import streamlit as st
import polars as pl
import os
import json
import json
import asyncio                                          # For asynchronous execution in Python
from azure.servicebus.aio import ServiceBusClient       # This class is used to interact with queues asynchronously
from azure.servicebus import ServiceBusMessage          # This class ensures that a single message can be sent to the queue
from dotenv import load_dotenv

# Importing the path2data and setting up the pages
path_2_data = "/data/"
st.set_page_config(page_title="Customer Calls", page_icon='📞', layout="wide")

# Importing the json file
with open('../data/scenarios/scenario_specifications.json', 'r') as file:
    pay_load = json.load(file)

# Connection string to the azure servicebus
name_ofthe_queue = 'customercalls'
load_dotenv(dotenv_path='connection-string-servicebus.env')
connection_str = os.getenv('AZURE_SERVICEBUS_CONNECTION_STRING')


## Different scenarios
st.title("Test Scenarios")

# Selectbox with different scenarios
option = st.selectbox(
        f"***Pick a scenario:***",
        ([f'Scenario {i+1}' for i in range(len(pay_load))])
        )

# Description of the selected scenarios + dropdown menu's
for i in range(len(pay_load)):
    if option == f'Scenario {i+1}':

        ## Sending a message to the servicebus
        # Defining the function to send a message
        async def send_single_message(sender):                          # Asynchronous function that takes a sender (Instance of the ServiceBusSender class --> from the servicebus.aio SDK) as input
            message = ServiceBusMessage(f"Customer ID: {pay_load[i]['customer']['customer_id']} \
                                       \n Call reason: {pay_load[i]['scenario_details']['call_reason']}")        # This creates a ServiceBusMessage 
                                        
            await sender.send_messages(message)                         # Sends the message asynchronous using the send_message method
            print('message sent')                                       # Await ensures that in the sending time Python can handle other tasks, e.g. sending/receiving messages, web requests, etc).
                                                                        # Async in front of the function allows you to use await inside the function

        # Sending the actual message
        async def run():
            # Create a service bus client using the connection string
            async with ServiceBusClient.from_connection_string(                               # This line creates a new ServiceBusClient called 'servicebus_client' 
                conn_str=connection_str,                                                      # Defines the string for which it has to create the ServiceBusClient object
                logging_enable=True) as servicebus_client:                                    # the with part means that the connection will automatically close when you're done    
                sender = servicebus_client.get_queue_sender(queue_name = name_ofthe_queue)    # Creates an object from the ServiceBusClient that can send messages to the defined queue       
                async with sender:
                    # Send one single message
                    await send_single_message(sender)


        # Header
        col_a, col_b = st.columns([10,1])
        col_a.write(f"***Description of the scenario:*** \
               \n {pay_load[i]['title']}")
        if col_b.button("Run this Scenario"):
            asyncio.run(run())


        # Customer PII
        with st.expander(f"**Customer personal information:**"):
            col1, col2 = st.columns([1,6])
            
            col1.write("Customer name:")
            col2.write(f"{pay_load[i]['customer']['name']}")

            col1.write("Customer ID:")
            col2.write(f"{pay_load[i]['customer']['customer_id']}")
            
            col1.write("Customer CLV:")
            col2.write(f"{pay_load[i]['customer']['clv']}")
        
        # Product information
        with st.expander("**Product info of the customer:**"):
            col1, col2 = st.columns([1,6])
            
            col1.write("Product name:")
            col2.write(f"{pay_load[i]['product']['name']}")

            col1.write("Product type:")
            col2.write(f"{pay_load[i]['product']['type']}")

        # Call dates
        with st.expander("**Previous call dates**"):
            col1, col2 = st.columns([1,6])
            
            col1.write("Primary call date:")
            col2.write(f"{pay_load[i]['dates']['primary_call_date']}")

            col1.write("Most recent call date:")
            col2.write(f"{pay_load[i]['dates']['previous_call_dates']}")

        # Scenario details
        with st.expander("**Scenario details**"):
            col1, col2 = st.columns([1,6])

            with col1:
                st.write("Call reason:")
                st.write("Call history analysis:")
                st.write("Operational insights:")
                st.write("Customer insights:")
                st.write("Recommended system response:")

            with col2:
                st.write(f"{pay_load[i]['scenario_details']['call_reason']}")
                st.write(f"{pay_load[i]['scenario_details']['call_history_analysis']}")
                st.write(f"{pay_load[i]['scenario_details']['operational_insight']}")
                st.write(f"{pay_load[i]['scenario_details']['customer_insights_and_retention_strategy']}")
                
                for j, response in enumerate(pay_load[i]['scenario_details']['recommended_system_response']):
                    st.write(f'{j+1}: {response}')
        




