import streamlit as st

from task32.qa import ask_question, create_client

st.title("QA")
st.caption("Task 3.2 — RAG Question Answering")

EXAMPLES = [
    "What is the optimal tyre pressure for a Holden Colorado?",
    "Which dictionary does the US government adhere to for official spelling?",
    "How many books are in the New Testament?",
]


@st.cache_resource
def get_client():
    return create_client()


if "qa_question_value" not in st.session_state:
    st.session_state.qa_question_value = ""

question = st.text_input(
    "Ask a question:",
    value=st.session_state.qa_question_value,
    placeholder="e.g. What colour is Moby Dick?",
)

def on_pill_select():
    picked = st.session_state.qa_pills
    if picked:
        st.session_state.qa_question_value = picked

st.pills(
    "Sample Prompts",
    EXAMPLES,
    selection_mode="single",
    default=None,
    key="qa_pills",
    on_change=on_pill_select,
    label_visibility="visible",
)

if st.button("Ask", disabled=not question):
    client = get_client()

    try:
        with st.spinner("Searching and generating answer..."):
            result = ask_question(question, client)
    except Exception as e:
        if "does not exist" in str(e).lower() or "collection" in str(e).lower():
            st.error(
                "The Chroma collection has not been ingested yet. "
                "Run the ingestion script first: `python task32/ingest.py`"
            )
        else:
            st.error(f"Error: {e}")
        st.stop()

    # Answer
    st.subheader("Answer")
    st.write(result["answer"])

    # Sources
    if result["sources"]:
        st.subheader("Sources")
        for i, src in enumerate(result["sources"], 1):
            st.markdown(f"**[{i}]** {src['title']}, chunk {src['chunk_index']}")

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Retrieval", f"{result['retrieve_ms']:.0f}ms")
    col2.metric("LLM", f"{result['llm_ms']:.0f}ms")
