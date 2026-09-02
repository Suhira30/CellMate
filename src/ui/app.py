"""
Streamlit Web Application for CellMate RAG Assistant.
Design System: "Cytosol OS — CellMate Living Interface"
An animated, bioluminescent cellular environment for G.C.E. A/L Biology Unit 02.

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


# ─── Page Configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CellMate — Living Cellular Biology AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ─── Cytosol OS Design System & Keyframe Animations ───────────────────────────

st.markdown("""
<style>
/* ── Deep Cytoplasm Base & Atmosphere ────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: radial-gradient(circle at 50% 20%, #0B1021 0%, #060913 80%, #03050B 100%) !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
/* ── Hide Streamlit Default Header, Toolbar, Fork/GitHub Links & Profile Avatar ── */
#MainMenu, header, [data-testid="stHeader"], [data-testid="stToolbar"], .stAppToolbar {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}
footer, [data-testid="stProfileAvatar"], div[class*="viewerBadge"], div[class*="stProfile"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* ── Phospholipid Membrane Sidebar ───────────────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.75) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(6, 182, 212, 0.2) !important;
    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5);
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}

/* ── Floating Background Organelles (Cytoplasmic Drift) ──────────── */
@keyframes cytoplasmicDrift {
    0%   { transform: translateY(0px) rotate(0deg); opacity: 0.15; }
    50%  { transform: translateY(-18px) rotate(180deg); opacity: 0.30; }
    100% { transform: translateY(0px) rotate(360deg); opacity: 0.15; }
}
.floating-organelle {
    position: fixed;
    pointer-events: none;
    z-index: 0;
    animation: cytoplasmicDrift 16s ease-in-out infinite;
}

/* ── Static Clean Header Icon ───────────────────────────────────── */
.clean-header-icon {
    display: inline-block;
    font-size: 2.4rem;
    vertical-align: middle;
}

/* ── Bioluminescent Gradient Header ──────────────────────────────── */
@keyframes bioluminescentShift {
    0%   { background-position: 0% 50%; filter: drop-shadow(0 0 15px rgba(6,182,212,0.3)); }
    50%  { background-position: 100% 50%; filter: drop-shadow(0 0 25px rgba(139,92,246,0.4)); }
    100% { background-position: 0% 50%; filter: drop-shadow(0 0 15px rgba(6,182,212,0.3)); }
}
.cellmate-title {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #06B6D4, #3B82F6, #8B5CF6, #F59E0B, #22D3EE);
    background-size: 300% 300%;
    animation: bioluminescentShift 6s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.1rem;
}
.cellmate-subtitle {
    font-size: 0.95rem;
    color: #64748B;
    margin-bottom: 1.2rem;
}
.badge-unit {
    display: inline-block;
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(139, 92, 246, 0.2));
    color: #38BDF8;
    padding: 0.25rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid rgba(56, 189, 248, 0.3);
    box-shadow: 0 0 12px rgba(6, 182, 212, 0.15);
    margin-right: 0.5rem;
}

/* ── Molecule Bubbles (Quick Prompt Pills Physics) ────────────────── */
@keyframes bobPhase1 { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-6px); } }
@keyframes bobPhase2 { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-8px); } }
@keyframes bobPhase3 { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-5px); } }
@keyframes bobPhase4 { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-7px); } }

[data-testid="column"]:nth-child(1) [data-testid="stButton"] { animation: bobPhase1 4s ease-in-out infinite; }
[data-testid="column"]:nth-child(2) [data-testid="stButton"] { animation: bobPhase2 4.5s ease-in-out infinite 0.5s; }
[data-testid="column"]:nth-child(3) [data-testid="stButton"] { animation: bobPhase3 3.8s ease-in-out infinite 1.0s; }
[data-testid="column"]:nth-child(4) [data-testid="stButton"] { animation: bobPhase4 4.2s ease-in-out infinite 0.3s; }

[data-testid="stButton"] button {
    background: rgba(15, 30, 51, 0.8) !important;
    color: #94A3B8 !important;
    border: 1px solid rgba(30, 58, 82, 0.8) !important;
    border-radius: 9999px !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}
[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(139, 92, 246, 0.25)) !important;
    color: #38BDF8 !important;
    border-color: #06B6D4 !important;
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.4) !important;
    transform: scale(1.06) translateY(-3px) !important;
}

/* ── Vesicle Transport Message Bubbles ────────────────────────────── */
@keyframes vesicleFusionRight {
    0%   { opacity: 0; transform: scale(0.92) translateX(24px); }
    70%  { transform: scale(1.01) translateX(-2px); }
    100% { opacity: 1; transform: scale(1) translateX(0); }
}
@keyframes vesicleFusionLeft {
    0%   { opacity: 0; transform: scale(0.92) translateX(-24px); }
    70%  { transform: scale(1.01) translateX(2px); }
    100% { opacity: 1; transform: scale(1) translateX(0); }
}

/* User Message Bubble — Enzymatic Amber */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(45, 29, 8, 0.9), rgba(28, 20, 8, 0.95)) !important;
    border: 1px solid rgba(245, 158, 11, 0.4) !important;
    border-left: 4px solid #F59E0B !important;
    border-radius: 18px !important;
    box-shadow: 0 0 22px rgba(245, 158, 11, 0.15) !important;
    backdrop-filter: blur(12px) !important;
    animation: vesicleFusionRight 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    margin-bottom: 1rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) li {
    color: #FDE68A !important;
    font-size: 1.02rem;
    line-height: 1.7;
}

/* Assistant Message Bubble — Bioluminescent Cyan */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: linear-gradient(135deg, rgba(6, 20, 33, 0.92), rgba(9, 29, 46, 0.95)) !important;
    border: 1px solid rgba(6, 182, 212, 0.35) !important;
    border-left: 4px solid #06B6D4 !important;
    border-radius: 18px !important;
    box-shadow: 0 0 22px rgba(6, 182, 212, 0.15) !important;
    backdrop-filter: blur(12px) !important;
    animation: vesicleFusionLeft 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    margin-bottom: 1rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) li {
    color: #CFFAFE !important;
    font-size: 1.02rem;
    line-height: 1.7;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) strong {
    color: #67E8F9 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) code {
    background: #0C2E3F !important;
    color: #A5F3FC !important;
    border-radius: 4px;
    padding: 2px 6px;
}

/* ── Enzyme Active Site Chat Input ────────────────────────────────── */
[data-testid="stChatInput"] textarea {
    background: rgba(15, 22, 38, 0.9) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(6, 182, 212, 0.3) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #06B6D4 !important;
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.35) !important;
}

/* ── Nucleus Transcription & Ribosome Translation Thinking State ─── */
@keyframes transcriptionSpin {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
@keyframes pulseBioluminescence {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.96); }
}
.transcription-indicator {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 0.6rem 1.2rem;
    background: linear-gradient(135deg, rgba(13, 27, 42, 0.9), rgba(9, 29, 46, 0.95));
    border: 1px solid rgba(6, 182, 212, 0.4);
    border-radius: 9999px;
    font-size: 0.88rem;
    color: #38BDF8;
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
    animation: pulseBioluminescence 2s ease-in-out infinite;
}
.ribosome-spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(6, 182, 212, 0.3);
    border-top: 2px solid #06B6D4;
    border-radius: 50%;
    animation: transcriptionSpin 1s linear infinite;
}

/* ── Vesicle Citation Drawer ──────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(13, 27, 42, 0.8) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(10px) !important;
}
[data-testid="stExpander"] summary {
    color: #A78BFA !important;
    font-weight: 600;
}

/* ── RNA Strand Slider & Controls ─────────────────────────────────── */
[data-testid="stSlider"] > div > div > div {
    background: linear-gradient(90deg, #06B6D4, #8B5CF6) !important;
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.5) !important;
}
.stSelectbox select, .stSelectbox [data-baseweb="select"] {
    background: rgba(15, 30, 51, 0.8) !important;
    color: #CBD5E1 !important;
    border-color: rgba(30, 58, 82, 0.8) !important;
}

hr {
    border-color: rgba(30, 45, 69, 0.6) !important;
    margin: 1rem 0 !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #060913; }
::-webkit-scrollbar-thumb { background: #1E3A52; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #06B6D4; }
</style>
""", unsafe_allow_html=True)


# ─── Floating Background Organelles ───────────────────────────────────────────

st.markdown("""
<div class="floating-organelle" style="top: 15%; left: 5%;">
    <svg width="40" height="40" viewBox="0 0 100 100" fill="none" opacity="0.25">
        <ellipse cx="50" cy="50" rx="40" ry="20" stroke="#06B6D4" stroke-width="3" />
        <path d="M 20 50 Q 35 30 50 50 T 80 50" stroke="#06B6D4" stroke-width="2" />
    </svg>
</div>
<div class="floating-organelle" style="top: 65%; right: 4%; animation-delay: -5s;">
    <svg width="45" height="45" viewBox="0 0 100 100" fill="none" opacity="0.2">
        <circle cx="50" cy="50" r="35" stroke="#8B5CF6" stroke-width="3" stroke-dasharray="8 4" />
        <circle cx="50" cy="50" r="12" fill="#8B5CF6" opacity="0.4" />
    </svg>
</div>
""", unsafe_allow_html=True)


# ─── Session State Initialization ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to Cytosol OS — I am CellMate**, your AI Study Assistant for "
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


# ─── Sidebar — "Cell Membrane" Control Panel ───────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1.2rem 0 0.5rem 0;'>
        <div style='font-size:2.2rem;'>🧬</div>
        <div style='font-size:1.3rem; font-weight:800; background:linear-gradient(135deg,#06B6D4,#8B5CF6);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:1px;'>
            CellMate
        </div>
        <div style='font-size:0.75rem; color:#64748B; margin-top:2px;'>Cytosol OS · Unit 02</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    st.markdown("<p style='color:#38BDF8; font-size:0.78rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;'>⚡ RETRIEVAL MEMBRANE</p>", unsafe_allow_html=True)

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

    # Knowledge Base Stats Indicator
    if st.session_state.rag_pipeline and st.session_state.rag_pipeline.retriever:
        try:
            stats = st.session_state.rag_pipeline.retriever.store_manager.get_stats()
            total = stats.get("total_chunks", 0)
            st.markdown(f"""
            <div style='background:rgba(6, 20, 33, 0.85); border:1px solid rgba(6, 182, 212, 0.4); border-radius:12px;
                        padding:0.8rem 1rem; margin-bottom:0.8rem; box-shadow:0 0 15px rgba(6, 182, 212, 0.15);'>
                <div style='font-size:0.72rem; color:#64748B; letter-spacing:1px; margin-bottom:2px;'>NUCLEUS DATABASE</div>
                <div style='font-size:1.2rem; font-weight:800; color:#06B6D4;'>{total} Chunks Indexed</div>
                <div style='font-size:0.72rem; color:#334155; margin-top:2px;'>NIE Unit 02 Resource Book ✓</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            pass

    if st.button("🗑️ Clear Cytoplasm History", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()


# ─── Main Title & Living Header ────────────────────────────────────────────────

st.markdown("""
<div style="display:flex; align-items:center; gap:12px;">
    <div style="font-size:2.2rem;">🧬</div>
    <div>
        <div class="cellmate-title">CellMate</div>
        <div class="cellmate-subtitle">
            <span class="badge-unit">Unit 02</span>
            Chemical &amp; Cellular Basis of Life &nbsp;·&nbsp; Grounded in NIE Sri Lanka G.C.E. A/L Resource Book
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Molecule Bubbles (Quick Prompt Pills) ─────────────────────────────────────

st.markdown("<p style='color:#64748B; font-size:0.82rem; font-weight:600; letter-spacing:1px; margin-bottom:0.5rem;'>✦ MOLECULE BUBBLES — QUICK PRACTICE QUESTIONS</p>", unsafe_allow_html=True)
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


# ─── Chat History (Vesicle Transport Entrance) ─────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander("📚 View NIE Textbook Vesicle Passages"):
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


# ─── Input & Response Processing ───────────────────────────────────────────────

prompt_input = st.chat_input("Ask a question about Unit 02 G.C.E. A/L Biology…")
user_query = selected_pill or prompt_input

if user_query:
    # 1. User Vesicle Fusion
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Assistant Response Synthesis
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("""
        <div class="transcription-indicator">
            <span class="ribosome-spinner"></span>
            &nbsp; Nucleus Transcription: Searching NIE Resource Book…
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
                        "⌛ **Daily API Quota Limit Reached (Anabiosis Spore Mode)**\n\n"
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
            with st.expander("📚 View NIE Textbook Vesicle Passages"):
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
