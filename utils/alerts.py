"""
utils/alerts.py — Generates alerts from real DB data.
"""
from utils.db import get_alerts_from_db, fetch_dataframe
 
_THRESHOLDS = {
    "success_rate_min": 70,
    "budget_exec_min": 70,
    "absenteeism_max": 12,
    "dropout_max": 10,
    "carbon_max": 300,
}
 
 
def get_all_alerts(limit: int = 50, thresholds: dict = None) -> list:
    th = thresholds or _THRESHOLDS
    alerts = get_alerts_from_db(th)
    return alerts[:limit]
 
 
def get_critical_alerts(limit: int = 6) -> list:
    alerts = get_all_alerts()
    return [a for a in alerts if a["level"] in ("critical", "warning")][:limit]
 
 
def get_alert_stats(thresholds: dict = None) -> dict:
    alerts = get_all_alerts(thresholds=thresholds)
    return {
        "critical": sum(1 for a in alerts if a["level"] == "critical"),
        "warning":  sum(1 for a in alerts if a["level"] == "warning"),
        "info":     sum(1 for a in alerts if a["level"] == "info"),
        "resolved_today": 0,
    }
 
 
def mark_alert_resolved(alert_id: str) -> bool:
    return True
 
 
def update_thresholds(new_thresholds: dict):
    """Update module-level thresholds (runtime only)."""
    global _THRESHOLDS
    _THRESHOLDS.update(new_thresholds)