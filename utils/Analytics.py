"""
utils/analytics.py — Délègue tout à utils/db.py. Aucune donnée mock.

Si tu vois ce fichier importé quelque part, c'est lui qui causait les fausses données.
"""
from utils.db import fetch_dataframe, get_all_institutions_summary


def get_historical_trend(institution: str, metric: str) -> list:
    """
    Retourne les valeurs historiques réelles depuis Supabase pour une institution/métrique.
    Remplace l'ancienne version qui générait des données aléatoires avec numpy.
    """
    df = fetch_dataframe(institution=institution if institution != "Toutes (Agrégé)" else None)
    if df.empty or metric not in df.columns or "year" not in df.columns:
        return []
    import pandas as pd
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df[metric] = pd.to_numeric(df[metric], errors="coerce")
    series = df.dropna(subset=["year", metric]).groupby("year")[metric].mean().sort_index()
    return [round(float(v), 1) for v in series.values]