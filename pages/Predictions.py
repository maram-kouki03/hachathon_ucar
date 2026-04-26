"""
pages/Predictions.py
Track 2 — Smart Analytics & Decision Support
Real data only from Supabase via utils/db.py and utils/predictor.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

from utils.db import fetch_dataframe, get_institutions
from utils.predictor import predict_kpi_trend, get_risk_matrix

# ── KPI map: label → DB column name ──────────────────────────────────────────
PREDICTION_TARGETS = {
    "🎓 Taux de Réussite":           "success_rate",
    "💰 Exécution Budgétaire":       "budget_execution_rate",
    "👥 Effectifs Étudiants":        "total_students",
    "🌱 Empreinte Carbone":          "carbon_footprint",
    "🔬 Publications":               "publications",
    "👔 Absentéisme RH":             "absenteeism_rate",
    "🎯 Taux d'Abandon":             "dropout_rate",
    "🏗 Taux d'Occupation":          "occupancy_rate",
    "🤝 Mobilité Étudiante (entrée)":"student_mobility_in",
    "📊 Taux d'Assiduité":           "attendance_rate",
}

PCT_METRICS = {
    "success_rate", "budget_execution_rate", "absenteeism_rate",
    "dropout_rate", "occupancy_rate", "attendance_rate",
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono&display=swap');

.pred-hero {
    background: linear-gradient(135deg, rgba(8,30,30,0.97) 0%, rgba(10,42,40,0.93) 50%, rgba(8,30,30,0.97) 100%);
    border: 1px solid rgba(79,209,197,0.14);
    border-radius: 16px; padding: 26px 32px; margin-bottom: 22px;
}
.pred-control-row {
    background: rgba(8,22,22,0.85);
    border: 1px solid rgba(79,209,197,0.09);
    border-radius: 12px; padding: 18px 20px; margin-bottom: 20px;
}
.pred-kpi-card {
    background: linear-gradient(145deg, rgba(8,25,25,0.92), rgba(5,16,16,0.97));
    border: 1px solid rgba(79,209,197,0.13);
    border-radius: 14px; padding: 18px 16px; text-align: center;
    position: relative; overflow: hidden; height: 100%;
}
.pred-kpi-card::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(circle at 50% 0%, rgba(79,209,197,0.06) 0%, transparent 70%);
}
.pred-val   { font-family:'Syne',sans-serif; font-size:1.75rem; font-weight:800; color:#4fd1c5; }
.pred-label { font-family:'DM Sans',sans-serif; font-size:0.67rem; color:#2a6a65;
              text-transform:uppercase; letter-spacing:1.1px; margin-top:5px; }
.pred-sub   { font-family:'DM Sans',sans-serif; font-size:0.77rem; color:#3a8a84; margin-top:6px; }

.narrative-box {
    background: rgba(79,209,197,0.04);
    border: 1px solid rgba(79,209,197,0.13);
    border-left: 3px solid #4fd1c5;
    border-radius: 0 14px 14px 0;
    padding: 20px 26px;
    font-family:'DM Sans',sans-serif; font-size:0.9rem;
    color:#e2e8f0; line-height:1.75; margin-top:20px;
}
.risk-card {
    border-radius: 10px; padding: 13px 15px; margin-bottom: 9px;
    display:flex; align-items:flex-start; gap:10px;
}
.risk-high { background:rgba(252,129,129,0.07); border:1px solid rgba(252,129,129,0.18); }
.risk-med  { background:rgba(246,173,85,0.07);  border:1px solid rgba(246,173,85,0.18);  }
.risk-low  { background:rgba(104,211,145,0.07); border:1px solid rgba(104,211,145,0.18); }
.risk-title { font-family:'Syne',sans-serif; font-size:0.82rem; font-weight:700; margin-bottom:2px; }
.risk-high .risk-title { color:#fc8181; }
.risk-med  .risk-title { color:#f6ad55; }
.risk-low  .risk-title { color:#68d391; }
.risk-desc  { font-family:'DM Sans',sans-serif; font-size:0.77rem; color:#5a8a85; line-height:1.4; }

.no-data-box {
    background: rgba(252,129,129,0.05);
    border: 1px solid rgba(252,129,129,0.18);
    border-radius: 12px; padding: 22px 26px;
    font-family:'DM Sans',sans-serif; color:#fc8181; font-size:0.9rem;
    text-align:center; margin-top:20px;
}
.section-divider { border-top: 1px solid rgba(79,209,197,0.08); margin: 28px 0; }
</style>
"""


def _unit(metric: str) -> str:
    return "%" if metric in PCT_METRICS else ""


def _build_chart(result: dict, metric: str) -> go.Figure:
    """
    Build prediction chart.
    All x-values forced to strings — avoids the int+str crash in add_vline.
    Uses add_shape + add_annotation instead of add_vline.
    """
    historical  = result.get("historical", [])
    forecast    = result.get("forecast", [])
    upper       = result.get("upper_bound", [])
    lower       = result.get("lower_bound", [])
    hist_labels = [str(l) for l in result.get("historical_labels", [])]
    fut_labels  = [str(l) for l in result.get("future_labels", [])]
    all_labels  = hist_labels + fut_labels

    fig = go.Figure()

    if historical and hist_labels:
        fig.add_trace(go.Scatter(
            x=hist_labels, y=historical,
            mode='lines+markers', name='Historique',
            line=dict(color='#4fd1c5', width=2.5),
            marker=dict(size=6, color='#4fd1c5'),
        ))

    if forecast and fut_labels and upper and lower:
        fig.add_trace(go.Scatter(
            x=fut_labels + fut_labels[::-1],
            y=upper + lower[::-1],
            fill='toself', fillcolor='rgba(79,209,197,0.07)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Intervalle 95%', hoverinfo='skip',
        ))

    if forecast and fut_labels:
        fig.add_trace(go.Scatter(
            x=fut_labels, y=forecast,
            mode='lines+markers', name='Prédiction',
            line=dict(color='#9ae6b4', width=2, dash='dash'),
            marker=dict(size=7, color='#9ae6b4', symbol='diamond'),
        ))

    if hist_labels:
        today_x = hist_labels[-1]
        fig.add_shape(
            type="line",
            x0=today_x, x1=today_x, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="rgba(255,255,255,0.18)", dash="dot", width=1.2),
        )
        fig.add_annotation(
            x=today_x, y=1, xref="x", yref="paper",
            text="Aujourd'hui", showarrow=False,
            font=dict(color="#3a8a84", size=10),
            yanchor="bottom", bgcolor="rgba(0,0,0,0)",
        )

    unit = _unit(metric)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#3a8a84', family='DM Sans', size=10),
        height=400, margin=dict(t=24, b=20, l=10, r=10),
        legend=dict(font=dict(color='#3a8a84', size=9), bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(
            gridcolor='rgba(79,209,197,0.05)',
            tickfont=dict(color='#3a8a84'),
            categoryorder='array',
            categoryarray=all_labels,
        ),
        yaxis=dict(
            gridcolor='rgba(79,209,197,0.05)',
            tickfont=dict(color='#3a8a84'),
            ticksuffix=unit,
        ),
        hovermode='x unified',
    )
    return fig


def _multi_kpi_table(institution) -> pd.DataFrame:
    """Build real multi-KPI forecast table — all from Supabase."""
    rows = []
    for label, col in PREDICTION_TARGETS.items():
        try:
            inst_arg = institution if institution else "Toutes (Agrégé)"
            r = predict_kpi_trend(inst_arg, col, n_future=12)
            if not r or not r.get("historical"):
                continue
            unit = _unit(col)
            fc   = r.get("forecast", [])
            rows.append({
                "KPI":       label,
                "Actuel":    r.get("current_value", "N/A"),
                "3 mois":    f"{fc[2]}{unit}"  if len(fc) > 2  else "N/A",
                "6 mois":    f"{fc[5]}{unit}"  if len(fc) > 5  else "N/A",
                "1 an":      f"{fc[11]}{unit}" if len(fc) > 11 else "N/A",
                "Tendance":  r.get("trend", "—"),
                "Confiance": f"{r.get('confidence', 0)}%",
            })
        except Exception:
            continue
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def render():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="pred-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:1.85rem; font-weight:800; color:#e2e8f0;">
                    Prédictions &amp; Tendances
                </div>
                <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#2a8a84; margin-top:5px;">
                    Moteur analytique prédictif &middot; Anticipation des risques &middot; Données Supabase temps réel
                </div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#2a6a65;
                        background:rgba(79,209,197,0.06); border:1px solid rgba(79,209,197,0.13);
                        border-radius:8px; padding:9px 15px; text-align:center; line-height:1.6;">
                TRACK 2 · SMART ANALYTICS<br>
                <span style="color:#4fd1c5; font-size:0.88rem; font-weight:700;">LIVE DATA</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Load institutions ─────────────────────────────────────────────────────
    institutions_list = get_institutions()
    if not institutions_list:
        st.markdown("""
        <div class="no-data-box">
            ⚠️ Aucune donnée trouvée dans Supabase.<br>
            Importez des données via la page d'import avant d'utiliser les prédictions.
        </div>
        """, unsafe_allow_html=True)
        return

    inst_options = ["Toutes (Agrégé)"] + institutions_list

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown('<div class="pred-control-row">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    target_label = c1.selectbox("Indicateur", list(PREDICTION_TARGETS.keys()), key="pred_target")
    institution  = c2.selectbox("Institution", inst_options, key="pred_inst")
    horizon      = c3.selectbox("Horizon", ["3 mois", "6 mois", "1 an", "2 ans"], index=1, key="pred_horizon")
    c4.markdown("<br>", unsafe_allow_html=True)
    run_pred = c4.button("🚀 Lancer", type="primary", use_container_width=True, key="pred_run")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Run prediction ────────────────────────────────────────────────────────
    if run_pred or "prediction_data" not in st.session_state:
        metric   = PREDICTION_TARGETS[target_label]
        n_future = {"3 mois": 3, "6 mois": 6, "1 an": 12, "2 ans": 24}[horizon]
        db_inst  = None if institution == "Toutes (Agrégé)" else institution

        with st.spinner("Calcul en cours sur les données Supabase..."):
            result = predict_kpi_trend(
                institution if institution != "Toutes (Agrégé)" else "Toutes (Agrégé)",
                metric,
                n_future,
            )

        if not result or not result.get("historical"):
            st.markdown(f"""
            <div class="no-data-box">
                ⚠️ Données insuffisantes pour <strong>{target_label}</strong>
                — {institution}.<br>
                Au moins 2 années de données sont requises pour générer une prédiction.
            </div>
            """, unsafe_allow_html=True)
            _show_bottom_sections(institution)
            return

        st.session_state.prediction_data = {
            "result":       result,
            "target_label": target_label,
            "metric":       metric,
            "institution":  institution,
            "horizon":      horizon,
        }

    # ── Display prediction ────────────────────────────────────────────────────
    if "prediction_data" in st.session_state:
        d      = st.session_state.prediction_data
        result = d["result"]
        metric = d["metric"]

        # Summary cards
        c1, c2, c3, c4 = st.columns(4)
        cards = [
            ("Valeur Actuelle",            result.get("current_value", "N/A"), f"Confiance : {result.get('confidence', 0)}%"),
            ("Prédiction J+90",            result.get("pred_short", "N/A"),    "Court terme"),
            (f"Prédiction {d['horizon']}", result.get("pred_target", "N/A"),   "Cible horizon"),
            ("Tendance",                   result.get("trend", "—"),           result.get("trend_strength", "—")),
        ]
        for col, (lbl, val, sub) in zip([c1, c2, c3, c4], cards):
            col.markdown(f"""
            <div class="pred-kpi-card">
                <div class="pred-val">{val}</div>
                <div class="pred-label">{lbl}</div>
                <div class="pred-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_chart, col_risk = st.columns([1.6, 1], gap="medium")

        with col_chart:
            st.markdown(f"#### 📈 {d['target_label']} — Prédiction avec intervalles de confiance")
            st.plotly_chart(_build_chart(result, metric), use_container_width=True)
            hist_years = result.get("historical_labels", [])
            year_range = f"{hist_years[0]} → {hist_years[-1]}" if len(hist_years) >= 2 else (str(hist_years[0]) if hist_years else "—")
            st.caption(
                f"📊 {len(result.get('historical',[]))} point(s) de données · "
                f"Période : {year_range} · Institution : {d['institution']}"
            )

        with col_risk:
            st.markdown("#### ⚠️ Matrice de Risques")
            risks = get_risk_matrix(
                None if d["institution"] == "Toutes (Agrégé)" else d["institution"]
            )
            if risks:
                for risk in risks:
                    level = risk.get("level", "med")
                    css  = {"high": "risk-high", "med": "risk-med", "low": "risk-low"}.get(level, "risk-med")
                    icon = {"high": "🔴", "med": "🟡", "low": "🟢"}.get(level, "🟡")
                    st.markdown(f"""
                    <div class="risk-card {css}">
                        <span style="font-size:1rem; flex-shrink:0;">{icon}</span>
                        <div>
                            <div class="risk-title">{risk.get('title','Risque')}</div>
                            <div class="risk-desc">{risk.get('description','')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Aucun risque détecté pour cette sélection.")

        # Narrative
        st.markdown('<div class="narrative-box">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'Syne',sans-serif; font-size:0.74rem; font-weight:700;
                    color:#4fd1c5; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">
            🤖 Analyse Prédictive IA
        </div>
        """, unsafe_allow_html=True)
        try:
            from utils.ai_insights import generate_prediction_narrative
            narrative = generate_prediction_narrative(d["target_label"], d["institution"], result)
            st.markdown(narrative, unsafe_allow_html=True)
        except Exception:
            # Inline fallback from real data — no hardcoded mock text
            fc    = result.get("forecast", [])
            hist  = result.get("historical", [])
            trend = result.get("trend", "—")
            conf  = result.get("confidence", 0)
            unit  = _unit(metric)
            delta = round(fc[-1] - hist[-1], 2) if fc and hist else 0
            direction = "hausse" if delta > 0 else "baisse" if delta < 0 else "stabilité"
            st.markdown(f"""
            L'indicateur **{d['target_label']}** pour **{d['institution']}** affiche
            une valeur actuelle de **{result.get('current_value','N/A')}**.

            Le modèle de régression linéaire, entraîné sur **{len(hist)} point(s)** de données
            historiques Supabase, projette une **{direction} de {abs(delta)}{unit}**
            sur un horizon de {d['horizon']} (cible : **{result.get('pred_target','N/A')}**).

            Tendance détectée : **{trend}** · {result.get('trend_strength','—')}
            · Niveau de confiance : **{conf}%**
            """)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    _show_bottom_sections(institution)


def _show_bottom_sections(institution: str):
    """Multi-KPI table + inter-institution comparison + trend chart."""

    # ── Multi-KPI forecast table ──────────────────────────────────────────────
    st.markdown("#### 📋 Tableau de Prévisions Multi-KPI")
    with st.spinner("Calcul en cours..."):
        db_inst  = None if institution == "Toutes (Agrégé)" else institution
        df_table = _multi_kpi_table(db_inst)

    if df_table.empty:
        st.warning(
            "Données insuffisantes pour le tableau multi-KPI. "
            "Au moins 2 années de données par institution sont nécessaires."
        )
    else:
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Inter-institution snapshot ────────────────────────────────────────────
    st.markdown("#### 🏛 Comparaison Inter-Institutions (Données Réelles)")
    df_all = fetch_dataframe()
    if df_all.empty:
        st.warning("Aucune donnée disponible.")
        return

    snap_map = {
        "institution":          "Institution",
        "year":                 "Année",
        "success_rate":         "Réussite %",
        "budget_execution_rate":"Budget Exec %",
        "total_students":       "Étudiants",
        "absenteeism_rate":     "Absentéisme %",
        "dropout_rate":         "Abandon %",
        "publications":         "Publications",
        "carbon_footprint":     "CO₂ (T)",
        "occupancy_rate":       "Occupation %",
    }
    available = {k: v for k, v in snap_map.items() if k in df_all.columns}
    df_snap   = df_all[list(available.keys())].rename(columns=available).copy()

    if "Année" in df_snap.columns:
        df_snap["Année"] = pd.to_numeric(df_snap["Année"], errors="coerce")
        df_snap = (
            df_snap.sort_values("Année", ascending=False)
                   .groupby("Institution").first().reset_index()
        )
    for col in df_snap.select_dtypes(include="float").columns:
        df_snap[col] = df_snap[col].round(1)

    st.dataframe(df_snap, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Trend chart across institutions ───────────────────────────────────────
    st.markdown("#### 📊 Évolution Temporelle par Institution")

    if "year" not in df_all.columns:
        st.info("Colonne 'year' absente — graphe de tendance indisponible.")
        return

    metric_opts = {
        lbl: col for lbl, col in PREDICTION_TARGETS.items()
        if col in df_all.columns
    }
    if not metric_opts:
        return

    sel_label  = st.selectbox("Indicateur", list(metric_opts.keys()), key="trend_metric")
    sel_metric = metric_opts[sel_label]

    df_trend = df_all[["institution", "year", sel_metric]].copy()
    df_trend[sel_metric] = pd.to_numeric(df_trend[sel_metric], errors="coerce")
    df_trend["year"]     = pd.to_numeric(df_trend["year"], errors="coerce")
    df_trend = df_trend.dropna().sort_values("year")

    if df_trend.empty:
        st.info("Aucune donnée temporelle disponible pour cet indicateur.")
        return

    colors  = ["#4fd1c5","#9ae6b4","#f6ad55","#fc8181","#b794f4","#63b3ed","#fbd38d","#68d391"]
    fig_t   = go.Figure()
    unit    = _unit(sel_metric)

    for i, inst in enumerate(sorted(df_trend["institution"].dropna().unique())):
        sub = df_trend[df_trend["institution"] == inst]
        fig_t.add_trace(go.Scatter(
            x=sub["year"].astype(int).astype(str).tolist(),
            y=sub[sel_metric].round(2).tolist(),
            mode='lines+markers', name=inst,
            line=dict(color=colors[i % len(colors)], width=2.2),
            marker=dict(size=5),
        ))

    fig_t.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#3a8a84', family='DM Sans', size=10),
        height=360, margin=dict(t=20, b=20, l=10, r=10),
        legend=dict(font=dict(color='#3a8a84', size=9), bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(gridcolor='rgba(79,209,197,0.05)', tickfont=dict(color='#3a8a84')),
        yaxis=dict(
            gridcolor='rgba(79,209,197,0.05)',
            tickfont=dict(color='#3a8a84'),
            ticksuffix=unit,
        ),
        hovermode='x unified',
    )
    st.plotly_chart(fig_t, use_container_width=True)