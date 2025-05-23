import streamlit as st
from send_page import streamlit_sendpage
from receive_page import streamlit_receivepage

st.set_page_config(page_title="Repeated customer contact", page_icon='📞', layout="wide")


page = st.selectbox("Choose a page",["Choose Scenario", "Recieve model's output"])

if page == "Choose Scenario":
    streamlit_sendpage()

if page == "Recieve model's output":
    streamlit_receivepage()


