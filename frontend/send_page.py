
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
from repeated_calls.database.schemas import CallEvent
from frontend import utils as us
from repeated_calls.streaming.settings import StreamingSettings
from datetime import datetime



config_ingressqueue = StreamingSettings(queue='customercalls')
config_egressqueue = StreamingSettings(queue='agent_output_messages')
client = us.get_sb_client(config_ingressqueue.connection_string)

def streamlit_sendpage():
    # Importing the json file
    with open('data/scenarios/scenario_specifications.json', 'r') as file:
        pay_load = json.load(file)

    ## Different scenarios
    st.title("Sending calls to servicebus")

    # Selectbox with different scenarios
    option = st.selectbox(
            f"***Pick a scenario:***",
            ([f'Scenario {i+1}' for i in range(len(pay_load))])
            )

    # Description of the selected scenarios + dropdown menu's
    for i in range(len(pay_load)):
        if option == f'Scenario {i+1}':

            message_dict = {
                "id": pay_load[i]['call_event_id'],
                "customer_id": pay_load[i]['customer']['customer_id'],
                "sdc": pay_load[i]['scenario_details']['call_reason'],
                "timestamp": pay_load[i]['dates']['primary_call_date'],
                # add other fields as needed
            }
            message_json = json.dumps(message_dict)
            
            # Header
            col_a, col_b = st.columns([10,1])
            col_a.write(f"***Description of the scenario:*** \
                \n {pay_load[i]['title']}")
            if col_b.button("Send scenario to servicebus"):
                # Purge the ingress queue before starting with main.py
                us.purge_servicebus_queue(client, config_ingressqueue.queue)

                us.send_servicebus_msg(message_json, client, config_ingressqueue.queue)


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
            








