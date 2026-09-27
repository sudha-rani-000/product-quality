import streamlit as st

from services.ai_assistant import build_quality_assistant_reply


def render_assistant_page(user):
    st.title("🤖 AI Quality Assistant")
    st.caption("Ask questions about the current inspection or quality checks.")

    if "assistant_history" not in st.session_state:
        st.session_state.assistant_history = []

    inspection = st.session_state.get("current_inspection")
    if not inspection:
        st.info("No active inspection available yet. Complete a product inspection to ask questions about the result.")
        return

    for message in st.session_state.assistant_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Ask about your inspection...")
    if prompt:
        st.session_state.assistant_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        response = build_quality_assistant_reply(prompt, inspection)
        st.session_state.assistant_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
