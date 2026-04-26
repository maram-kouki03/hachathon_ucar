"""
pages/AI_Insights.py — AI analytics using real DB data.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
 
from utils.ai_insights import generate_domain_insight, generate_comparative_analysis
from utils.db import get_all_institutions_summary, fetch_dataframe
 
DOMAINS = ["Académique", "Finance", "RH", "Recherche", "ESG / Environnement", "Infrastructure"]
 
_CSS = """
<style>
.ai-hero {
    background: linear-gradient(135deg, rgba(8,15,30,0.95) 0%, rgba(12,22,45,0.9) 50%, rgba(8,15,30,0.95) 100%);
    border: 1px solid rgba(154,230,180,0.1); border-radius: 16px; padding: 24px 32px; margin-bottom: 22px;
}
.insight-card {
    background: linear-gradient(145deg, rgba(10,22,18,0.9), rgba(6,15,12,0.95));
    border: 1px solid rgba(154,230,180,0.12); border-radius: 14px; padding: 22px 24px; margin-bottom:16px;
    position:relative; overflow:hidden;
}
.insight-card::before { content:''; position:absolute; top:-30px; right:-30px; width:150px; height:150px; background: radial-gradient(circle, rgba(154,230,180,0.06) 0%, transparent 70%); }
.insight-domain { font-family:'Syne',sans-serif; font-size:0.82rem; font-weight:700; color:#9ae6b4; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px; }
.insight-text { font-family:'DM Sans',sans-serif; font-size:0.88rem; color:#cbd5e0; line-height:1.75; white-space:pre-wrap; }
.ai-chip { display:inline-flex; align-items:center; gap:4px; background:rgba(154,230,180,0.1); color:#9ae6b4; border:1px solid rgba(154,230,180,0.15); border-radius:20px; font-family:'Syne',sans-serif; font-size:0.65rem; font-weight:700; letter-spacing:1px; padding:2px 8px; margin-bottom:6px; text-transform:uppercase; }
.no-data-box { background: rgba(8,18,14,0.5); border: 1px dashed rgba(154,230,180,0.15); border-radius: 12px; padding: 32px; text-align: center; font-family: 'DM Sans', sans-serif; color: #2a6a50; font-size: 0.9rem; }
</style>
"""
 
# Domain → relevant DB columns mapping
DOMAIN_COLS = {
    "Académique":         ["success_rate", "dropout_rate", "attendance_rate", "repetition_rate", "total_students", "passed_students"],
    "Finance":            ["budget_allocated", "budget_used", "budget_execution_rate", "cost_per_student"],
    "RH":                 ["staff_count", "absenteeism_rate", "teaching_load"],
    "Recherche":          ["publications", "projects", "funding"],
    "ESG / Environnement":["carbon_footprint", "energy_consumption", "recycling_rate"],
    "Infrastructure":     ["classrooms", "occupancy_rate"],
}
 
 
def _domain_data(domain: str) -> dict:
    """Extract relevant DB data for a domain and return as dict for Claude."""
    cols = DOMAIN_COLS.get(domain, [])
    df = fetch_dataframe()
    if df.empty:
        return {}
    num_cols = [c for c in cols if c in df.columns]
    if not num_cols or "institution" not in df.columns:
        return {}
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    agg = df.groupby("institution")[num_cols].mean().round(2).reset_index()
    return agg.to_dict(orient="records")
 
 
def render():
    st.markdown(_CSS, unsafe_allow_html=True)
 
    st.markdown("""
    <div class="ai-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e2e8f0;">AI Insights</div>
                <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#2a6a50; margin-top:4px;">Analyses intelligentes par domaine · Comparaison inter-institutions</div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#9ae6b4; background:rgba(154,230,180,0.06); border:1px solid rgba(154,230,180,0.12); border-radius:8px; padding:8px 14px; text-align:center;">
                CLAUDE AI<br><span style="color:#9ae6b4;">● CONNECTÉ</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    df_summary = get_all_institutions_summary()
 
    if df_summary.empty:
        st.markdown('<div class="no-data-box">📭 Aucune donnée disponible.<br>Importez des documents via <strong>Import de Données</strong>.</div>', unsafe_allow_html=True)
        return
 
    tab1, tab2 = st.tabs(["📊 Analyses par Domaine", "🔍 Analyse Comparative"])
 
    # ── TAB 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        cs, cb = st.columns([2, 1])
        sel_domain = cs.selectbox("Domaine d'analyse", DOMAINS, key="ai_domain")
        cb.markdown("<br>", unsafe_allow_html=True)
        run_btn = cb.button("🚀 Générer", use_container_width=True, key="ai_run")
 
        if run_btn:
            domain_data = _domain_data(sel_domain)
            with st.spinner(f"Analyse IA — **{sel_domain}**..."):
                insight = generate_domain_insight(sel_domain, data=domain_data)
            if "domain_insights" not in st.session_state:
                st.session_state.domain_insights = {}
            st.session_state.domain_insights[sel_domain] = insight
 
        if sel_domain in st.session_state.get("domain_insights", {}):
            insight = st.session_state.domain_insights[sel_domain]
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-domain">🤖 Analyse IA — {sel_domain}</div>
                <div class="insight-text">{insight}</div>
            </div>
            """, unsafe_allow_html=True)
 
        # Heatmap
        st.markdown("---")
        st.markdown("#### 🌡️ Heatmap des KPIs par Institution")
        num_cols = df_summary.select_dtypes(include="number").columns.tolist()
        if num_cols and "Institution" in df_summary.columns:
            hm = df_summary.set_index("Institution")[num_cols].fillna(0)
            fig = px.imshow(
                hm, color_continuous_scale=["#0a1e14", "#2a6a50", "#9ae6b4"],
                aspect="auto", labels=dict(color="Valeur"),
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#3a8a60", family="DM Sans"), height=380,
                margin=dict(t=10, b=10),
                coloraxis_colorbar=dict(tickfont=dict(color="#3a8a60")),
                xaxis=dict(tickfont=dict(color="#3a8a60")),
                yaxis=dict(tickfont=dict(color="#3a8a60")),
            )
            st.plotly_chart(fig, use_container_width=True)
 
    # ── TAB 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("#### 🔍 Analyse Comparative Inter-Institutions")
        insts = df_summary["Institution"].tolist() if "Institution" in df_summary.columns else []
 
        if len(insts) < 2:
            st.info("Au moins deux institutions nécessaires pour la comparaison.")
            return
 
        ca, cb2 = st.columns(2)
        inst_a = ca.selectbox("Institution A", insts, index=0, key="comp_a")
        inst_b = cb2.selectbox("Institution B", insts, index=min(1, len(insts)-1), key="comp_b")
 
        if st.button("⚖️ Lancer la comparaison", use_container_width=True, type="primary"):
            if inst_a == inst_b:
                st.warning("Veuillez sélectionner deux institutions différentes.")
            else:
                with st.spinner("Comparaison IA en cours..."):
                    analysis = generate_comparative_analysis(inst_a, inst_b, df_summary)
 
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-domain">⚖️ {inst_a} vs {inst_b}</div>
                    <div class="insight-text">{analysis}</div>
                </div>
                """, unsafe_allow_html=True)
 
                # Radar
                num_cols = [c for c in df_summary.select_dtypes(include="number").columns]
                if num_cols:
                    row_a = df_summary[df_summary["Institution"] == inst_a][num_cols].values.flatten().tolist()
                    row_b = df_summary[df_summary["Institution"] == inst_b][num_cols].values.flatten().tolist()
                    if row_a and row_b:
                        fig_r = go.Figure()
                        fig_r.add_trace(go.Scatterpolar(
                            r=row_a + [row_a[0]], theta=num_cols + [num_cols[0]],
                            fill="toself", name=inst_a, fillcolor="rgba(99,179,237,0.12)",
                            line=dict(color="#63b3ed", width=2),
                        ))
                        fig_r.add_trace(go.Scatterpolar(
                            r=row_b + [row_b[0]], theta=num_cols + [num_cols[0]],
                            fill="toself", name=inst_b, fillcolor="rgba(154,230,180,0.1)",
                            line=dict(color="#9ae6b4", width=2),
                        ))
                        fig_r.update_layout(
                            polar=dict(bgcolor="rgba(0,0,0,0)",
                                radialaxis=dict(visible=True, tickfont=dict(color="#3a8a60", size=8), gridcolor="rgba(154,230,180,0.05)"),
                                angularaxis=dict(tickfont=dict(color="#3a8a60"))),
                            paper_bgcolor="rgba(0,0,0,0)",
                            legend=dict(font=dict(color="#3a8a60"), bgcolor="rgba(0,0,0,0)"),
                            height=380, margin=dict(t=20),
                        )
                        st.plotly_chart(fig_r, use_container_width=True)