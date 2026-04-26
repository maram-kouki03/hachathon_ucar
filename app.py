

"""
HACK4UCAR — Main Application Entry Point
University of Carthage · Intelligent University Management Platform
"""
import streamlit as st
 
st.set_page_config(
    page_title="UCAR Intelligence Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&family=JetBrains+Mono:wght@400;500&display=swap');
 
*, *::before, *::after { box-sizing: border-box; }
 
html, body, [data-testid="stAppViewContainer"] {
    background: #050d1a !important;
    color: #e2e8f0;
}
 
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 20% 0%, rgba(30,58,95,0.4) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(15,35,60,0.3) 0%, transparent 50%),
                #050d1a !important;
}
 
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070f1e 0%, #0a1628 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.08) !important;
    min-width: 260px !important;
    max-width: 260px !important;
}
 
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
 
.main .block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1600px !important;
}
 
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,179,237,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,179,237,0.4); }
 
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
 
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1e3a5f 0%, #2a4a7f 100%) !important;
    border: 1px solid rgba(99,179,237,0.3) !important;
    color: #63b3ed !important;
}
 
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2a4a7f 0%, #1e3a5f 100%) !important;
    border-color: rgba(99,179,237,0.6) !important;
    box-shadow: 0 0 20px rgba(99,179,237,0.15) !important;
    transform: translateY(-1px) !important;
}
 
.stSelectbox > div > div {
    background: rgba(15,26,48,0.8) !important;
    border: 1px solid rgba(99,179,237,0.15) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
 
.stTextInput > div > div > input {
    background: rgba(15,26,48,0.8) !important;
    border: 1px solid rgba(99,179,237,0.15) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
 
.stTabs [data-baseweb="tab-list"] {
    background: rgba(10,22,40,0.6) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(99,179,237,0.08) !important;
}
 
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 7px !important;
    color: #8da9c4 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    padding: 8px 16px !important;
    transition: all 0.2s !important;
}
 
.stTabs [aria-selected="true"] {
    background: rgba(99,179,237,0.12) !important;
    color: #63b3ed !important;
}
 
.stMarkdown hr { border-color: rgba(99,179,237,0.1) !important; }
 
.stExpander {
    background: rgba(10,22,40,0.5) !important;
    border: 1px solid rgba(99,179,237,0.1) !important;
    border-radius: 10px !important;
}
 
.stSpinner > div { border-top-color: #63b3ed !important; }
 
div[data-testid="stMetric"] {
    background: rgba(15,26,48,0.6);
    border: 1px solid rgba(99,179,237,0.1);
    border-radius: 12px;
    padding: 16px;
}
 
.stAlert { border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important; }
 
.stDataFrame {
    border: 1px solid rgba(99,179,237,0.1) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
 
.js-plotly-plot .plotly .modebar { background: transparent !important; }
 
.stSlider > div > div > div > div { background: #63b3ed !important; }
 
/* Hide default streamlit sidebar nav buttons visually but keep them clickable */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    color: transparent !important;
    position: absolute !important;
    opacity: 0 !important;
    height: 44px !important;
    width: calc(100% - 24px) !important;
    margin-top: -44px !important;
    cursor: pointer !important;
    z-index: 10 !important;
}
</style>
""", unsafe_allow_html=True)
 
 
# ── Session state init ─────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "overview"
 
 
# ── Sidebar Navigation ─────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        # Logo / Brand
        st.markdown("""
        <div style="padding: 28px 20px 20px; border-bottom: 1px solid rgba(99,179,237,0.08);">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                <div style="
                    width:38px; height:38px;
                    background: linear-gradient(135deg, #1e3a5f, #2a5f8f);
                    border-radius:10px;
                    display:flex; align-items:center; justify-content:center;
                    font-size:1.1rem;
                    border: 1px solid rgba(99,179,237,0.2);
                ">🏛️</div>
                <div>
                    <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:800; color:#e2e8f0; letter-spacing:-0.3px;">UCAR</div>
                    <div style="font-family:'DM Sans',sans-serif; font-size:0.68rem; color:#4a7fa5; letter-spacing:1.5px; text-transform:uppercase;">Intelligence Platform</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
 
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
 
        nav_items = [
            ("🏢", "Executive Overview", "overview"),
            ("🏛️", "Institutions",       "institutions"),
            ("🔮", "Prédictions",         "predictions"),
            ("🚨", "Alertes & Monitoring","alerts"),
            ("🧠", "AI Insights",         "ai_insights"),
            ("💬", "Assistant IA",        "chatbot"),
            ("📋", "Rapports",            "reports"),
            ("📥", "Import de Données",   "upload"),
        ]
 
        st.markdown("""
        <div style="padding: 8px 12px; font-family:'Syne',sans-serif; font-size:0.65rem;
             color:#3a5f7a; text-transform:uppercase; letter-spacing:2px; font-weight:700;">
             Navigation
        </div>
        """, unsafe_allow_html=True)
 
        current = st.session_state.current_page
 
        for icon, label, key in nav_items:
            is_active = current == key
            active_style = (
                "background: rgba(99,179,237,0.1); border: 1px solid rgba(99,179,237,0.2); color:#63b3ed;"
                if is_active else
                "border: 1px solid transparent; color:#7a9ab5;"
            )
            icon_bg = "rgba(99,179,237,0.15)" if is_active else "rgba(255,255,255,0.03)"
 
            st.markdown(f"""
            <div style="padding: 0 12px; margin-bottom:2px;">
                <div style="
                    display:flex; align-items:center; gap:10px;
                    padding: 9px 12px; border-radius: 8px;
                    font-family:'DM Sans',sans-serif; font-size:0.87rem; font-weight:500;
                    {active_style}
                ">
                    <span style="
                        width:28px; height:28px; background:{icon_bg};
                        border-radius:6px; display:inline-flex;
                        align-items:center; justify-content:center; font-size:0.85rem;
                    ">{icon}</span>
                    {label}
                </div>
            </div>
            """, unsafe_allow_html=True)
 
            # Invisible button overlay for click detection
            if st.button(label, key=f"nav_btn_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()
 
        # System Status
        st.markdown("""
        <div style="margin: 16px 12px 0; border-top: 1px solid rgba(99,179,237,0.06); padding-top:16px;">
            <div style="padding: 0 4px 8px; font-family:'Syne',sans-serif; font-size:0.65rem;
                 color:#3a5f7a; text-transform:uppercase; letter-spacing:2px; font-weight:700;">
                 System Status
            </div>
        </div>
        """, unsafe_allow_html=True)
 
        col1, col2 = st.columns(2)
        col1.markdown("""
        <div style="background:rgba(104,211,145,0.08); border:1px solid rgba(104,211,145,0.15);
             border-radius:8px; padding:10px; text-align:center;">
            <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:800; color:#68d391;">31</div>
            <div style="font-family:'DM Sans',sans-serif; font-size:0.65rem; color:#4a7a5a;
                 text-transform:uppercase; letter-spacing:0.5px;">Institutions</div>
        </div>
        """, unsafe_allow_html=True)
        col2.markdown("""
        <div style="background:rgba(99,179,237,0.08); border:1px solid rgba(99,179,237,0.15);
             border-radius:8px; padding:10px; text-align:center;">
            <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:800; color:#63b3ed;">●</div>
            <div style="font-family:'DM Sans',sans-serif; font-size:0.65rem; color:#3a5f7a;
                 text-transform:uppercase; letter-spacing:0.5px;">Live</div>
        </div>
        """, unsafe_allow_html=True)
 
        st.markdown("""
        <div style="padding: 16px 12px 8px; margin-top:auto;">
            <div style="font-family:'DM Sans',sans-serif; font-size:0.72rem; color:#2a4a5a; text-align:center;">
                HACK4UCAR 2025 · v1.0.0<br>
                <span style="color:#3a5f7a;">Université de Carthage</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
 
 
render_sidebar()
 
# ── Page Router ───────────────────────────────────────────────────────────────
page = st.session_state.current_page
 
if page == "overview":
    from pages.Executive_Overview import render
    render()
elif page == "institutions":
    from pages.Institutions import render
    render()
elif page == "predictions":
    from pages.Predictions import render
    render()
elif page == "alerts":
    from pages.Alerts import render
    render()
elif page == "ai_insights":
    from pages.AI_Insights import render
    render()
elif page == "chatbot":
    from pages.Chatbot import render
    render()
elif page == "reports":
    from pages.Reports import render
    render()
elif page == "upload":
    from pages.Upload import render
    render()