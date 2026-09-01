"""
Streamlit Web Application for CellMate RAG Assistant.
Provides an interactive chat interface, quick prompt pills, sidebar configuration,
health diagnostics, and expandable source citation drawer for G.C.E. A/L Biology students.

Usage:
    streamlit run src/ui/app.py
"""
import sys
import time
import requests
from pathlib import Path

# Add project root to path for clean imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from src.config import TOP_K, LLM_MODEL, EMBEDDING_MODEL
from src.rag.pipeline import CellMateRAG


# ─── Page Configuration & Custom CSS ───────────────────────────────────────────

st.set_page_config(
    page_title="CellMate — A/L Biology AI Assistant",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Tailwind-inspired CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .badge-unit {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .source-box {
        background-color: #F3F4F6;
        border-left: 4px solid #3B82F6;
        padding: 0.75rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State Initialization ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Hello! I am CellMate**, your AI Study Assistant for **Sri Lanka G.C.E. Advanced Level Biology (Unit 02: Chemical and Cellular Basis of Life)**.\n\n"
                "Ask me anything about water properties, biological molecules, enzymes, cell membranes, or cellular energy. "
                "Every answer is strictly grounded in official NIE Resource Book materials with page citations!"
            ),
            "citations": [],
            "retrieved_chunks": []
        }
    ]

if "rag_pipeline" not in st.session_state:
    try:
        st.session_state.rag_pipeline = CellMateRAG()
    except Exception as e:
        st.session_state.rag_pipeline = None


# ─── Sidebar Controls & System Health ───────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/color/96/dna.png", width=64)
    st.title("CellMate Control Panel")
    st.markdown("---")

    st.subheader("⚙️ System Configuration")

    api_mode = st.radio(
        "Backend Connection Mode",
        options=["Direct Python RAG", "FastAPI REST API (port 8000)"],
        index=0,
        help="Choose whether Streamlit calls local Python code directly or communicates via HTTP REST API."
    )

    top_k_val = st.slider(
        "Context Retrieval (Top-K Chunks)",
        min_value=1,
        max_value=8,
        value=TOP_K,
        help="Number of NIE textbook passages to retrieve per question."
    )

    doc_filter_choice = st.selectbox(
        "Document Filter",
        options=["All Materials", "Resource Book Only", "Past Papers Only", "Model Papers Only"],
        index=0
    )

    filter_map = {
        "All Materials": None,
        "Resource Book Only": "resource_book",
        "Past Papers Only": "past_paper",
        "Model Papers Only": "model_paper"
    }
    selected_doc_filter = filter_map[doc_filter_choice]

    st.markdown("---")
    st.subheader("📊 System Health & Status")

    # Check vector DB status
    if st.session_state.rag_pipeline and st.session_state.rag_pipeline.retriever:
        try:
            stats = st.session_state.rag_pipeline.retriever.store_manager.get_stats()
            st.success(f"🟢 **Vector Store**: Connected ({stats.get('total_chunks', 0)} chunks)")
        except Exception:
            st.warning("🟡 **Vector Store**: Reconnecting...")
    else:
        st.error("🔴 **Vector Store**: Disconnected")

    st.info(f"🤖 **LLM Model**: `{LLM_MODEL}`\n\n🔢 **Embedder**: `{EMBEDDING_MODEL}`")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()


# ─── Main Header Banner ────────────────────────────────────────────────────────

st.markdown('<div class="main-header">🧬 CellMate — A/L Biology AI Study Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    '<span class="badge-unit">Unit 02: Chemical & Cellular Basis of Life</span> &nbsp;'
    'Grounded in official NIE Sri Lanka G.C.E. A/L Resource Book'
    '</div>',
    unsafe_allow_html=True
)


# ─── Quick Prompt Pills ────────────────────────────────────────────────────────

st.markdown("##### 💡 Quick Practice Questions:")
col1, col2, col3, col4 = st.columns(4)

selected_pill = None
with col1:
    if st.button("🧪 Water Properties", use_container_width=True):
        selected_pill = "What are the unique properties of water that make it essential for life?"
with col2:
    if st.button("🔬 Enzyme Inhibition", use_container_width=True):
        selected_pill = "Explain the difference between competitive and non-competitive enzyme inhibition."
with col3:
    if st.button("⚡ Role of ATP", use_container_width=True):
        selected_pill = "What is the role of ATP in cellular metabolism?"
with col4:
    if st.button("🧬 DNA Structure", use_container_width=True):
        selected_pill = "What is the structure of DNA and what bonds hold the double helix together?"

st.markdown("---")


# ─── Render Chat History ───────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Render expandable source citation drawer if assistant message has citations
        if msg.get("citations"):
            with st.expander("📚 View NIE Textbook Source Snippets"):
                for idx, c in enumerate(msg["citations"], 1):
                    st.markdown(
                        f"**Source {idx}:** {c.get('markdown_badge', '')}  \n"
                        f"*File:* `{c.get('source_file', '')}` | *Page:* `{c.get('page_number', '?')}` | *Section:* `{c.get('section_heading', '')}`"
                    )
                if msg.get("retrieved_chunks"):
                    st.markdown("---")
                    st.markdown("**Retrieved Context Text:**")
                    for chunk in msg["retrieved_chunks"]:
                        st.caption(f"📍 {chunk.get('citation', '')}")
                        st.markdown(f"> {chunk.get('text', '')}")


# ─── Handle User Input ─────────────────────────────────────────────────────────

prompt_input = st.chat_input("Ask a question about Unit 02 G.C.E. A/L Biology...")
user_query = selected_pill or prompt_input

if user_query:
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching NIE Resource Book & generating answer..."):
            answer_text = ""
            citations = []
            retrieved_chunks = []

            # Execute RAG query based on selected Backend API Mode
            if "Direct Python" in api_mode:
                if st.session_state.rag_pipeline:
                    res = st.session_state.rag_pipeline.answer_question(
                        query=user_query,
                        top_k=top_k_val,
                        doc_type_filter=selected_doc_filter,
                        include_citation_footer=True
                    )
                    answer_text = res["answer"]
                    citations = res.get("citations", [])
                    retrieved_chunks = res.get("retrieved_chunks", [])
                else:
                    answer_text = "⚠️ Error: RAG Pipeline is not initialized."
            else:
                # FastAPI REST API mode
                try:
                    resp = requests.post(
                        "http://127.0.0.1:8000/api/v1/query",
                        json={
                            "query": user_query,
                            "top_k": top_k_val,
                            "doc_type_filter": selected_doc_filter
                        },
                        timeout=30
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        answer_text = data["answer"]
                        citations = data.get("citations", [])
                    else:
                        answer_text = f"⚠️ API Error ({resp.status_code}): {resp.text}"
                except Exception as ex:
                    answer_text = f"⚠️ Could not connect to FastAPI backend at http://127.0.0.1:8000: {ex}"

            # Display generated answer
            st.markdown(answer_text)

            # Display citation drawer
            if citations:
                with st.expander("📚 View NIE Textbook Source Snippets"):
                    for idx, c in enumerate(citations, 1):
                        st.markdown(
                            f"**Source {idx}:** {c.get('markdown_badge', '')}  \n"
                            f"*File:* `{c.get('source_file', '')}` | *Page:* `{c.get('page_number', '?')}` | *Section:* `{c.get('section_heading', '')}`"
                        )
                    if retrieved_chunks:
                        st.markdown("---")
                        st.markdown("**Retrieved Context Text:**")
                        for chunk in retrieved_chunks:
                            st.caption(f"📍 {chunk.get('citation', '')}")
                            st.markdown(f"> {chunk.get('text', '')}")

            # Save assistant message to session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "citations": citations,
                "retrieved_chunks": retrieved_chunks
            })

