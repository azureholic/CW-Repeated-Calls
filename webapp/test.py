import streamlit as st
import utils as su

from repeated_calls.streaming.settings import StreamingSettings
from repeated_calls.utils.loggers import Logger

logger = Logger()
config = StreamingSettings()

# Load (cached) ServiceBusClient and scenario data
client = su.get_sb_client(config.connection_string)
engine = su.get_sql_client()
data = su.load_scenarios("data/scenarios/scenario_specifications.json")

test = su.send_msg(2, client, config.queue, engine)



