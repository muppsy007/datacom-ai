import streamlit as st
import plotly.express as px  # noqa: F401 — confirm plotly is available

st.title("Metrics")
st.caption("Evaluation dashboard — metrics across all tasks")

tab_chat, tab_retrieval, tab_agents = st.tabs(["Chat Telemetry", "Retrieval Performance", "Agent Runs"])

with tab_chat:
    st.info("No data available")

with tab_retrieval:
    st.info("No data available")

with tab_agents:
    st.info("No data available")
