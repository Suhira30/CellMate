"""
Streamlit Web Application for CellMate RAG Assistant.
Empathy Experiment-inspired dark theme with two-color conversation bubbles.

Usage:
    streamlit run src/ui/app.py
"""
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from src.config import TOP_K, LLM_MODEL, EMBEDDING_MODEL
from src.rag.pipeline import CellMateRAG


# ─── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CellMate — A/L Biology AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS — Empathy Experiment Dark Theme ────────────────────────────────

st.markdown("""
<style>
/* ── Base & Background ───────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0A0E1A !important;
    color: #E2E8F0 !important;
}
[data-testid="stHeader"] {
    background-color: #0A0E1A !important;
    border-bottom: 1px solid #1E2D45;
}
[data-testid="stSidebar"] {
    background-color: #0F1626 !important;
    border-right: 1px solid #1E2D45;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}

/* ── Animated gradient header title ─────────────────────────────── */
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.cellmate-title {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #06B6D4, #3B82F6, #8B5CF6, #F59E0B);
    background-size: 300% 300%;
    animation: gradientShift 5s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.1rem;
}
.cellmate-subtitle {
    font-size: 0.95rem;
    color: #64748B;
    margin-bottom: 1.2rem;
    letter-spacing: 0.2px;
}
.badge-unit {
    display: inline-block;
    background: linear-gradient(135deg, #0F2A45, #0F3460);
    color: #38BDF8;
    padding: 0.2rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid #1E4976;
    margin-right: 0.5rem;
}

/* ── USER message bubble — warm amber/coral ──────────────────────── */
@keyframes fadeSlideRight {
    from { opacity: 0; transform: translateX(18px); }
    to   { opacity: 1; transform: translateX(0); }
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, #1C1408, #2D1D08) !important;
    border: 1px solid #78350F !important;
    border-left: 4px solid #F59E0B !important;
    border-radius: 16px !important;
    box-shadow: 0 0 18px rgba(245,158,11,0.12) !important;
    animation: fadeSlideRight 0.35s ease-out;
    margin-bottom: 1rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) li {
    color: #FDE68A !important;
    font-size: 1.0rem;
    line-height: 1.7;
}

/* ── ASSISTANT message bubble — cool teal/cyan ───────────────────── */
@keyframes fadeSlideLeft {
    from { opacity: 0; transform: translateX(-18px); }
    to   { opacity: 1; transform: translateX(0); }
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: linear-gradient(135deg, #061421, #091D2E) !important;
    border: 1px solid #164E63 !important;
    border-left: 4px solid #06B6D4 !important;
    border-radius: 16px !important;
    box-shadow: 0 0 18px rgba(6,182,212,0.10) !important;
    animation: fadeSlideLeft 0.35s ease-out;
    margin-bottom: 1rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) li {
    color: #CFFAFE !important;
    font-size: 1.0rem;
    line-height: 1.7;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) strong {
    color: #67E8F9 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) code {
    background: #0C2E3F !important;
    color: #A5F3FC !important;
    border-radius: 4px;
    padding: 0 4px;
}

/* ── Citation drawer ─────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #0D1B2A !important;
    border: 1px solid #1E3A52 !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
    color: #38BDF8 !important;
    font-weight: 600;
}

/* ── Quick pill buttons ──────────────────────────────────────────── */
[data-testid="stButton"] button {
    background: #0F1E33 !important;
    color: #94A3B8 !important;
    border: 1px solid #1E3A52 !important;
    border-radius: 9999px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    transition: all 0.25s ease !important;
}
[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #0F2A45, #0F3460) !important;
    color: #38BDF8 !important;
    border-color: #0EA5E9 !important;
    box-shadow: 0 0 12px rgba(6,182,212,0.25) !important;
    transform: translateY(-2px) !important;
}

/* ── Chat input ──────────────────────────────────────────────────── */
[data-testid="stChatInput"] textarea {
    background: #0F1626 !important;
    color: #E2E8F0 !important;
    border: 1px solid #1E3A52 !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #06B6D4 !important;
    box-shadow: 0 0 10px rgba(6,182,212,0.2) !important;
}

/* ── Sidebar sliders & selects ───────────────────────────────────── */
[data-testid="stSlider"] > div > div > div {
    background: #06B6D4 !important;
}
.stSelectbox select, .stSelectbox [data-baseweb="select"] {
    background: #0F1E33 !important;
    color: #CBD5E1 !important;
    border-color: #1E3A52 !important;
}

/* ── Divider ─────────────────────────────────────────────────────── */
hr {
    border-color: #1E2D45 !important;
    margin: 1rem 0 !important;
}

/* ── Spinner / status ────────────────────────────────────────────── */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}
.thinking-indicator {
    display: inline-flex;
    gap: 5px;
    align-items: center;
    padding: 0.5rem 1rem;
    background: #0D1B2A;
    border: 1px solid #164E63;
    border-radius: 9999px;
    font-size: 0.85rem;
    color: #38BDF8;
}
.thinking-indicator span {
    animation: pulse 1.2s ease-in-out infinite;
}
.thinking-indicator span:nth-child(2) { animation-delay: 0.2s; }
.thinking-indicator span:nth-child(3) { animation-delay: 0.4s; }

/* ── Source snippet card ─────────────────────────────────────────── */
.source-card {
    background: #071524;
    border-left: 3px solid #0EA5E9;
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
    color: #94A3B8;
}

/* ── Scrollbar styling ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0A0E1A; }
::-webkit-scrollbar-thumb { background: #1E3A52; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #06B6D4; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Hello! I am CellMate**, your AI Study Assistant for "
                "**Sri Lanka G.C.E. Advanced Level Biology (Unit 02: Chemical and Cellular Basis of Life)**.\n\n"
                "Ask me anything about water properties, biological molecules, enzymes, cell membranes, "
                "or cellular energy. Every answer is strictly grounded in official NIE Resource Book materials with page citations!"
            ),
            "citations": [],
            "retrieved_chunks": []
        }
    ]

if "rag_pipeline" not in st.session_state:
    try:
        st.session_state.rag_pipeline = CellMateRAG()
    except Exception:
        st.session_state.rag_pipeline = None


# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
        <div style='font-size:2.5rem;'>🧬</div>
        <div style='font-size:1.2rem; font-weight:700; color:#38BDF8; letter-spacing:1px;'>CellMate</div>
        <div style='font-size:0.72rem; color:#475569; margin-top:2px;'>A/L Biology AI Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    st.markdown("<p style='color:#64748B; font-size:0.78rem; font-weight:600; letter-spacing:1px; text-transform:uppercase;'>Retrieval Settings</p>", unsafe_allow_html=True)

    top_k_val = st.slider(
        "Context Chunks (Top-K)",
        min_value=1,
        max_value=8,
        value=TOP_K,
        help="Number of NIE textbook passages retrieved per question."
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

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Chunk indicator
    if st.session_state.rag_pipeline and st.session_state.rag_pipeline.retriever:
        try:
            stats = st.session_state.rag_pipeline.retriever.store_manager.get_stats()
            total = stats.get("total_chunks", 0)
            st.markdown(f"""
            <div style='background:#0D1B2A; border:1px solid #164E63; border-radius:10px;
                        padding:0.7rem 1rem; margin-bottom:0.8rem;'>
                <div style='font-size:0.75rem; color:#475569; margin-bottom:2px;'>KNOWLEDGE BASE</div>
                <div style='font-size:1.1rem; font-weight:700; color:#06B6D4;'>{total} chunks</div>
                <div style='font-size:0.72rem; color:#334155;'>NIE Unit 02 indexed ✓</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            pass

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()


# ─── Main Header ───────────────────────────────────────────────────────────────

st.markdown("""
<div class="cellmate-title">🧬 CellMate</div>
<div class="cellmate-subtitle">
    <span class="badge-unit">Unit 02</span>
    Chemical &amp; Cellular Basis of Life &nbsp;·&nbsp; Grounded in NIE Sri Lanka G.C.E. A/L Resource Book
</div>
""", unsafe_allow_html=True)


# ─── Quick Prompt Pills ────────────────────────────────────────────────────────

st.markdown("<p style='color:#475569; font-size:0.82rem; font-weight:500; margin-bottom:0.4rem;'>✦ TRY A QUICK QUESTION</p>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

selected_pill = None
with col1:
    if st.button("💧 Water Properties", use_container_width=True):
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

st.markdown("<hr/>", unsafe_allow_html=True)


# ─── Chat History ──────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander("📚 View NIE Source Passages"):
                for idx, c in enumerate(msg["citations"], 1):
                    st.markdown(
                        f"**Source {idx}:** {c.get('markdown_badge', '')}  \n"
                        f"*File:* `{c.get('source_file', '')}` | "
                        f"*Page:* `{c.get('page_number', '?')}` | "
                        f"*Section:* `{c.get('section_heading', '')}`"
                    )
                if msg.get("retrieved_chunks"):
                    st.markdown("---")
                    for chunk in msg["retrieved_chunks"]:
                        st.caption(f"📍 {chunk.get('citation', '')}")
                        st.markdown(f"> {chunk.get('text', '')}")


# ─── Handle Input ──────────────────────────────────────────────────────────────

prompt_input = st.chat_input("Ask anything about Unit 02 G.C.E. A/L Biology…")
user_query = selected_pill or prompt_input

if user_query:
    # Display user bubble
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate & display assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("""
        <div class="thinking-indicator">
            <span>●</span><span>●</span><span>●</span>
            &nbsp; Searching NIE Resource Book…
        </div>
        """, unsafe_allow_html=True)

        answer_text = ""
        citations = []
        retrieved_chunks = []

        if st.session_state.rag_pipeline:
            try:
                res = st.session_state.rag_pipeline.answer_question(
                    query=user_query,
                    top_k=top_k_val,
                    doc_type_filter=selected_doc_filter,
                    include_citation_footer=True
                )
                answer_text = res["answer"]
                citations = res.get("citations", [])
                retrieved_chunks = res.get("retrieved_chunks", [])
            except Exception as ex:
                err_str = str(ex)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    answer_text = (
                        "⌛ **Daily API Quota Limit Reached**\n\n"
                        "The free-tier API quota for Google Gemini has been exhausted for today "
                        "(1,000 requests/day limit on Free Tier).\n\n"
                        "**What you can do:**\n"
                        "- 🕒 Please try again tomorrow when the daily API quota resets.\n"
                        "- 🔑 Or update your `GEMINI_API_KEY` in settings."
                    )
                else:
                    answer_text = f"⚠️ An error occurred: {ex}"
        else:
            answer_text = "⚠️ RAG Pipeline could not be initialized. Please check your API key in settings."

        placeholder.markdown(answer_text)

        if citations:
            with st.expander("📚 View NIE Source Passages"):
                for idx, c in enumerate(citations, 1):
                    st.markdown(
                        f"**Source {idx}:** {c.get('markdown_badge', '')}  \n"
                        f"*File:* `{c.get('source_file', '')}` | "
                        f"*Page:* `{c.get('page_number', '?')}` | "
                        f"*Section:* `{c.get('section_heading', '')}`"
                    )
                if retrieved_chunks:
                    st.markdown("---")
                    for chunk in retrieved_chunks:
                        st.caption(f"📍 {chunk.get('citation', '')}")
                        st.markdown(f"> {chunk.get('text', '')}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "citations": citations,
        "retrieved_chunks": retrieved_chunks
    })
