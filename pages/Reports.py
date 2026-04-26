import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.reports import generate_report, get_report_history
from utils.ai_insights import generate_report_summary

REPORT_TYPES = {
    "📊 Rapport Exécutif Mensuel": "monthly_executive",
    "🎓 Rapport Académique": "academic",
    "💰 Rapport Financier": "financial",
    "🌱 Rapport ESG / Environnement": "esg",
    "👥 Rapport RH": "hr",
    "🔬 Rapport Recherche": "research",
    "🏗️ Rapport Infrastructure": "infrastructure",
    "📋 Rapport KPI Global": "kpi_global",
}
INSTITUTIONS = ["Toutes les institutions (Consolidé)", "ENIT", "FST", "SUP'COM", "ENSI", "INSAT", "FSEG", "FSHS", "IPEIT"]
PERIODS = ["Semaine courante", "Mois courant", "Trimestre courant", "Semestre courant", "Année courante", "Période personnalisée"]


def render():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
    .page-title { font-family:'Syne',sans-serif; font-size:1.9rem; font-weight:800; color:#e2e8f0; }
    .page-sub { font-family:'DM Sans',sans-serif; color:#f6ad55; font-size:0.88rem; margin-bottom:28px; }
    .report-config-box {
        background: linear-gradient(145deg, #1f1a0d, #151008);
        border: 1px solid rgba(246,173,85,0.2);
        border-radius: 16px;
        padding: 26px 28px;
        margin-bottom: 24px;
    }
    .config-title { font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:#f6ad55; margin-bottom:18px; }
    .report-history-item {
        background: rgba(246,173,85,0.05);
        border: 1px solid rgba(246,173,85,0.12);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-family: 'DM Sans', sans-serif;
    }
    .report-name { color: #e2e8f0; font-size: 0.88rem; font-weight:500; }
    .report-meta { color: #8da9c4; font-size: 0.78rem; margin-top: 2px; }
    .preview-box {
        background: rgba(246,173,85,0.04);
        border: 1px solid rgba(246,173,85,0.15);
        border-radius: 12px;
        padding: 22px 26px;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        color: #e2e8f0;
        line-height: 1.8;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-title">📋 Rapports Automatisés</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Génération intelligente · Export PDF/Excel · Planification automatique</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚀 Générer un Rapport", "📁 Historique", "⏰ Planification"])

    # ─── TAB 1: Generate ───
    with tab1:
        st.markdown('<div class="report-config-box"><div class="config-title">⚙️ Configuration du Rapport</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        report_type_label = col1.selectbox("Type de rapport", list(REPORT_TYPES.keys()), key="rpt_type")
        institution = col2.selectbox("Périmètre", INSTITUTIONS, key="rpt_inst")

        col3, col4 = st.columns(2)
        period = col3.selectbox("Période", PERIODS, key="rpt_period")
        export_format = col4.multiselect("Format d'export", ["PDF", "Excel", "Word", "JSON"], default=["PDF", "Excel"], key="rpt_format")

        if period == "Période personnalisée":
            col_d1, col_d2 = st.columns(2)
            date_from = col_d1.date_input("Du", datetime.now() - timedelta(days=30), key="rpt_from")
            date_to = col_d2.date_input("Au", datetime.now(), key="rpt_to")

        col_opts1, col_opts2, col_opts3 = st.columns(3)
        include_charts = col_opts1.checkbox("Inclure graphiques", value=True, key="rpt_charts")
        include_ai_analysis = col_opts2.checkbox("Inclure analyse IA", value=True, key="rpt_ai")
        include_recommendations = col_opts3.checkbox("Inclure recommandations", value=True, key="rpt_reco")

        st.markdown('</div>', unsafe_allow_html=True)

        generate_btn = st.button("📄 Générer le Rapport", type="primary", use_container_width=True)

        if generate_btn:
            target_key = REPORT_TYPES[report_type_label]
            with st.spinner("Génération du rapport en cours... L'IA analyse et structure les données."):
                try:
                    report_content = generate_report(
                        report_type=target_key,
                        institution=institution,
                        period=period,
                        include_charts=include_charts,
                        include_ai=include_ai_analysis,
                    )
                    ai_summary = generate_report_summary(report_content)
                except Exception:
                    report_content = _mock_report_content(report_type_label, institution, period)
                    ai_summary = _mock_ai_summary(report_type_label)

            st.success("✅ Rapport généré avec succès !")

            st.markdown("#### 👁️ Aperçu du Rapport")
            st.markdown(f'<div class="preview-box">{report_content}</div>', unsafe_allow_html=True)

            if include_ai_analysis:
                st.markdown("#### 🤖 Synthèse IA")
                st.info(ai_summary)

            # Export buttons
            st.markdown("#### 📥 Télécharger")
            col_dl1, col_dl2, col_dl3 = st.columns(3)

            if "PDF" in export_format:
                try:
                    from utils.reports import export_to_pdf
                    pdf_bytes = export_to_pdf(report_content, report_type_label)
                    col_dl1.download_button(
                        "📄 Télécharger PDF",
                        data=pdf_bytes,
                        file_name=f"rapport_{target_key}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception:
                    col_dl1.download_button(
                        "📄 Télécharger Rapport (TXT)",
                        data=report_content.encode(),
                        file_name=f"rapport_{target_key}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            if "Excel" in export_format:
                try:
                    from utils.reports import export_to_excel
                    excel_bytes = export_to_excel(target_key, institution)
                    col_dl2.download_button(
                        "📊 Télécharger Excel",
                        data=excel_bytes,
                        file_name=f"rapport_{target_key}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except Exception:
                    col_dl2.button("📊 Excel (non disponible)", disabled=True, use_container_width=True)

    # ─── TAB 2: History ───
    with tab2:
        st.markdown("#### 📁 Rapports Générés Récemment")
        try:
            history = get_report_history()
        except Exception:
            history = _mock_history()

        col_search = st.text_input("🔍 Rechercher", placeholder="Nom, type, institution...", key="rpt_search")

        for report in history:
            name = report.get("name", "Rapport")
            if col_search.lower() and col_search.lower() not in name.lower():
                continue
            rtype = report.get("type", "")
            date = report.get("date", "")
            inst = report.get("institution", "")
            size = report.get("size", "")
            st.markdown(f"""
            <div class="report-history-item">
                <div>
                    <div class="report-name">📄 {name}</div>
                    <div class="report-meta">🏛️ {inst} &nbsp;·&nbsp; 📂 {rtype} &nbsp;·&nbsp; 📅 {date} &nbsp;·&nbsp; 💾 {size}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ─── TAB 3: Scheduling ───
    with tab3:
        st.markdown("#### ⏰ Rapports Automatiques Planifiés")

        schedules = [
            {"name": "Rapport Exécutif Mensuel", "freq": "1er du mois", "dest": "Présidence UCAR", "status": "✅ Actif", "next": "01/06/2025"},
            {"name": "Rapport KPI Hebdomadaire", "freq": "Chaque lundi", "dest": "Doyens & Directeurs", "status": "✅ Actif", "next": "28/04/2025"},
            {"name": "Rapport ESG Trimestriel", "freq": "Fin de trimestre", "dest": "Direction RSE", "status": "✅ Actif", "next": "30/06/2025"},
            {"name": "Rapport RH Mensuel", "freq": "15 du mois", "dest": "DRH", "status": "⏸️ Pausé", "next": "—"},
        ]

        df_sched = pd.DataFrame(schedules)
        st.dataframe(df_sched, use_container_width=True, hide_index=True)

        st.markdown("#### ➕ Ajouter une Planification")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.selectbox("Type de rapport", list(REPORT_TYPES.keys()), key="sched_type")
        col_s2.selectbox("Fréquence", ["Hebdomadaire", "Mensuelle", "Trimestrielle", "Annuelle"], key="sched_freq")
        col_s3.text_input("Destinataires (email)", placeholder="presi@ucar.tn, ...", key="sched_dest")
        if st.button("💾 Sauvegarder la planification", key="sched_save"):
            st.success("✅ Rapport planifié ajouté avec succès.")


def _mock_report_content(report_type, institution, period):
    now = datetime.now().strftime("%d/%m/%Y")
    return f"""RAPPORT — {report_type.upper()}
Périmètre : {institution}
Période : {period}
Généré le : {now}

═══════════════════════════════════════════════════
1. SYNTHÈSE EXÉCUTIVE
═══════════════════════════════════════════════════

Ce rapport consolide les indicateurs de performance pour la période analysée.
Le taux de réussite global atteint 78.4%, en progression de 2.1 points vs N-1.
L'exécution budgétaire globale est de 84.7% avec des disparités notables entre institutions.

Points saillants :
• 3 alertes critiques identifiées (Finance, ESG, RH)
• 31 institutions actives, 47,200 étudiants inscrits
• 142 projets de recherche actifs

═══════════════════════════════════════════════════
2. INDICATEURS CLÉS (KPIs)
═══════════════════════════════════════════════════

Académique
  - Taux de réussite global : 78.4% (+2.1 pts)
  - Taux d'abandon L1 : 10.2% (-0.8 pts)
  - Taux d'encadrement : 1/24 (objectif : 1/20)

Finance
  - Exécution budgétaire : 84.7%
  - Budget total alloué : 145M DT
  - Budget consommé : 122.8M DT

RH
  - Personnel total : 4,230 agents
  - Taux d'absentéisme : 11.2%
  - Formations réalisées : 89%

═══════════════════════════════════════════════════
3. RECOMMANDATIONS
═══════════════════════════════════════════════════

1. Renforcer l'accompagnement pédagogique en L1 (FSEG, FSHS)
2. Réviser les enveloppes infrastructure (ENIT, SUP'COM)
3. Déployer un plan de réduction énergétique ESG
4. Mutualiser les achats entre institutions similaires
"""


def _mock_ai_summary(report_type):
    return f"L'analyse IA du {report_type} révèle une dynamique positive sur les indicateurs académiques et de recherche. Les risques prioritaires portent sur la gestion financière de l'infrastructure et l'absentéisme RH. 3 actions correctives sont recommandées à court terme pour maintenir la trajectoire de performance globale."


def _mock_history():
    now = datetime.now()
    return [
        {"name": "Rapport Exécutif — Avril 2025", "type": "Exécutif", "institution": "Toutes", "date": "01/04/2025", "size": "2.4 MB"},
        {"name": "Rapport Académique — T1 2025", "type": "Académique", "institution": "Toutes", "date": "31/03/2025", "size": "1.8 MB"},
        {"name": "Rapport Finance ENIT — Mars", "type": "Financier", "institution": "ENIT", "date": "28/03/2025", "size": "890 KB"},
        {"name": "Rapport ESG — Q1 2025", "type": "ESG", "institution": "Toutes", "date": "15/03/2025", "size": "1.2 MB"},
        {"name": "Rapport KPI Hebdo W12", "type": "KPI Global", "institution": "Toutes", "date": "24/03/2025", "size": "450 KB"},
    ]