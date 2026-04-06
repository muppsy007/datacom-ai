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
    status = st.status("Running...", expanded=True)
    last_result = None

    for result in run_task(task, force_fail=force_fail):
        last_result = result
        label = "passed" if result.success else "failed"
        status.write(f"**Attempt {result.attempt_number}** — {label}")
        if result.stderr:
            status.code(result.stderr)

    if last_result.success:
        status.update(label=f"All tests passed on attempt {last_result.attempt_number}", state="complete")
    else:
        status.update(label=f"Failed after {last_result.attempt_number} attempts", state="error")

    st.subheader("Final Code")
    st.code(last_result.code)
