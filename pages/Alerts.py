"""
pages/Alerts.py — Real anomaly detection from Supabase data.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
 
from utils.alerts import get_all_alerts, get_alert_stats, update_thresholds
from utils.db import fetch_dataframe
 
_CSS = """
<style>
.alerts-hero {
    background: linear-gradient(135deg, rgba(30,8,8,0.95) 0%, rgba(45,12,12,0.9) 50%, rgba(30,8,8,0.95) 100%);
    border: 1px solid rgba(252,129,129,0.12); border-radius: 16px; padding: 24px 32px; margin-bottom: 22px;
}
.stat-card { border-radius: 14px; padding: 18px 16px; text-align:center; position:relative; overflow:hidden; }
.stat-card.critical  { background:linear-gradient(145deg,rgba(45,12,12,0.9),rgba(30,8,8,0.95)); border:1px solid rgba(252,129,129,0.15); }
.stat-card.warning   { background:linear-gradient(145deg,rgba(40,22,8,0.9),rgba(28,15,5,0.95)); border:1px solid rgba(246,173,85,0.15); }
.stat-card.info      { background:linear-gradient(145deg,rgba(8,18,32,0.9),rgba(5,12,22,0.95)); border:1px solid rgba(99,179,237,0.15); }
.stat-card.ok        { background:linear-gradient(145deg,rgba(8,28,14,0.9),rgba(5,18,9,0.95));  border:1px solid rgba(104,211,145,0.15); }
.stat-num { font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800; line-height:1; margin-bottom:4px; }
.stat-num.critical { color:#fc8181; } .stat-num.warning { color:#f6ad55; }
.stat-num.info { color:#63b3ed; }     .stat-num.ok { color:#68d391; }
.stat-label { font-family:'DM Sans',sans-serif; font-size:0.68rem; text-transform:uppercase; letter-spacing:1px; opacity:0.5; }
 
.alert-row { padding: 12px 14px; border-radius: 10px; margin-bottom:8px; display:flex; align-items:flex-start; gap:12px; font-family:'DM Sans',sans-serif; }
.alert-row.critical { background:rgba(252,129,129,0.06); border:1px solid rgba(252,129,129,0.12); border-left:3px solid #fc8181; }
.alert-row.warning  { background:rgba(246,173,85,0.06);  border:1px solid rgba(246,173,85,0.12);  border-left:3px solid #f6ad55; }
.alert-row.info     { background:rgba(99,179,237,0.06);  border:1px solid rgba(99,179,237,0.12);  border-left:3px solid #63b3ed; }
.a-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:5px; }
.a-dot.critical { background:#fc8181; box-shadow:0 0 6px rgba(252,129,129,0.5); }
.a-dot.warning  { background:#f6ad55; } .a-dot.info { background:#63b3ed; }
.a-msg  { font-size:0.84rem; color:#e2e8f0; line-height:1.4; margin-bottom:3px; }
.a-meta { font-size:0.73rem; color:#4a3030; }
 
.badge-label { display:inline-flex; align-items:center; padding:2px 8px; border-radius:20px; font-size:0.68rem; font-weight:700; font-family:'Syne',sans-serif; letter-spacing:0.5px; margin-right:6px; }
.badge-label.critical { background:rgba(252,129,129,0.15); color:#fc8181; border:1px solid rgba(252,129,129,0.2); }
.badge-label.warning  { background:rgba(246,173,85,0.15);  color:#f6ad55; border:1px solid rgba(246,173,85,0.2); }
.badge-label.info     { background:rgba(99,179,237,0.15);  color:#63b3ed; border:1px solid rgba(99,179,237,0.2); }
 
.no-alert-box { background: rgba(8,28,14,0.5); border: 1px dashed rgba(104,211,145,0.2); border-radius: 12px; padding: 32px; text-align: center; font-family: 'DM Sans', sans-serif; color: #4a9a6a; font-size: 0.9rem; }
</style>
"""
 
 
def render():
    st.markdown(_CSS, unsafe_allow_html=True)
 
    # Threshold state
    if "alert_thresholds" not in st.session_state:
        st.session_state.alert_thresholds = {
            "success_rate_min": 70,
            "budget_exec_min": 70,
            "absenteeism_max": 12,
            "dropout_max": 10,
            "carbon_max": 300,
        }
 
    st.markdown("""
    <div class="alerts-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e2e8f0;">Alertes & Monitoring</div>
                <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#7a2a2a; margin-top:4px;">Détection d'anomalies en temps réel · Seuils KPI configurables</div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#fc8181; background:rgba(252,129,129,0.08); border:1px solid rgba(252,129,129,0.15); border-radius:8px; padding:8px 14px; text-align:center;">
                SENTINEL<br><span style="color:#fc8181;">● ACTIF</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    # Stats
    stats = get_alert_stats(thresholds=st.session_state.alert_thresholds)
    total = stats["critical"] + stats["warning"] + stats["info"]
 
    c1, c2, c3, c4 = st.columns(4)
    for col, level, label, val in [
        (c1, "critical", "Critiques",      stats["critical"]),
        (c2, "warning",  "Avertissements", stats["warning"]),
        (c3, "info",     "Informations",   stats["info"]),
        (c4, "ok",       "Total alertes",  total),
    ]:
        col.markdown(f"""
        <div class="stat-card {level}">
            <div class="stat-num {level}">{val}</div>
            <div class="stat-label" style="color:{'#fc8181' if level=='critical' else '#f6ad55' if level=='warning' else '#63b3ed' if level=='info' else '#68d391'};">{label}</div>
        </div>
        """, unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # Filters
    cf1, cf2, cf3 = st.columns(3)
    filter_level = cf1.selectbox("Niveau", ["Tous", "Critique", "Avertissement", "Info"], key="af_level")
    filter_dom   = cf2.selectbox("Domaine", ["Tous", "Finance", "Académique", "RH", "ESG", "Infrastructure", "Recherche"], key="af_domain")
 
    # Get all institutions from DB
    df_all = fetch_dataframe()
    inst_options = ["Toutes"]
    if not df_all.empty and "institution" in df_all.columns:
        inst_options += sorted(df_all["institution"].dropna().unique().tolist())
    filter_inst = cf3.selectbox("Institution", inst_options, key="af_inst")
 
    alerts = get_all_alerts(thresholds=st.session_state.alert_thresholds)
 
    level_map = {"Critique": "critical", "Avertissement": "warning", "Info": "info"}
    if filter_level != "Tous":
        alerts = [a for a in alerts if a.get("level") == level_map.get(filter_level, "")]
    if filter_dom != "Tous":
        alerts = [a for a in alerts if a.get("domain", "").lower() == filter_dom.lower()]
    if filter_inst != "Toutes":
        alerts = [a for a in alerts if filter_inst in a.get("institution", "")]
 
    col_feed, col_charts = st.columns([1.3, 1], gap="medium")
 
    with col_feed:
        st.markdown(f"**{len(alerts)} alerte(s) correspondant aux critères**")
        if not alerts:
            st.markdown('<div class="no-alert-box">✅ Aucune alerte pour ces critères.<br>Ajustez les filtres ou vérifiez les seuils.</div>', unsafe_allow_html=True)
        else:
            for alert in alerts[:20]:
                level  = alert.get("level", "info")
                msg    = alert.get("message", "")
                inst   = alert.get("institution", "UCAR")
                domain = alert.get("domain", "Général")
                ts     = alert.get("timestamp", "")
                level_label = {"critical": "🔴 CRITIQUE", "warning": "🟡 AVERT.", "info": "🔵 INFO"}.get(level, level.upper())
                st.markdown(f"""
                <div class="alert-row {level}">
                    <div class="a-dot {level}"></div>
                    <div style="flex:1;">
                        <div class="a-msg">
                            <span class="badge-label {level}">{level_label}</span>{msg}
                        </div>
                        <div class="a-meta">🏛️ {inst} · 📂 {domain} · 📅 {ts}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
 
    with col_charts:
        # Distribution by domain
        st.markdown("#### 🍩 Alertes par Domaine")
        if alerts:
            from collections import Counter
            domain_counts = Counter(a.get("domain", "Autre") for a in alerts)
            fig_p = go.Figure(go.Pie(
                labels=list(domain_counts.keys()), values=list(domain_counts.values()), hole=0.6,
                marker=dict(colors=["#63b3ed", "#9ae6b4", "#f6ad55", "#fc8181", "#b794f4", "#4fd1c5"]),
                textfont=dict(color="#e2e8f0", size=10),
            ))
            fig_p.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#7a3a3a"),
                legend=dict(font=dict(color="#7a3a3a", size=9), bgcolor="rgba(0,0,0,0)"),
                height=260, margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.info("Aucune alerte à afficher.")
 
        # By level bar
        st.markdown("#### 📊 Par Niveau")
        level_counts = {"Critique": stats["critical"], "Avertissement": stats["warning"], "Info": stats["info"]}
        fig_b = go.Figure(go.Bar(
            x=list(level_counts.keys()), y=list(level_counts.values()),
            marker_color=["#fc8181", "#f6ad55", "#63b3ed"], opacity=0.85,
        ))
        fig_b.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#7a3a3a", family="DM Sans", size=10),
            xaxis=dict(gridcolor="rgba(252,129,129,0.04)", tickfont=dict(color="#7a3a3a")),
            yaxis=dict(gridcolor="rgba(252,129,129,0.04)", tickfont=dict(color="#7a3a3a")),
            height=220, margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_b, use_container_width=True)
 
    # ── Threshold configuration ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### ⚙️ Configuration des Seuils")
    with st.expander("Modifier les seuils de déclenchement"):
        ct1, ct2, ct3 = st.columns(3)
        with ct1:
            sr_min = st.slider("Réussite min (%)", 50, 90,
                               st.session_state.alert_thresholds["success_rate_min"], key="ts_success")
            ab_max = st.slider("Absentéisme max (%)", 5, 30,
                               st.session_state.alert_thresholds["absenteeism_max"], key="ts_abs")
        with ct2:
            be_min = st.slider("Exécution budget min (%)", 50, 95,
                               st.session_state.alert_thresholds["budget_exec_min"], key="ts_budget")
            dr_max = st.slider("Abandon max (%)", 5, 30,
                               st.session_state.alert_thresholds["dropout_max"], key="ts_dropout")
        with ct3:
            co2_max = st.slider("CO₂ max (T)", 100, 600,
                                st.session_state.alert_thresholds["carbon_max"], key="ts_carbon")
 
        if st.button("💾 Appliquer les seuils", type="primary"):
            new_thresholds = {
                "success_rate_min": sr_min,
                "absenteeism_max":  ab_max,
                "budget_exec_min":  be_min,
                "dropout_max":      dr_max,
                "carbon_max":       co2_max,
            }
            st.session_state.alert_thresholds = new_thresholds
            update_thresholds(new_thresholds)
            st.success("✅ Seuils mis à jour. Les alertes ont été recalculées.")
            st.rerun()
 