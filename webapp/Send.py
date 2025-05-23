import streamlit as st
import utils as su

from repeated_calls.streaming.settings import StreamingSettings
from repeated_calls.utils.loggers import Logger

logger = Logger()
config = StreamingSettings()

st.set_page_config(page_title="Simulate Customer Calls", page_icon=":material/call:", layout="wide")

# Load (cached) ServiceBusClient and scenario data
client = su.get_sb_client(config.connection_string)
engine = su.get_sql_client()
data = su.load_scenarios("data/scenarios/scenario_specifications.json")

st.title("Test call scenarios")


def render_options(raw: int):
    return f"{data[raw]['name']}: {data[raw]['title']}"


# Selection of scenario
option = st.selectbox(
    "***Pick a scenario:***",
    range(len(data)),
    format_func=render_options,
)
scenario = data[option]


# Header
col_a, col_b = st.columns([10, 1])
col_a.write(
    f"***Description of the scenario:*** \
        \n {scenario['title']}"
)
col_b.button(
    "Run this scenario",
    on_click=su.send_msg,
    args=(scenario["call_event_id"], client, config.queue, engine),
)

# Customer PII
with st.expander(f"**Customer personal information:**"):
    col1, col2 = st.columns([1, 6])

    col1.write("Customer name:")
    col2.write(f"{scenario['customer']['name']}")

    col1.write("Customer ID:")
    col2.write(f"{scenario['customer']['customer_id']}")

    col1.write("Customer CLV:")
    col2.write(f"{scenario['customer']['clv']}")

# Product information
with st.expander("**Product info of the customer:**"):
    col1, col2 = st.columns([1, 6])

    col1.write("Product name:")
    col2.write(f"{scenario['product']['name']}")

    col1.write("Product type:")
    col2.write(f"{scenario['product']['type']}")

# Call dates
with st.expander("**Previous call dates**"):
    col1, col2 = st.columns([1, 6])

    col1.write("Primary call date:")
    col2.write(f"{scenario['dates']['primary_call_date']}")

    col1.write("Most recent call date:")
    col2.write(f"{scenario['dates']['previous_call_dates']}")

# Scenario details
with st.expander("**Scenario details**"):
    col1, col2 = st.columns([1, 6])

    with col1:
        st.write("Call reason:")
        st.write("Call history analysis:")
        st.write("Operational insights:")
        st.write("Customer insights:")
        st.write("Recommended system response:")

    with col2:
        st.write(f"{scenario['scenario_details']['call_reason']}")
        st.write(f"{scenario['scenario_details']['call_history_analysis']}")
        st.write(f"{scenario['scenario_details']['operational_insight']}")
        st.write(f"{scenario['scenario_details']['customer_insights_and_retention_strategy']}")

        for j, response in enumerate(scenario["scenario_details"]["recommended_system_response"]):
            st.write(f"{j+1}: {response}")
