import streamlit as st

from task31.chat import bootstrap, init_db, load_messages, send_message

st.title("Chat")
st.caption("Task 3.1 — Conversational Core")


@st.cache_resource
def get_client_and_config():
    client, config = bootstrap()
    return client, config


client, config = get_client_and_config()
conn = init_db(config.db_path)

# Always reload persisted history from SQLite so we pick up messages
# from previous sessions (page refresh, CLI usage, etc.)
st.session_state.chat_history = load_messages(conn)

# Render conversation
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message immediately
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Call LLM
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_message(client, config, conn, user_input)

        st.write(result["response"])

        if result["cost"] is not None:
            cols = st.columns(4)
            cols[0].caption(f"Prompt: {result['prompt_tokens']}")
            cols[1].caption(f"Completion: {result['completion_tokens']}")
            cols[2].caption(f"Cost: ${result['cost']:.6f}")
            cols[3].caption(f"Latency: {result['latency_ms']:.0f}ms")

    st.session_state.chat_history.append({"role": "assistant", "content": result["response"]})
