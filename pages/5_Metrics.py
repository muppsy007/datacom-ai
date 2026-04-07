import streamlit as st

from pages.metrics.retrieval import render_retrieval_tab

st.title("Metrics")
st.caption("Evaluation dashboard — metrics across all tasks")

tab_chat, tab_retrieval, tab_agents = st.tabs(
    ["Chat Telemetry", "Retrieval Performance", "Agent Runs"]
)

with tab_chat:
    st.info("No data available")

with tab_retrieval:
    render_retrieval_tab()

with tab_agents:
    st.info("No data available")
