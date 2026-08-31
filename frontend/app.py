"""
Streamlit Web Frontend for A/L BioGenie RAG System.
"""
import streamlit as st

st.set_page_config(
    page_title="A/L BioGenie - Biology RAG Assistant",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 A/L BioGenie: Sri Lanka A/L Biology RAG Tutor")
st.subheader("Unit 2: Chemical and Cellular Basis of Life (English Medium)")

st.sidebar.header("📌 System Information")
st.sidebar.info(
    "**Knowledge Base**: NIE Biology Resource Book (Unit 2), Past Papers & Model Papers.\n\n"
    "**Powered by**: Google Gemini API & Vector RAG Pipeline."
)

# Sample query buttons
st.write("### 💡 Example Practice Questions")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Properties of Water"):
        st.session_state["user_query"] = "What are the physical and chemical properties of water essential for life according to the NIE Resource Book?"
with col2:
    if st.button("Enzyme Inhibition"):
        st.session_state["user_query"] = "Explain competitive vs non-competitive enzyme inhibition with examples."
with col3:
    if st.button("Protein Structure"):
        st.session_state["user_query"] = "Describe primary, secondary, tertiary, and quaternary protein structures."

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User query input
user_input = st.chat_input("Ask any question from Unit 2...") or st.session_state.get("user_query", None)

if user_input:
    # Clear temporary query state
    if "user_query" in st.session_state:
        del st.session_state["user_query"]

    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate bot response
    with st.chat_message("assistant"):
        with st.spinner("Searching NIE Resource Book & generating grounded answer..."):
            response_placeholder = st.empty()
            sample_answer = f"**Answer for**: '{user_input}'\n\n*Note: Configure your GEMINI_API_KEY in `.env` and run the ingestion pipeline to index Unit 2 PDF files for live grounded RAG answers.*"
            response_placeholder.markdown(sample_answer)
            st.session_state.messages.append({"role": "assistant", "content": sample_answer})
