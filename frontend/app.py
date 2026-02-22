import os
import streamlit as st
import requests

st.title("FastAPI + Streamlit Integration")

name = st.text_input("Enter your name")

st.set_page_config(
    page_title="My AI App",
    page_icon="🤖",
    layout="wide"
)

st.title("AI Dashboard")

with st.sidebar:
    st.header("Navigation")
    menu = st.radio("Go to", ["Home", "Chat", "Analytics"])

    
if st.button("Send to Backend"):
    response = requests.get(
        "http://localhost:8000/get_api?name=prem",
    )

    if response.status_code == 200:
        st.success(response.json()["result"])
    else:
        st.error("Something went wrong")
