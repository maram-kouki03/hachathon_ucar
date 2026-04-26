"""
utils/db.py
Supabase connection and all data access helpers.
"""
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ── Constants ──────────────────────────────────────────────────────────────────
PCT_COLS = [
    "success_rate", "dropout_rate", "attendance_rate", "repetition_rate",
    "budget_execution_rate", "absenteeism_rate", "occupancy_rate",
    "recycling_rate", "employability_rate", "national_partnership_rate",
    "international_partnership_rate",
]

# ── Type helpers ───────────────────────────────────────────────────────────────
def to_int(value):
    try:
        return int(float(value))
    except Exception:
        return None

def to_float(value):
    try:
        return float(value)
    except Exception:
        return None

def normalize_scalar_pct(value):
    """
    Normalize a single percentage value for storage.
    - If value > 100: divide by 100 (e.g. 2404 → 24.04)
    - If 0 <= value <= 100: keep as-is (e.g. 75 → 75)
    - If 0 < value < 1: multiply by 100 (e.g. 0.75 → 75)
    """
    try:
        v = float(value)
        if v > 100:
            return round(v / 100, 4)
        if 0 < v < 1:
            return round(v * 100, 4)
        return v
    except Exception:
        return None

def _normalize_pct_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize percentage columns in a DataFrame after fetching from DB.
    Fixes row-by-row: if value > 100, divide by 100.
    """
    for col in PCT_COLS:
        if col not in df.columns:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].apply(
            lambda v: round(v / 100, 4) if pd.notna(v) and v > 100 else v
        )
    return df

# ── Core fetch ─────────────────────────────────────────────────────────────────
def fetch_dataframe(institution: str = None, year: int = None) -> pd.DataFrame:
    """Fetch all rows from institutions_data, optionally filtered."""
    query = supabase.table("institutions_data").select("*")
    if institution and institution not in ("All", "Toutes les institutions (Consolidé)", "Toutes"):
        query = query.eq("institution", institution)
    if year:
        query = query.eq("year", year)
    res = query.execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df = _normalize_pct_df(df)  # fix any bad values from DB
    return df

def get_institutions() -> list:
    df = fetch_dataframe()
    if df.empty or "institution" not in df.columns:
        return []
    return sorted(df["institution"].dropna().unique().tolist())

def get_years() -> list:
    df = fetch_dataframe()
    if df.empty or "year" not in df.columns:
        return []
    return sorted(df["year"].dropna().unique().tolist(), reverse=True)

# ── Insert ─────────────────────────────────────────────────────────────────────
def insert_data(data: dict):
    try:
        m   = data.get("metadata", {})
        a   = data.get("academic", {})
        emp = data.get("employment", {})
        f   = data.get("finance", {})
        h   = data.get("hr", {})
        e   = data.get("esg", {})
        r   = data.get("research", {})
        i   = data.get("infrastructure", {})
        p   = data.get("partnerships", {})

        record = {
            "institution":                    m.get("institution"),
            "department":                     m.get("department"),
            "year":                           to_int(m.get("year")),
            "document_type":                  m.get("document_type"),

            "total_students":                 to_int(a.get("total_students")),
            "passed_students":                to_int(a.get("passed_students")),
            "failed_students":                to_int(a.get("failed_students")),
            "attendance_rate":                normalize_scalar_pct(a.get("attendance_rate")),
            "success_rate":                   normalize_scalar_pct(a.get("success_rate")),
            "dropout_rate":                   normalize_scalar_pct(a.get("dropout_rate")),
            "repetition_rate":                normalize_scalar_pct(a.get("repetition_rate")),

            "employability_rate":             normalize_scalar_pct(emp.get("employability_rate")),
            "time_to_employment":             to_float(emp.get("time_to_employment")),
            "national_partnership_rate":      to_float(emp.get("national_partnership_rate")),
            "international_partnership_rate": to_float(emp.get("international_partnership_rate")),

            "budget_allocated":               to_float(f.get("budget_allocated")),
            "budget_used":                    to_float(f.get("budget_used")),
            "cost_per_student":               to_float(f.get("cost_per_student")),
            "budget_execution_rate":          normalize_scalar_pct(f.get("budget_execution_rate")),

            "staff_count":                    to_int(h.get("staff_count")),
            "absenteeism_rate":               normalize_scalar_pct(h.get("absenteeism_rate")),
            "teaching_load":                  to_float(h.get("teaching_load")),

            "energy_consumption":             to_float(e.get("energy_consumption")),
            "carbon_footprint":               to_float(e.get("carbon_footprint")),
            "recycling_rate":                 to_float(e.get("recycling_rate")),

            "publications":                   to_int(r.get("publications")),
            "projects":                       to_int(r.get("projects")),

            "classrooms":                     to_int(i.get("classrooms")),
            "occupancy_rate":                 normalize_scalar_pct(i.get("occupancy_rate")),

            "agreements":                     to_int(p.get("agreements")),
            "student_mobility_in":            to_int(p.get("student_mobility_in")),
            "student_mobility_out":           to_int(p.get("student_mobility_out")),

            "data": data,
        }

        record = {k: v for k, v in record.items() if v is not None}
        result = supabase.table("institutions_data").insert(record).execute()

        if not result or not result.data:
            return None
        return result

    except Exception as ex:
        import traceback
        traceback.print_exc()
        raise ex

# ── Global KPIs ────────────────────────────────────────────────────────────────
def get_global_kpis() -> dict:
    df = fetch_dataframe()
    if df.empty:
        return {}

    def _pct(col):
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        return round(vals.mean(), 1) if not vals.empty else None

    def _sum(col):
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        return int(vals.sum()) if not vals.empty else None

    success  = _pct("success_rate")
    budget   = _pct("budget_execution_rate")
    students = _sum("total_students")
    pubs     = _sum("publications")
    carbon   = _sum("carbon_footprint")
    insts    = df["institution"].nunique() if "institution" in df.columns else 0

    return {
        "success_rate":        {"value": f"{success}%" if success else "N/A",   "delta": "", "positive": True, "bar": int(success or 0)},
        "budget_execution":    {"value": f"{budget}%"  if budget  else "N/A",   "delta": "", "positive": True, "bar": int(budget or 0)},
        "active_institutions": {"value": str(insts),                             "delta": "", "positive": True, "bar": 100},
        "total_students":      {"value": f"{students:,}" if students else "N/A", "delta": "", "positive": True, "bar": 70},
        "research_projects":   {"value": str(pubs or "N/A"),                     "delta": "", "positive": True, "bar": 65},
        "carbon_footprint":    {"value": f"{carbon} T" if carbon else "N/A",     "delta": "", "positive": True, "bar": 40},
    }

# ── Institution Summary ────────────────────────────────────────────────────────
def get_all_institutions_summary() -> pd.DataFrame:
    df = fetch_dataframe()
    if df.empty:
        return pd.DataFrame()

    num_cols = [
        "total_students", "success_rate", "budget_execution_rate",
        "publications", "carbon_footprint", "absenteeism_rate",
        "dropout_rate", "attendance_rate",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    agg = {c: ("sum" if c == "total_students" else "mean") for c in num_cols if c in df.columns}

    if "institution" not in df.columns:
        return pd.DataFrame()

    summary = df.groupby("institution").agg(agg).reset_index().round(1)

    rename = {
        "institution": "Institution",
        "total_students": "Étudiants",
        "success_rate": "Réussite %",
        "budget_execution_rate": "Budget Exec %",
        "publications": "Publications",
        "carbon_footprint": "CO₂ (T)",
        "absenteeism_rate": "Absentéisme %",
        "dropout_rate": "Abandon %",
    }
    summary.rename(columns={k: v for k, v in rename.items() if k in summary.columns}, inplace=True)

    score_cols = [summary[c] for c in ["Réussite %", "Budget Exec %"] if c in summary.columns]
    if score_cols:
        summary["Score Global"] = round(sum(score_cols) / len(score_cols), 1)

    return summary

# ── Institution Detail ─────────────────────────────────────────────────────────
def get_institution_detail(institution: str) -> dict:
    df = fetch_dataframe(institution=institution)
    if df.empty:
        return {}

    if "year" in df.columns:
        df = df.sort_values("year", ascending=False)
    row = df.iloc[0].to_dict()

    def _v(col):
        v = row.get(col)
        return v if v is not None else "N/A"

    def _fmt(col, suffix=""):
        v = _v(col)
        if v == "N/A":
            return "N/A"
        try:
            return f"{float(v):.1f}{suffix}"
        except Exception:
            return str(v)

    return {
        "info": {
            "city":    row.get("city", "Tunis"),
            "type":    row.get("document_type", "Institution"),
            "founded": row.get("year", ""),
        },
        "kpis": {
            "students":         _fmt("total_students"),
            "success_rate":     _fmt("success_rate", "%"),
            "success_rate_num": to_float(row.get("success_rate")) or 0,
            "budget_exec":      _fmt("budget_execution_rate", "%"),
            "teachers":         str(_v("staff_count")),
            "publications":     str(_v("publications")),
            "co2":              str(_v("carbon_footprint")),
        },
        "raw": row,
        "all_rows": df,
    }

# ── Alerts ────────────────────────────────────────────────────────────────────
def get_alerts_from_db(thresholds: dict = None) -> list:
    thresholds = thresholds or {
        "success_rate_min": 70,
        "budget_exec_min": 70,
        "absenteeism_max": 12,
        "dropout_max": 10,
        "carbon_max": 300,
    }

    df = fetch_dataframe()
    if df.empty:
        return []

    alerts = []
    num_cols = ["success_rate", "budget_execution_rate", "absenteeism_rate",
                "dropout_rate", "carbon_footprint", "occupancy_rate"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    for _, row in df.iterrows():
        inst = row.get("institution", "?")
        year = row.get("year", "")

        sr = row.get("success_rate")
        if pd.notna(sr) and sr < thresholds["success_rate_min"]:
            alerts.append({"level": "critical" if sr < thresholds["success_rate_min"] - 10 else "warning",
                           "message": f"Taux de réussite {sr:.1f}% — sous le seuil ({thresholds['success_rate_min']}%)",
                           "institution": inst, "domain": "Académique", "timestamp": str(year)})

        be = row.get("budget_execution_rate")
        if pd.notna(be) and be < thresholds["budget_exec_min"]:
            alerts.append({"level": "warning",
                           "message": f"Exécution budgétaire {be:.1f}% — sous le seuil ({thresholds['budget_exec_min']}%)",
                           "institution": inst, "domain": "Finance", "timestamp": str(year)})

        ab = row.get("absenteeism_rate")
        if pd.notna(ab) and ab > thresholds["absenteeism_max"]:
            alerts.append({"level": "critical" if ab > thresholds["absenteeism_max"] + 5 else "warning",
                           "message": f"Absentéisme RH {ab:.1f}% — dépasse le seuil ({thresholds['absenteeism_max']}%)",
                           "institution": inst, "domain": "RH", "timestamp": str(year)})

        dr = row.get("dropout_rate")
        if pd.notna(dr) and dr > thresholds["dropout_max"]:
            alerts.append({"level": "critical" if dr > thresholds["dropout_max"] + 5 else "warning",
                           "message": f"Taux d'abandon {dr:.1f}% — dépasse le seuil ({thresholds['dropout_max']}%)",
                           "institution": inst, "domain": "Académique", "timestamp": str(year)})

        co2 = row.get("carbon_footprint")
        if pd.notna(co2) and co2 > thresholds["carbon_max"]:
            alerts.append({"level": "warning",
                           "message": f"Empreinte carbone {co2:.0f} T — dépasse le seuil ({thresholds['carbon_max']} T)",
                           "institution": inst, "domain": "ESG", "timestamp": str(year)})

    return alerts