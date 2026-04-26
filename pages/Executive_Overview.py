"""
pages/Executive_Overview.py — Premium cockpit using real Supabase data.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
 
from utils.db import get_global_kpis, get_all_institutions_summary
from utils.alerts import get_critical_alerts
from utils.ai_insights import generate_executive_insight
 
 
def _card_css():
    return """
<style>
.kpi-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 24px; }
.kpi-card {
    background: linear-gradient(145deg, rgba(15,26,48,0.9), rgba(10,18,35,0.95));
    border: 1px solid rgba(99,179,237,0.12); border-radius: 14px;
    padding: 18px 16px; position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}
.kpi-card::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(circle at 50% 0%, rgba(99,179,237,0.05) 0%, transparent 70%);
    pointer-events: none;
}
.kpi-card:hover { border-color: rgba(99,179,237,0.25); transform: translateY(-2px); }
.kpi-icon { font-size:1.3rem; margin-bottom:10px; display:block; }
.kpi-value { font-family:'Syne',sans-serif; font-size:1.7rem; font-weight:800; color:#e2e8f0; line-height:1; margin-bottom:4px; }
.kpi-label { font-family:'DM Sans',sans-serif; font-size:0.7rem; color:#4a7a9a; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }
.kpi-bar { height:2px; background: rgba(99,179,237,0.1); border-radius:2px; margin-top:10px; }
.kpi-bar-fill { height:100%; background: linear-gradient(90deg, #63b3ed, #9ae6b4); border-radius:2px; }
 
.section-label {
    font-family:'Syne',sans-serif; font-size:0.72rem; font-weight:700;
    color:#3a5f7a; text-transform:uppercase; letter-spacing:2px;
    margin-bottom:12px; display:flex; align-items:center; gap:8px;
}
.section-label::after {
    content:''; flex:1; height:1px;
    background: linear-gradient(90deg, rgba(99,179,237,0.15), transparent);
}
 
.page-hero {
    background: linear-gradient(135deg, rgba(15,25,48,0.95) 0%, rgba(20,35,65,0.9) 50%, rgba(15,25,48,0.95) 100%);
    border: 1px solid rgba(99,179,237,0.1); border-radius: 16px;
    padding: 28px 32px; margin-bottom: 24px; position: relative; overflow: hidden;
}
.page-hero::before {
    content:''; position:absolute; top:-60px; right:-60px;
    width:300px; height:300px;
    background: radial-gradient(circle, rgba(99,179,237,0.06) 0%, transparent 70%); pointer-events:none;
}
.hero-title { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e2e8f0; letter-spacing:-0.5px; margin-bottom:4px; }
.hero-subtitle { font-family:'DM Sans',sans-serif; font-size:0.88rem; color:#4a7a9a; font-weight:300; }
.hero-badge { display:inline-flex; align-items:center; gap:6px; background: rgba(104,211,145,0.1); border: 1px solid rgba(104,211,145,0.2); border-radius:20px; padding:4px 12px; font-family:'DM Sans',sans-serif; font-size:0.75rem; color:#68d391; margin-top:12px; }
.live-dot { width:6px; height:6px; border-radius:50%; background:#68d391; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
 
.ai-banner {
    background: linear-gradient(90deg, rgba(99,179,237,0.08) 0%, rgba(154,230,180,0.05) 100%);
    border: 1px solid rgba(99,179,237,0.15); border-left: 3px solid #63b3ed;
    border-radius: 0 12px 12px 0; padding: 14px 20px; margin-bottom: 24px;
    display:flex; align-items:center; gap:14px;
}
.ai-banner-icon { width:36px; height:36px; flex-shrink:0; background: rgba(99,179,237,0.12); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1.1rem; }
.ai-banner-label { font-family:'Syne',sans-serif; font-size:0.65rem; font-weight:700; color:#63b3ed; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:2px; }
.ai-banner-text { font-family:'DM Sans',sans-serif; font-size:0.88rem; color:#cbd5e0; line-height:1.4; }
 
.alert-feed-item { display:flex; align-items:flex-start; gap:12px; padding: 12px 14px; border-radius: 10px; margin-bottom: 8px; }
.alert-feed-item.critical { background: rgba(252,129,129,0.06); border: 1px solid rgba(252,129,129,0.12); border-left: 3px solid #fc8181; }
.alert-feed-item.warning  { background: rgba(246,173,85,0.06);  border: 1px solid rgba(246,173,85,0.12);  border-left: 3px solid #f6ad55; }
.alert-feed-item.info     { background: rgba(99,179,237,0.06);  border: 1px solid rgba(99,179,237,0.12);  border-left: 3px solid #63b3ed; }
.alert-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:5px; }
.alert-dot.critical { background:#fc8181; box-shadow: 0 0 6px rgba(252,129,129,0.5); }
.alert-dot.warning  { background:#f6ad55; }
.alert-dot.info     { background:#63b3ed; }
.alert-msg  { font-family:'DM Sans',sans-serif; font-size:0.83rem; color:#e2e8f0; line-height:1.4; }
.alert-meta-text { font-family:'DM Sans',sans-serif; font-size:0.73rem; color:#4a7a9a; margin-top:2px; }
 
.no-data-box {
    background: rgba(10,22,40,0.5); border: 1px dashed rgba(99,179,237,0.2);
    border-radius: 12px; padding: 32px; text-align: center;
    font-family: 'DM Sans', sans-serif; color: #4a7a9a; font-size: 0.9rem;
}
</style>
"""
 
 
def render():
    st.markdown(_card_css(), unsafe_allow_html=True)
 
    now_str = datetime.now().strftime("%A, %d %B %Y · %H:%M")
 
    # ── Hero ──────────────────────────────────────────────────────────────────
    kpis    = get_global_kpis()
    insts_n = kpis.get("active_institutions", {}).get("value", "—")
 
    st.markdown(f"""
    <div class="page-hero">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:12px;">
            <div>
                <div class="hero-title">Executive Overview</div>
                <div class="hero-subtitle">Consolidated Multi-Institution Cockpit · Université de Carthage</div>
                <div class="hero-badge"><div class="live-dot"></div>Live · {now_str}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#3a5f7a; margin-bottom:4px;">INSTITUTIONS ACTIVES</div>
                <div style="font-family:'Syne',sans-serif; font-size:2.5rem; font-weight:800; color:#63b3ed; line-height:1;">{insts_n}</div>
                <div style="font-family:'DM Sans',sans-serif; font-size:0.75rem; color:#2a4a6a;">dans la base de données</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    if not kpis:
        st.markdown("""
        <div class="no-data-box">
            📭 Aucune donnée disponible.<br>
            Importez des documents via <strong>Import de Données</strong> pour alimenter le dashboard.
        </div>
        """, unsafe_allow_html=True)
        return
 
    # ── AI Banner ─────────────────────────────────────────────────────────────
    with st.spinner("Génération du insight IA..."):
        insight = generate_executive_insight(context={k: v.get("value") for k, v in kpis.items()})
 
    st.markdown(f"""
    <div class="ai-banner">
        <div class="ai-banner-icon">🤖</div>
        <div>
            <div class="ai-banner-label">AI Executive Insight</div>
            <div class="ai-banner-text">{insight}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    # ── Global KPIs ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📊 Indicateurs Clés Globaux</div>', unsafe_allow_html=True)
 
    kpi_items = [
        ("🎓", "Taux Réussite",   kpis.get("success_rate",        {"value":"N/A","positive":True, "bar":0})),
        ("💰", "Budget Exec.",    kpis.get("budget_execution",     {"value":"N/A","positive":True, "bar":0})),
        ("🏛️", "Institutions",   kpis.get("active_institutions",  {"value":"N/A","positive":True, "bar":100})),
        ("👥", "Étudiants",      kpis.get("total_students",        {"value":"N/A","positive":True, "bar":70})),
        ("🔬", "Publications",   kpis.get("research_projects",     {"value":"N/A","positive":True, "bar":65})),
        ("🌱", "CO₂ Émis",       kpis.get("carbon_footprint",      {"value":"N/A","positive":True, "bar":40})),
    ]
 
    cols = st.columns(6)
    for col, (icon, label, data) in zip(cols, kpi_items):
        bar_w = data.get("bar", 0)
        col.markdown(f"""
        <div class="kpi-card">
            <span class="kpi-icon">{icon}</span>
            <div class="kpi-value">{data['value']}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{bar_w}%"></div></div>
        </div>
        """, unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # ── Summary table + Alerts ────────────────────────────────────────────────
    df_summary = get_all_institutions_summary()
    col_tbl, col_right = st.columns([1.6, 1], gap="medium")
 
    with col_tbl:
        st.markdown('<div class="section-label">🏛️ Tableau Comparatif</div>', unsafe_allow_html=True)
        if df_summary.empty:
            st.info("Importez des données pour voir le comparatif.")
        else:
            # Bubble chart
            num_cols = [c for c in ["Réussite %", "Budget Exec %", "Étudiants", "Score Global"] if c in df_summary.columns]
            if len(num_cols) >= 2:
                x_col = "Budget Exec %" if "Budget Exec %" in df_summary.columns else num_cols[0]
                y_col = "Réussite %" if "Réussite %" in df_summary.columns else num_cols[1]
                size_col = "Étudiants" if "Étudiants" in df_summary.columns else None
                color_col = "Score Global" if "Score Global" in df_summary.columns else y_col
 
                fig = px.scatter(
                    df_summary,
                    x=x_col, y=y_col,
                    size=size_col if size_col else None,
                    color=color_col,
                    text="Institution",
                    color_continuous_scale=["#fc8181", "#f6ad55", "#9ae6b4"],
                    size_max=40,
                )
                fig.update_traces(textfont=dict(color="#e2e8f0", size=10))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#7a5aaa", family="DM Sans"),
                    height=300, margin=dict(t=10, b=10),
                    xaxis=dict(gridcolor="rgba(183,148,244,0.05)", title=x_col),
                    yaxis=dict(gridcolor="rgba(183,148,244,0.05)", title=y_col),
                    coloraxis_colorbar=dict(tickfont=dict(color="#7a5aaa")),
                )
                st.plotly_chart(fig, use_container_width=True)
 
            st.dataframe(df_summary, use_container_width=True, hide_index=True, height=260)
 
    with col_right:
        # Alerts
        st.markdown('<div class="section-label">🚨 Alertes Critiques</div>', unsafe_allow_html=True)
        alerts = get_critical_alerts(limit=6)
        if not alerts:
            st.markdown('<div class="no-data-box">✅ Aucune alerte active.<br>Toutes les métriques sont dans les seuils.</div>', unsafe_allow_html=True)
        else:
            for alert in alerts:
                level = alert.get("level", "info")
                msg   = alert.get("message", "")
                inst  = alert.get("institution", "UCAR")
                domain = alert.get("domain", "")
                ts    = alert.get("timestamp", "")
                st.markdown(f"""
                <div class="alert-feed-item {level}">
                    <div class="alert-dot {level}"></div>
                    <div>
                        <div class="alert-msg">{msg}</div>
                        <div class="alert-meta-text">🏛️ {inst} · {domain} · {ts}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
 
        # Radar
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">📡 Performance Globale</div>', unsafe_allow_html=True)
 
        # Build radar from real data
        categories = ["Réussite", "Budget Exec", "Absentéisme inv.", "Publications", "Abandon inv.", "CO₂ inv."]
        values = []
        if not df_summary.empty:
            def _mean(col):
                return float(df_summary[col].mean()) if col in df_summary.columns else 50
 
            success  = _mean("Réussite %")
            budget   = _mean("Budget Exec %")
            absent   = max(0, 100 - _mean("Absentéisme %")) if "Absentéisme %" in df_summary.columns else 70
            pubs     = min(100, _mean("Publications") * 3) if "Publications" in df_summary.columns else 50
            dropout  = max(0, 100 - _mean("Abandon %") * 5) if "Abandon %" in df_summary.columns else 70
            co2      = max(0, 100 - _mean("CO₂ (T)") / 5) if "CO₂ (T)" in df_summary.columns else 60
            values   = [success, budget, absent, pubs, dropout, co2]
        else:
            values = [50, 50, 50, 50, 50, 50]
 
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]],
            fill="toself", name="Actuel",
            fillcolor="rgba(99,179,237,0.12)",
            line=dict(color="#63b3ed", width=2),
        ))
        fig_r.add_trace(go.Scatterpolar(
            r=[80] * len(categories) + [80], theta=categories + [categories[0]],
            fill="toself", name="Objectif",
            fillcolor="rgba(104,211,145,0.05)",
            line=dict(color="#68d391", width=1.5, dash="dash"),
        ))
        fig_r.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100],
                    tickfont=dict(color="#3a5f7a", size=8),
                    gridcolor="rgba(255,255,255,0.04)"),
                angularaxis=dict(tickfont=dict(color="#7a9ab5", size=9),
                    gridcolor="rgba(255,255,255,0.04)"),
            ),
            showlegend=True,
            legend=dict(font=dict(color="#5a8aaa", size=9), bgcolor="rgba(0,0,0,0)", x=0.8, y=0),
            paper_bgcolor="rgba(0,0,0,0)",
            height=260, margin=dict(t=10, b=10, l=20, r=20),
        )
        st.plotly_chart(fig_r, use_container_width=True)