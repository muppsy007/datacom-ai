"""
Streamlit UI for the Datacom AI tasks.
Landing page with navigation to each task.
"""

import sys
from pathlib import Path

# Add task directories to the Python path so their internal imports resolve.
# This runs once on app load before any page is rendered.
_root = Path(__file__).resolve().parent
for _task_dir in ["task31", "task32", "task33", "task34"]:
    _path = str(_root / _task_dir)
    if _path not in sys.path:
        sys.path.insert(0, _path)

import streamlit as st


def home():
    st.title("Datacom AI Assessment")
    st.markdown("""
This application demonstrates four AI-powered tasks:

- **Chat** — Task 3.1: Conversational chatbot with message history and cost tracking
- **QA** — Task 3.2: RAG-based question answering with document retrieval and citations
- **Trip Planner** — Task 3.3: Planning agent with tool calling and budget constraints
- **Code Assistant** — Task 3.4: Self-healing code generator with automated test retry loop

Use the sidebar to navigate to each task.
""")


pg = st.navigation([
    st.Page(home, title="Home", icon="🏠"),
    st.Page("pages/1_Chat.py", title="Chat", icon="💬"),
    st.Page("pages/2_QA.py", title="QA", icon="📚"),
    st.Page("pages/3_Trip_Planner.py", title="Trip Planner", icon="✈️"),
    st.Page("pages/4_Code_Assistant.py", title="Code Assistant", icon="💻"),
])

pg.run()
