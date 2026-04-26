"""
utils/predictor.py — Statistical trend prediction on real DB data.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from utils.db import fetch_dataframe
 
 
def predict_kpi_trend(institution: str, metric: str, n_future: int = 6) -> dict:
    """
    Fit a linear trend to historical DB data and forecast forward.
    Falls back to a flat line if insufficient data points exist.
    """
    df = fetch_dataframe(institution=institution if institution != "Toutes (Agrégé)" else None)
 
    unit = "%" if metric in ("success_rate", "budget_execution_rate", "absenteeism_rate", "dropout_rate") else ""
 
    if df.empty or metric not in df.columns or "year" not in df.columns:
        return _empty_prediction(metric, n_future, unit)
 
    df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    series = df.dropna(subset=[metric, "year"]).groupby("year")[metric].mean().sort_index()
 
    if len(series) < 2:
        # Only one data point — flat forecast
        last_val = float(series.iloc[-1]) if not series.empty else 0.0
        historical = [last_val]
        hist_labels = [str(series.index[-1])]
        forecast = [round(last_val, 1)] * n_future
        upper = [round(last_val + 5, 1)] * n_future
        lower = [round(max(0, last_val - 5), 1)] * n_future
        now = datetime.now()
        fut_labels = [(now + timedelta(days=30 * (i + 1))).strftime("%b %Y") for i in range(n_future)]
        return _build_result(historical, hist_labels, forecast, upper, lower, fut_labels, last_val, unit, trend=0)
 
    x = np.array(series.index, dtype=float)
    y = np.array(series.values, dtype=float)
 
    # Linear regression
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs
 
    historical = [round(float(v), 1) for v in y]
    hist_labels = [str(int(yr)) for yr in series.index]
 
    last_x = x[-1]
    x_future = [last_x + (i + 1) / 4 for i in range(n_future)]   # quarterly steps
    forecast = [round(float(np.polyval(coeffs, xf)), 1) for xf in x_future]
 
    residuals = y - np.polyval(coeffs, x)
    std_err = float(np.std(residuals)) if len(residuals) > 1 else float(abs(slope))
    ci = std_err * 2.0
    upper = [round(f + ci * (1 + i * 0.05), 1) for i, f in enumerate(forecast)]
    lower = [round(max(0, f - ci * (1 + i * 0.05)), 1) for i, f in enumerate(forecast)]
 
    now = datetime.now()
    fut_labels = [(now + timedelta(days=30 * (i + 1))).strftime("%b %Y") for i in range(n_future)]
 
    return _build_result(historical, hist_labels, forecast, upper, lower, fut_labels, y[-1], unit, slope)
 
 
def _build_result(hist, hist_labels, forecast, upper, lower, fut_labels, last_val, unit, trend) -> dict:
    confidence = min(95, max(60, int(85 - abs(trend) * 2)))
    return {
        "historical": hist,
        "forecast": forecast,
        "upper_bound": upper,
        "lower_bound": lower,
        "historical_labels": hist_labels,
        "future_labels": fut_labels,
        "current_value": f"{round(last_val, 1)}{unit}",
        "pred_short": f"{forecast[2]}{unit}" if len(forecast) > 2 else f"{forecast[-1]}{unit}",
        "pred_target": f"{forecast[-1]}{unit}",
        "trend": "↗ Hausse" if trend > 0 else "↘ Baisse" if trend < 0 else "→ Stable",
        "trend_strength": f"{'Modérée' if abs(trend) < 0.5 else 'Forte'} ({trend:+.3f}/an)",
        "confidence": confidence,
    }
 
 
def _empty_prediction(metric, n_future, unit) -> dict:
    now = datetime.now()
    fut_labels = [(now + timedelta(days=30 * (i + 1))).strftime("%b %Y") for i in range(n_future)]
    return {
        "historical": [], "forecast": [], "upper_bound": [], "lower_bound": [],
        "historical_labels": [], "future_labels": fut_labels,
        "current_value": "N/A", "pred_short": "N/A", "pred_target": "N/A",
        "trend": "→ Données insuffisantes", "trend_strength": "—", "confidence": 0,
    }
 
 
def get_risk_matrix(institution: str) -> list:
    """Generate risk items based on real DB thresholds."""
    from utils.db import fetch_dataframe
    df = fetch_dataframe(institution=institution if institution != "Toutes (Agrégé)" else None)
 
    risks = []
    if df.empty:
        return [{"level": "info", "title": "Données insuffisantes",
                 "description": "Importez des données pour générer la matrice de risques."}]
 
    def _mean(col):
        if col not in df.columns:
            return None
        v = pd.to_numeric(df[col], errors="coerce").dropna()
        return round(float(v.mean()), 1) if not v.empty else None
 
    ab = _mean("absenteeism_rate")
    if ab is not None:
        risks.append({
            "level": "high" if ab > 15 else "med" if ab > 10 else "low",
            "title": "Absentéisme RH",
            "description": f"Taux actuel: {ab}% — {'⚠ Critique' if ab > 15 else 'À surveiller' if ab > 10 else '✓ Normal'}",
        })
 
    sr = _mean("success_rate")
    if sr is not None:
        risks.append({
            "level": "high" if sr < 65 else "med" if sr < 75 else "low",
            "title": "Taux de réussite",
            "description": f"Moyenne: {sr}% — {'⚠ Critique' if sr < 65 else 'Attention' if sr < 75 else '✓ Satisfaisant'}",
        })
 
    be = _mean("budget_execution_rate")
    if be is not None:
        risks.append({
            "level": "high" if be < 65 else "med" if be < 80 else "low",
            "title": "Exécution budgétaire",
            "description": f"Taux: {be}% — {'⚠ Sous-consommation critique' if be < 65 else 'À améliorer' if be < 80 else '✓ Bon niveau'}",
        })
 
    co2 = _mean("carbon_footprint")
    if co2 is not None:
        risks.append({
            "level": "high" if co2 > 400 else "med" if co2 > 250 else "low",
            "title": "Empreinte carbone",
            "description": f"Valeur: {co2} T CO₂ — {'⚠ Très élevée' if co2 > 400 else 'Modérée' if co2 > 250 else '✓ Maîtrisée'}",
        })
 
    dr = _mean("dropout_rate")
    if dr is not None:
        risks.append({
            "level": "high" if dr > 15 else "med" if dr > 8 else "low",
            "title": "Taux d'abandon",
            "description": f"Taux: {dr}% — {'⚠ Élevé' if dr > 15 else 'À surveiller' if dr > 8 else '✓ Sous contrôle'}",
        })
 
    pubs = _mean("publications")
    if pubs is not None:
        risks.append({
            "level": "low" if pubs > 20 else "med" if pubs > 8 else "high",
            "title": "Publications R&D",
            "description": f"Moyenne: {pubs} publications — {'✓ Bonne production' if pubs > 20 else 'Moyen' if pubs > 8 else '⚠ Insuffisant'}",
        })
 
    if not risks:
        risks.append({"level": "info", "title": "Analyse disponible",
                      "description": "Données chargées — indicateurs dans les normes."})
 
    return sorted(risks, key=lambda r: {"high": 0, "med": 1, "low": 2, "info": 3}.get(r["level"], 3))
 