import streamlit as st

from task34.code_assistant import run_task

st.title("Code Assistant")
st.caption("Task 3.4 — Self-Healing Code Generator")

EXAMPLE_PROMPT = "write a Rust struct called Matrix that supports 2x2 matrix multiplication, with tests"

if "code_task_value" not in st.session_state:
    st.session_state.code_task_value = ""

task = st.text_input(
    "Describe your coding task:",
    value=st.session_state.code_task_value,
    placeholder="e.g. write quicksort in Rust",
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
    st.session_state.code_task_value = EXAMPLE_PROMPT
    st.rerun()

force_fail = st.checkbox("Force fail (demo retry loop)")

if st.button("Run", disabled=not task):
    with st.spinner("Generating and testing code..."):
        outcome = run_task(task, force_fail=force_fail)

    if outcome.success:
        st.success(f"All tests passed on attempt {outcome.total_attempts}")
    else:
        st.error(f"Failed after {outcome.total_attempts} attempts")
        if outcome.last_error:
            st.subheader("Last Error")
            st.code(outcome.last_error)

    st.subheader("Final Code")
    st.code(outcome.final_code)
