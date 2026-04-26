

"""
utils/aggregator.py
All aggregation logic — delegates to utils/db.py for real data.
"""
from utils.db import (
    get_global_kpis,
    get_all_institutions_summary,
    get_institution_detail,
    fetch_dataframe,
)
 
__all__ = [
    "get_global_kpis",
    "get_all_institutions_summary",
    "get_institution_detail",
    "fetch_dataframe",
]