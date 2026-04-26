"""
utils/reports.py — Report generation from real DB data.
"""
import io
from datetime import datetime
import pandas as pd
from utils.db import fetch_dataframe, get_all_institutions_summary
 
 
def generate_report(report_type: str, institution: str, period: str,
                    include_charts: bool = True, include_ai: bool = True) -> str:
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    header = (
        f"RAPPORT UCAR — {report_type.upper().replace('_', ' ')}\n"
        f"Périmètre   : {institution}\n"
        f"Période     : {period}\n"
        f"Généré le   : {now}\n"
        f"{'=' * 60}\n\n"
    )
 
    inst = None if "Toutes" in institution or "Consolidé" in institution else institution
    df = fetch_dataframe(institution=inst)
 
    if df.empty:
        return header + "⚠ Aucune donnée disponible pour ce périmètre.\nImportez des données via 'Import de Données'."
 
    body_fn = {
        "monthly_executive": _section_executive,
        "academic":          _section_academic,
        "financial":         _section_financial,
        "esg":               _section_esg,
        "hr":                _section_hr,
        "research":          _section_research,
        "infrastructure":    _section_infrastructure,
        "kpi_global":        _section_kpi_global,
    }.get(report_type, _section_kpi_global)
 
    return header + body_fn(df)
 
 
def _val(df, col, agg="mean", fmt=".1f"):
    if col not in df.columns:
        return "N/A"
    v = pd.to_numeric(df[col], errors="coerce").dropna()
    if v.empty:
        return "N/A"
    result = v.mean() if agg == "mean" else v.sum()
    return f"{result:{fmt}}"
 
 
def _section_executive(df):
    insts = df["institution"].nunique() if "institution" in df.columns else "N/A"
    return (
        "1. SYNTHÈSE EXÉCUTIVE\n"
        f"{'─' * 57}\n"
        f"Institutions couvertes : {insts}\n"
        f"Taux de réussite moyen : {_val(df,'success_rate')}%\n"
        f"Exécution budgétaire   : {_val(df,'budget_execution_rate')}%\n"
        f"Effectifs totaux       : {_val(df,'total_students',agg='sum',fmt='.0f')}\n"
        f"Publications           : {_val(df,'publications',agg='sum',fmt='.0f')}\n\n"
        "2. KPIs PAR DOMAINE\n"
        f"{'─' * 57}\n"
        f"Académique  : réussite {_val(df,'success_rate')}% | abandon {_val(df,'dropout_rate')}%\n"
        f"Finance     : exécution {_val(df,'budget_execution_rate')}%\n"
        f"RH          : absentéisme {_val(df,'absenteeism_rate')}%\n"
        f"Recherche   : {_val(df,'publications',agg='sum',fmt='.0f')} publications | {_val(df,'projects',agg='sum',fmt='.0f')} projets\n"
        f"ESG         : {_val(df,'carbon_footprint',agg='sum',fmt='.0f')} T CO₂\n\n"
        "3. RECOMMANDATIONS\n"
        f"{'─' * 57}\n"
        "→ Analyser les institutions dont le taux de réussite est < 70%\n"
        "→ Réviser les enveloppes budgétaires sous-consommées\n"
        "→ Renforcer le suivi RH dans les établissements à fort absentéisme\n"
    )
 
 
def _section_academic(df):
    return (
        "RAPPORT ACADÉMIQUE\n"
        f"{'─' * 57}\n"
        f"Taux de réussite moyen    : {_val(df,'success_rate')}%\n"
        f"Taux d'abandon moyen      : {_val(df,'dropout_rate')}%\n"
        f"Taux d'assiduité moyen    : {_val(df,'attendance_rate')}%\n"
        f"Taux de répétition moyen  : {_val(df,'repetition_rate')}%\n"
        f"Total étudiants           : {_val(df,'total_students',agg='sum',fmt='.0f')}\n"
        f"Étudiants admis (total)   : {_val(df,'passed_students',agg='sum',fmt='.0f')}\n\n"
        "PAR INSTITUTION:\n"
        + _per_institution_table(df, ["success_rate", "dropout_rate", "attendance_rate"])
    )
 
 
def _section_financial(df):
    return (
        "RAPPORT FINANCIER\n"
        f"{'─' * 57}\n"
        f"Budget alloué total    : {_val(df,'budget_allocated',agg='sum',fmt='.0f')} DT\n"
        f"Budget consommé total  : {_val(df,'budget_used',agg='sum',fmt='.0f')} DT\n"
        f"Taux d'exécution moyen : {_val(df,'budget_execution_rate')}%\n"
        f"Coût moyen/étudiant    : {_val(df,'cost_per_student')} DT\n\n"
        "PAR INSTITUTION:\n"
        + _per_institution_table(df, ["budget_allocated", "budget_used", "budget_execution_rate"])
    )
 
 
def _section_esg(df):
    return (
        "RAPPORT ESG / ENVIRONNEMENT\n"
        f"{'─' * 57}\n"
        f"Empreinte carbone totale  : {_val(df,'carbon_footprint',agg='sum',fmt='.0f')} T CO₂\n"
        f"Consommation énergie moy. : {_val(df,'energy_consumption')} kWh\n"
        f"Taux de recyclage moyen   : {_val(df,'recycling_rate')}%\n\n"
        "PAR INSTITUTION:\n"
        + _per_institution_table(df, ["carbon_footprint", "energy_consumption", "recycling_rate"])
    )
 
 
def _section_hr(df):
    return (
        "RAPPORT RESSOURCES HUMAINES\n"
        f"{'─' * 57}\n"
        f"Effectif total (personnel) : {_val(df,'staff_count',agg='sum',fmt='.0f')}\n"
        f"Taux d'absentéisme moyen   : {_val(df,'absenteeism_rate')}%\n"
        f"Charge d'enseignement moy. : {_val(df,'teaching_load')}\n\n"
        "PAR INSTITUTION:\n"
        + _per_institution_table(df, ["staff_count", "absenteeism_rate"])
    )
 
 
def _section_research(df):
    return (
        "RAPPORT RECHERCHE & INNOVATION\n"
        f"{'─' * 57}\n"
        f"Publications totales : {_val(df,'publications',agg='sum',fmt='.0f')}\n"
        f"Projets actifs total : {_val(df,'projects',agg='sum',fmt='.0f')}\n"
        f"Financement obtenu   : {_val(df,'funding',agg='sum',fmt='.0f')} DT\n\n"
        "PAR INSTITUTION:\n"
        + _per_institution_table(df, ["publications", "projects", "funding"])
    )
 
 
def _section_infrastructure(df):
    return (
        "RAPPORT INFRASTRUCTURE & ÉQUIPEMENTS\n"
        f"{'─' * 57}\n"
        f"Taux d'occupation salles (moy.) : {_val(df,'occupancy_rate')}%\n"
        f"Nombre de salles (total)        : {_val(df,'classrooms',agg='sum',fmt='.0f')}\n\n"
        "PAR INSTITUTION:\n"
        + _per_institution_table(df, ["classrooms", "occupancy_rate"])
    )
 
 
def _section_kpi_global(df):
    return (
        "TABLEAU DE BORD KPI GLOBAL — UCAR\n"
        f"{'─' * 57}\n"
        f"ACADÉMIQUE\n"
        f"  Réussite     : {_val(df,'success_rate')}%\n"
        f"  Abandon      : {_val(df,'dropout_rate')}%\n"
        f"  Assiduité    : {_val(df,'attendance_rate')}%\n\n"
        f"FINANCE\n"
        f"  Exécution    : {_val(df,'budget_execution_rate')}%\n"
        f"  Budget alloué: {_val(df,'budget_allocated',agg='sum',fmt='.0f')} DT\n\n"
        f"RESSOURCES HUMAINES\n"
        f"  Effectif     : {_val(df,'staff_count',agg='sum',fmt='.0f')}\n"
        f"  Absentéisme  : {_val(df,'absenteeism_rate')}%\n\n"
        f"RECHERCHE\n"
        f"  Publications : {_val(df,'publications',agg='sum',fmt='.0f')}\n"
        f"  Projets      : {_val(df,'projects',agg='sum',fmt='.0f')}\n\n"
        f"ESG\n"
        f"  CO₂          : {_val(df,'carbon_footprint',agg='sum',fmt='.0f')} T\n"
        f"  Recyclage    : {_val(df,'recycling_rate')}%\n\n"
        f"INFRASTRUCTURE\n"
        f"  Occupation   : {_val(df,'occupancy_rate')}%\n"
        f"  Salles       : {_val(df,'classrooms',agg='sum',fmt='.0f')}\n"
    )
 
 
def _per_institution_table(df, cols) -> str:
    if "institution" not in df.columns:
        return ""
    agg_dict = {c: "mean" for c in cols if c in df.columns}
    if not agg_dict:
        return ""
    tbl = df.groupby("institution").agg(agg_dict).round(1).reset_index()
    lines = []
    for _, row in tbl.iterrows():
        parts = [f"{row['institution']}"]
        for c in cols:
            if c in tbl.columns:
                parts.append(f"{c.replace('_', ' ')}: {row[c]}")
        lines.append("  " + " | ".join(parts))
    return "\n".join(lines) + "\n"
 
 
def get_report_history() -> list:
    return []   # Real history would be stored in a reports table in Supabase
 
 
def export_to_pdf(content: str, title: str) -> bytes:
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)
        pdf.set_title(title)
        for line in content.split("\n"):
            safe = line.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 6, safe)
        return pdf.output()
    except ImportError:
        return content.encode("utf-8")
 
 
def export_to_excel(report_type: str, institution: str) -> bytes:
    output = io.BytesIO()
    inst = None if "Toutes" in institution or "Consolidé" in institution else institution
    df = fetch_dataframe(institution=inst)
    summary = get_all_institutions_summary()
 
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not df.empty:
            df.to_excel(writer, sheet_name="Données Brutes", index=False)
        if not summary.empty:
            summary.to_excel(writer, sheet_name="KPI Global", index=False)
        meta = pd.DataFrame([{
            "Rapport": report_type, "Institution": institution,
            "Date": datetime.now().strftime("%d/%m/%Y"),
        }])
        meta.to_excel(writer, sheet_name="Metadata", index=False)
 
    return output.getvalue()
 