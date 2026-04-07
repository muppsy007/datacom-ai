import streamlit as st

from pages.metrics.agent import render_agent_tab
from pages.metrics.chat import render_chat_tab
from pages.metrics.retrieval import render_retrieval_tab

st.title("Metrics")
st.caption("Evaluation dashboard — metrics across all tasks")

tab_chat, tab_retrieval, tab_agents = st.tabs(
    ["Chat Telemetry", "Retrieval Performance", "Agent Runs"]
)

with tab_chat:
    render_chat_tab()

with tab_retrieval:
    render_retrieval_tab()

with tab_agents:
    render_agent_tab()
