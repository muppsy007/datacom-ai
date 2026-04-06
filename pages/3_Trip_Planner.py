import json

import streamlit as st

from task33.travel_planner import plan_trip

st.title("Trip Planner")
st.caption("Task 3.3 — Planning Agent with Tool Calling")

EXAMPLE_PROMPT = "A trip from Christchurch to Auckland, 7th April 2026 to 8th April, Budget of $500"

if "prompt_value" not in st.session_state:
    st.session_state.prompt_value = ""

user_prompt = st.text_input(
    "Describe the trip you want to plan:",
    value=st.session_state.prompt_value,
    placeholder="e.g. A 3-day trip to Queenstown for $800",
)

st.markdown(
    f'<span style="color: grey; font-size: 0.85em;">'
    f"<u>Example Prompt</u>: {EXAMPLE_PROMPT} "
    f'<a href="?use_example=1" target="_self" style="color: #4A90D9;">[use this]</a>'
    f"</span>",
    unsafe_allow_html=True,
)

if st.query_params.get("use_example") == "1":
    st.query_params.clear()
    st.session_state.prompt_value = EXAMPLE_PROMPT
    st.rerun()

if st.button("Plan Trip", disabled=not user_prompt):
    with st.spinner("Planning your trip..."):
        result = plan_trip(user_prompt)

    # Budget and cost summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Budget (NZD)", f"${result['budget']:,.2f}")
    col2.metric("Itinerary Cost (NZD)", f"${result['itinerary']['actual_cost_nzd']:,.2f}")
    col3.metric("LLM Cost (USD)", f"${result['cost']:.6f}")

    # Itinerary
    st.subheader("Itinerary")
    st.json(json.dumps(result["itinerary"], indent=2))

    # Scratchpad steps
    st.subheader("Agent Scratchpad")
    for i, step in enumerate(result["scratchpad"], 1):
        st.markdown(f"**Step {i}** | tool: `{step['tool']}`")
        st.text(f"  reasoning: {step['reasoning']}")
