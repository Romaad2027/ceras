import os
import logging
from typing import Dict, List, Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text, func
from sqlalchemy.engine import Engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from ..db.models.entity_profile import EntityProfile


logger = logging.getLogger("risk_analysis.ml_engine")


THRESHOLD: float = 0.8
DEFAULT_LOOKBACK_DAYS: int = 30


def _get_engine() -> Engine:
    """
    Prefer DATABASE_URL from environment; fall back to the service's engine if not set.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)
                                                                           
    from ..db.session import engine as app_engine                

    return app_engine


def _cumulative_top(values: pd.Series, threshold: float) -> List[Any]:
    """
    Return the smallest set of top values whose cumulative normalized frequency
    reaches or exceeds the threshold.
    """
    if values.empty:
        return []
    counts = (
        values.dropna()
        .astype(str)
        .replace({"": pd.NA})
        .dropna()
        .value_counts(normalize=True, dropna=True)
        .sort_values(ascending=False)
    )
    if counts.empty:
        return []
    csum = counts.cumsum()
                                                                                             
    cutoff_idx = (csum >= threshold).idxmax()
                                          
    upto = list(counts.index[: counts.index.get_loc(cutoff_idx) + 1])
    return upto


def _compute_entity_id(df: pd.DataFrame) -> pd.Series:
    """
    Hybrid Identity:
    - Prefer actor_identity if present and non-empty
    - Otherwise fall back to actor_ip_address
    - Rows where both are missing/empty will produce NA and can be dropped for grouping
    """
    actor_identity = (
        df.get("actor_identity").astype("string").str.strip().replace({"": pd.NA})
    )
    actor_ip = (
        df.get("actor_ip_address").astype("string").str.strip().replace({"": pd.NA})
    )
    return actor_identity.fillna(actor_ip)


def _load_events_df(engine: Engine, days: Optional[int]) -> pd.DataFrame:
    """
    Load audit events for the specified lookback window.
    """
    base_query = """
        SELECT
            event_time,
            actor_identity,
            actor_ip_address,
            action_name
        FROM audit_events
    """
    params: Dict[str, Any] = {}
    if days and days > 0:
        query = base_query + " WHERE event_time >= NOW() - INTERVAL :days_str"
                                                            
        params["days_str"] = f"{int(days)} days"
    else:
        query = base_query

    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)
                           
    if "event_time" in df.columns and not pd.api.types.is_datetime64_any_dtype(
        df["event_time"]
    ):
        df["event_time"] = pd.to_datetime(df["event_time"], utc=True, errors="coerce")
    return df


def build_profiles(
    threshold: float = THRESHOLD, days: int = DEFAULT_LOOKBACK_DAYS
) -> Dict[str, Dict[str, List[Any]]]:
    """
    Build statistically grounded behavior profiles per hybrid entity_id.

    Returns a dictionary mapping:
      entity_id -> {
        "common_hours": [int, ...],
        "common_ips": [str, ...],
        "common_actions": [str, ...],
      }
    """
    engine = _get_engine()
    df = _load_events_df(engine, days=days)
    if df.empty:
        return {}

                     
    df["entity_id"] = _compute_entity_id(df)
    df = df.dropna(subset=["entity_id"])

                                            
    if "event_time" in df.columns:
                                                      
        df["event_time"] = pd.to_datetime(df["event_time"], utc=True, errors="coerce")
        df["hour"] = df["event_time"].dt.hour
    else:
        df["hour"] = pd.NA

    profiles: Dict[str, Dict[str, List[Any]]] = {}
    for entity_id, g in df.groupby("entity_id", dropna=True):
        try:
            common_hours_idx = _cumulative_top(g["hour"], threshold)
            common_ips_idx = _cumulative_top(g["actor_ip_address"], threshold)
            common_actions_idx = _cumulative_top(g["action_name"], threshold)

                                                    
            common_hours: List[int] = [int(h) for h in common_hours_idx if pd.notna(h)]
            common_ips: List[str] = [str(ip) for ip in common_ips_idx]
            common_actions: List[str] = [str(a) for a in common_actions_idx]

            profiles[str(entity_id)] = {
                "common_hours": common_hours,
                "common_ips": common_ips,
                "common_actions": common_actions,
            }
        except Exception as exc:
            logger.exception(
                "Failed to build profile for entity_id=%s: %s", entity_id, exc
            )
            continue

                                                  
    if profiles:
        rows = [
            {
                "entity_id": eid,
                                                                         
                "auto_common_hours": prof.get("common_hours", []),
                "auto_common_ips": prof.get("common_ips", []),
                "auto_common_actions": prof.get("common_actions", []),
            }
            for eid, prof in profiles.items()
        ]
        table = EntityProfile.__table__
        insert_stmt = pg_insert(table).values(rows)
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[table.c.entity_id],
            set_={
                "auto_common_hours": insert_stmt.excluded.auto_common_hours,
                "auto_common_ips": insert_stmt.excluded.auto_common_ips,
                "auto_common_actions": insert_stmt.excluded.auto_common_actions,
                "updated_at": func.now(),
            },
        )
        with engine.begin() as conn:
            conn.execute(upsert_stmt)

    return profiles


if __name__ == "__main__":
    profiles_dict = build_profiles()
    print(f"Built {len(profiles_dict)} profiles and upserted into DB")
