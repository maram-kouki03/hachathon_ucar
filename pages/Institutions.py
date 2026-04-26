"""
pages/Institutions.py — Detailed institution view from real Supabase data.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
 
from utils.db import get_institutions, get_institution_detail, get_all_institutions_summary, fetch_dataframe
 
_CSS = """
<style>
.inst-hero {
    background: linear-gradient(135deg, rgba(26,15,60,0.95) 0%, rgba(40,20,90,0.9) 50%, rgba(26,15,60,0.95) 100%);
    border: 1px solid rgba(183,148,244,0.15); border-radius: 16px;
    padding: 28px 32px; margin-bottom: 20px; position: relative; overflow: hidden;
}
.inst-hero::before {
    content:''; position:absolute; top:-40px; right:-40px; width:250px; height:250px;
    background: radial-gradient(circle, rgba(183,148,244,0.08) 0%, transparent 70%);
}
.inst-name { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e2e8f0; }
.inst-type-badge { display:inline-flex; align-items:center; gap:6px; background: rgba(183,148,244,0.12); border: 1px solid rgba(183,148,244,0.2); border-radius:20px; padding:4px 12px; margin-top:8px; font-family:'DM Sans',sans-serif; font-size:0.75rem; color:#b794f4; }
 
.kpi-mini { background: rgba(15,10,35,0.8); border: 1px solid rgba(183,148,244,0.1); border-radius: 12px; padding: 14px 12px; text-align:center; transition: border-color 0.2s; }
.kpi-mini:hover { border-color: rgba(183,148,244,0.25); }
.kpi-mini-icon { font-size:1.1rem; margin-bottom:6px; display:block; }
.kpi-mini-val { font-family:'Syne',sans-serif; font-size:1.35rem; font-weight:800; color:#b794f4; }
.kpi-mini-lbl { font-family:'DM Sans',sans-serif; font-size:0.65rem; color:#5a3f7a; text-transform:uppercase; letter-spacing:0.8px; margin-top:3px; }
 
.chart-panel { background: rgba(10,6,25,0.7); border: 1px solid rgba(183,148,244,0.08); border-radius: 14px; padding: 18px; margin-bottom: 14px; }
.chart-panel-title { font-family:'Syne',sans-serif; font-size:0.82rem; font-weight:700; color:#7a5aaa; margin-bottom:14px; text-transform:uppercase; letter-spacing:0.5px; }
 
.no-data-box { background: rgba(10,6,25,0.5); border: 1px dashed rgba(183,148,244,0.2); border-radius: 12px; padding: 32px; text-align: center; font-family: 'DM Sans', sans-serif; color: #5a3f7a; font-size: 0.9rem; }
</style>
"""
 
 
def _layout(height=240, barmode=None):
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6a4a9a", family="DM Sans", size=10),
        height=height, margin=dict(t=8, b=8, l=8, r=8),
        legend=dict(font=dict(color="#7a5aaa", size=9), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(183,148,244,0.05)", tickfont=dict(color="#6a4a9a")),
        yaxis=dict(gridcolor="rgba(183,148,244,0.05)", tickfont=dict(color="#6a4a9a")),
    )
    if barmode:
        layout["barmode"] = barmode
    return layout
 
 
def render():
    st.markdown(_CSS, unsafe_allow_html=True)
 
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e2e8f0;">Institutions</div>
        <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#6a4a9a;">Vue détaillée par institution · KPIs & tendances · Analyse comparative</div>
    </div>
    """, unsafe_allow_html=True)
 
    institutions = get_institutions()
 
    if not institutions:
        st.markdown("""
        <div class="no-data-box">
            📭 Aucune institution dans la base de données.<br>
            Importez des documents via <strong>Import de Données</strong>.
        </div>
        """, unsafe_allow_html=True)
        return
 
    col_sel, col_view = st.columns([2, 1])
    selected = col_sel.selectbox("Sélectionner une institution", institutions, key="inst_select")
    view_mode = col_view.radio("Vue", ["Détail", "Comparatif"], horizontal=True, key="inst_view")
 
    if view_mode == "Détail":
        _render_detail(selected)
    else:
        _render_comparative()
 
 
def _render_detail(institution: str):
    data = get_institution_detail(institution)
 
    if not data:
        st.warning(f"Aucune donnée disponible pour **{institution}**.")
        return
 
    info = data.get("info", {})
    kpis = data.get("kpis", {})
    raw  = data.get("raw", {})
    all_rows = data.get("all_rows", pd.DataFrame())
 
    # ── Hero ──────────────────────────────────────────────────────────────────
    score = kpis.get("success_rate", "N/A")
    st.markdown(f"""
    <div class="inst-hero">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
            <div>
                <div class="inst-name">🏛️ {institution}</div>
                <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#7a5aaa; margin-top:6px;">
                    📅 Année {info.get('founded', '—')}
                    {f" &nbsp;·&nbsp; 📂 {info.get('type','')}" if info.get('type') else ''}
                </div>
                <div class="inst-type-badge">🎓 {info.get('type','Institution')}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'DM Sans',sans-serif; font-size:0.7rem; color:#5a3f7a; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Réussite</div>
                <div style="font-family:'Syne',sans-serif; font-size:2.8rem; font-weight:800; color:#b794f4; line-height:1;">{score}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    # ── KPI mini grid ─────────────────────────────────────────────────────────
    kpi_items = [
        ("👥", "Étudiants",    kpis.get("students", "N/A")),
        ("🎓", "Réussite",     kpis.get("success_rate", "N/A")),
        ("💰", "Budget Exec.", kpis.get("budget_exec", "N/A")),
        ("👨‍🏫","Personnel",     kpis.get("teachers", "N/A")),
        ("🔬", "Publications", kpis.get("publications", "N/A")),
        ("🌱", "CO₂ (T)",      kpis.get("co2", "N/A")),
    ]
    cols = st.columns(6)
    for col, (icon, label, val) in zip(cols, kpi_items):
        col.markdown(f"""
        <div class="kpi-mini">
            <span class="kpi-mini-icon">{icon}</span>
            <div class="kpi-mini-val">{val}</div>
            <div class="kpi-mini-lbl">{label}</div>
        </div>
        """, unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # ── Charts from real data ─────────────────────────────────────────────────
    if not all_rows.empty and "year" in all_rows.columns:
        all_rows["year"] = pd.to_numeric(all_rows["year"], errors="coerce")
        by_year = all_rows.dropna(subset=["year"]).sort_values("year")
 
        c1, c2, c3 = st.columns(3)
 
        with c1:
            st.markdown('<div class="chart-panel"><div class="chart-panel-title">📈 Taux de Réussite (historique)</div>', unsafe_allow_html=True)
            if "success_rate" in by_year.columns:
                sr = by_year.groupby("year")["success_rate"].mean().reset_index()
                sr["success_rate"] = pd.to_numeric(sr["success_rate"], errors="coerce")
                fig = go.Figure(go.Scatter(
                    x=sr["year"].astype(str), y=sr["success_rate"],
                    mode="lines+markers",
                    line=dict(color="#b794f4", width=2.5),
                    marker=dict(color="#b794f4", size=7),
                    fill="tozeroy", fillcolor="rgba(183,148,244,0.06)",
                ))
                fig.update_layout(_layout(220))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Données de réussite non disponibles.")
            st.markdown("</div>", unsafe_allow_html=True)
 
        with c2:
            st.markdown('<div class="chart-panel"><div class="chart-panel-title">💰 Budget Alloué vs Consommé</div>', unsafe_allow_html=True)
            if "budget_allocated" in by_year.columns and "budget_used" in by_year.columns:
                ba = by_year.groupby("year")[["budget_allocated", "budget_used"]].mean().reset_index()
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(name="Alloué",   x=ba["year"].astype(str), y=pd.to_numeric(ba["budget_allocated"], errors="coerce"), marker_color="rgba(183,148,244,0.25)", marker_line_color="#b794f4", marker_line_width=1))
                fig2.add_trace(go.Bar(name="Consommé", x=ba["year"].astype(str), y=pd.to_numeric(ba["budget_used"], errors="coerce"),      marker_color="#b794f4", opacity=0.9))
                fig2.update_layout(_layout(220, barmode="group"))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Données budgétaires non disponibles.")
            st.markdown("</div>", unsafe_allow_html=True)
 
        with c3:
            st.markdown('<div class="chart-panel"><div class="chart-panel-title">📊 Indicateurs Académiques</div>', unsafe_allow_html=True)
            acad_cols = [c for c in ["success_rate", "dropout_rate", "attendance_rate", "repetition_rate"] if c in by_year.columns]
            if acad_cols:
                acad = by_year.groupby("year")[acad_cols].mean().reset_index()
                fig3 = go.Figure()
                colors = ["#b794f4", "#fc8181", "#63b3ed", "#f6ad55"]
                for i, col in enumerate(acad_cols):
                    fig3.add_trace(go.Bar(
                        name=col.replace("_", " ").title(),
                        x=acad["year"].astype(str),
                        y=pd.to_numeric(acad[col], errors="coerce"),
                        marker_color=colors[i % len(colors)], opacity=0.85,
                    ))
                fig3.update_layout(_layout(220, barmode="group"))
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Données académiques non disponibles.")
            st.markdown("</div>", unsafe_allow_html=True)
 
        # Row 2
        c4, c5 = st.columns(2)
 
        with c4:
            st.markdown('<div class="chart-panel"><div class="chart-panel-title">👥 Ressources Humaines</div>', unsafe_allow_html=True)
            hr_cols = [c for c in ["staff_count", "absenteeism_rate"] if c in by_year.columns]
            if hr_cols:
                hr = by_year.groupby("year")[hr_cols].mean().reset_index()
                fig4 = go.Figure()
                for col in hr_cols:
                    fig4.add_trace(go.Scatter(
                        x=hr["year"].astype(str), y=pd.to_numeric(hr[col], errors="coerce"),
                        mode="lines+markers", name=col.replace("_", " ").title(),
                        line=dict(width=2),
                    ))
                fig4.update_layout(_layout(230))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Données RH non disponibles.")
            st.markdown("</div>", unsafe_allow_html=True)
 
        with c5:
            st.markdown('<div class="chart-panel"><div class="chart-panel-title">🌱 Indicateurs ESG</div>', unsafe_allow_html=True)
            esg_cols = [c for c in ["carbon_footprint", "energy_consumption", "recycling_rate"] if c in by_year.columns]
            if esg_cols:
                esg = by_year.groupby("year")[esg_cols].mean().reset_index()
                fig5 = go.Figure()
                esg_colors = ["#9ae6b4", "#63b3ed", "#f6ad55"]
                for i, col in enumerate(esg_cols):
                    fig5.add_trace(go.Bar(
                        name=col.replace("_", " ").title(),
                        x=esg["year"].astype(str),
                        y=pd.to_numeric(esg[col], errors="coerce"),
                        marker_color=esg_colors[i % len(esg_colors)], opacity=0.85,
                    ))
                fig5.update_layout(_layout(230, barmode="group"))
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info("Données ESG non disponibles.")
            st.markdown("</div>", unsafe_allow_html=True)
 
    # Raw data expander
    with st.expander("📋 Voir toutes les données brutes"):
        if not all_rows.empty:
            disp = all_rows.drop(columns=["data", "id", "created_at"], errors="ignore")
            st.dataframe(disp, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée brute disponible.")
 
 
def _render_comparative():
    st.markdown("### 📊 Tableau Comparatif — Toutes les Institutions")
    df = get_all_institutions_summary()
 
    if df.empty:
        st.info("Importez des données pour voir la comparaison.")
        return
 
    # Bubble chart
    x_col     = "Budget Exec %" if "Budget Exec %" in df.columns else df.select_dtypes("number").columns[0]
    y_col     = "Réussite %"    if "Réussite %" in df.columns    else df.select_dtypes("number").columns[1]
    size_col  = "Étudiants"     if "Étudiants" in df.columns     else None
    color_col = "Score Global"  if "Score Global" in df.columns  else y_col
 
    fig = px.scatter(
        df, x=x_col, y=y_col,
        size=size_col,
        color=color_col, text="Institution",
        color_continuous_scale=["#fc8181", "#f6ad55", "#9ae6b4"],
        size_max=50,
    )
    fig.update_traces(textfont=dict(color="#e2e8f0", size=10))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#7a5aaa", family="DM Sans"),
        height=420, margin=dict(t=10, b=10),
        xaxis=dict(gridcolor="rgba(183,148,244,0.05)", title=x_col),
        yaxis=dict(gridcolor="rgba(183,148,244,0.05)", title=y_col),
        coloraxis_colorbar=dict(title="Score", tickfont=dict(color="#7a5aaa")),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)