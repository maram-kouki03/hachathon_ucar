

"""
pages/Chatbot.py — Mistral-powered conversational assistant for UCAR data.
"""
import streamlit as st
import json
from utils.ai_insights import answer_question_mistral
from utils.db import fetch_dataframe, get_all_institutions_summary, get_institutions
 
_CSS = """
<style>
.chatbot-hero {
    background: linear-gradient(135deg, rgba(8,18,14,0.97) 0%, rgba(12,28,22,0.95) 50%, rgba(8,18,14,0.97) 100%);
    border: 1px solid rgba(154,230,180,0.12);
    border-radius: 16px; padding: 24px 32px; margin-bottom: 20px;
}
 
.chat-window {
    background: rgba(5,12,10,0.85);
    border: 1px solid rgba(154,230,180,0.1);
    border-radius: 14px;
    padding: 20px 16px;
    min-height: 420px;
    max-height: 520px;
    overflow-y: auto;
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
 
.msg-user {
    align-self: flex-end;
    background: rgba(99,179,237,0.1);
    border: 1px solid rgba(99,179,237,0.18);
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    max-width: 78%;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: #bee3f8;
    line-height: 1.55;
}
 
.msg-ai {
    align-self: flex-start;
    background: rgba(154,230,180,0.06);
    border: 1px solid rgba(154,230,180,0.12);
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    max-width: 88%;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: #e2e8f0;
    line-height: 1.7;
    white-space: pre-wrap;
}
 
.msg-ai-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.6rem;
    font-weight: 700;
    color: #9ae6b4;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 6px;
}
 
.msg-user-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.6rem;
    font-weight: 700;
    color: #63b3ed;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 6px;
    text-align: right;
}
 
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    gap: 12px;
    color: #2a5a44;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
}
 
.sugg-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 14px;
}
 
.context-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(154,230,180,0.06);
    border: 1px solid rgba(154,230,180,0.12);
    border-radius: 20px;
    padding: 4px 12px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    color: #4a9a6a;
    margin-right: 6px; margin-bottom: 8px;
}
 
.data-badge {
    background: rgba(154,230,180,0.08);
    border: 1px solid rgba(154,230,180,0.15);
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #4a9a6a;
    margin-bottom: 14px;
}
</style>
"""
 
SUGGESTIONS = [
    "Quel est le taux de réussite moyen toutes institutions confondues ?",
    "Quelle institution a le taux d'abandon le plus élevé ?",
    "Compare l'exécution budgétaire entre les institutions disponibles.",
    "Résume les indicateurs ESG (empreinte carbone, énergie).",
    "Quelles institutions ont le plus de publications de recherche ?",
    "Donne-moi un rapport global sur les ressources humaines.",
]
 
 
def _build_db_context() -> str:
    """Build a compact text summary of real DB data to inject into the prompt."""
    try:
        summary = get_all_institutions_summary()
        if summary.empty:
            return "Aucune donnée disponible dans la base de données."
        ctx = "Résumé des données UCAR (par institution):\n"
        ctx += summary.to_string(index=False)
        return ctx[:3000]  # cap to avoid token overflow
    except Exception as ex:
        return f"Erreur lors de la récupération des données: {ex}"
 
 
def render():
    st.markdown(_CSS, unsafe_allow_html=True)
 
    # Hero
    st.markdown("""
    <div class="chatbot-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e2e8f0;">
                    💬 Assistant IA
                </div>
                <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#2a6a50; margin-top:4px;">
                    Interrogez vos données institutionnelles en langage naturel · Propulsé par Mistral AI
                </div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#9ae6b4;
                 background:rgba(154,230,180,0.06); border:1px solid rgba(154,230,180,0.12);
                 border-radius:8px; padding:8px 14px; text-align:center;">
                MISTRAL AI<br><span style="color:#9ae6b4;">● CONNECTÉ</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    # Data context info
    try:
        insts = get_institutions()
        df_check = fetch_dataframe()
        n_rows = len(df_check)
    except Exception:
        insts = []
        n_rows = 0
 
    if n_rows > 0:
        st.markdown(
            f'<div class="data-badge">'
            f'📊 Base active · {n_rows} enregistrement(s) · {len(insts)} institution(s): '
            f'{", ".join(insts[:6])}{"..." if len(insts) > 6 else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("⚠ Aucune donnée dans la base. Importez des documents via **Import de Données** pour activer l'assistant.")
 
    # Session state
    if "chatbot_history" not in st.session_state:
        st.session_state.chatbot_history = []
 
    # Suggestions (only when empty)
    if not st.session_state.chatbot_history:
        st.markdown("**💡 Questions suggérées :**")
        cols = st.columns(2)
        for idx, sugg in enumerate(SUGGESTIONS):
            if cols[idx % 2].button(sugg, key=f"sugg_{idx}", use_container_width=True):
                _send_message(sugg)
                st.rerun()
 
    # Chat window
    st.markdown('<div class="chat-window">', unsafe_allow_html=True)
    if not st.session_state.chatbot_history:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2.5rem;">💬</div>
            <div style="color:#3a7a5a; font-size:0.95rem;">Bonjour ! Je suis votre assistant UCAR.</div>
            <div style="color:#2a5a3a; font-size:0.82rem;">Posez-moi une question sur les données de vos institutions.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.chatbot_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="msg-user">'
                    f'<div class="msg-user-label">Vous</div>'
                    f'{msg["content"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="msg-ai">'
                    f'<div class="msg-ai-label">🤖 Assistant UCAR · Mistral AI</div>'
                    f'{msg["content"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    st.markdown('</div>', unsafe_allow_html=True)
 
    # Input row
    col_input, col_send, col_clear = st.columns([5, 1, 1])
    user_input = col_input.text_input(
        "Message",
        placeholder="Ex: Quel est le taux de réussite moyen ? Quelle institution a le plus de publications ?",
        key="chatbot_input",
        label_visibility="collapsed",
    )
    send  = col_send.button("📤 Envoyer", use_container_width=True, type="primary", key="chatbot_send")
    clear = col_clear.button("🗑️ Effacer", use_container_width=True, key="chatbot_clear")
 
    if clear:
        st.session_state.chatbot_history = []
        st.rerun()
 
    if send and user_input.strip():
        _send_message(user_input.strip())
        st.rerun()
 
    # Sidebar controls
    with st.sidebar:
        st.markdown("---")
        st.markdown("""
        <div style="padding: 0 4px 8px; font-family:'Syne',sans-serif; font-size:0.65rem;
             color:#3a5f7a; text-transform:uppercase; letter-spacing:2px; font-weight:700;">
             Assistant
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ Nouvelle conversation", use_container_width=True, key="chatbot_clear_sidebar"):
            st.session_state.chatbot_history = []
            st.rerun()
 
    # Export conversation
    if st.session_state.chatbot_history:
        st.markdown("---")
        col_exp, _ = st.columns([1, 3])
        conv_text = "\n\n".join(
            f"{'Vous' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in st.session_state.chatbot_history
        )
        col_exp.download_button(
            "📥 Exporter la conversation",
            data=conv_text.encode("utf-8"),
            file_name=f"conversation_ucar_{len(st.session_state.chatbot_history)}.txt",
            mime="text/plain",
            use_container_width=True,
        )
 
 
def _send_message(text: str):
    """Add user message, call Mistral, append response."""
    st.session_state.chatbot_history.append({"role": "user", "content": text})
    db_context = _build_db_context()
    with st.spinner("L'assistant analyse vos données..."):
        response = answer_question_mistral(
            question=text,
            history=st.session_state.chatbot_history[:-1],
            db_context=db_context,
        )
    st.session_state.chatbot_history.append({"role": "assistant", "content": response})