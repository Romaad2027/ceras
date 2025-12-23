import os
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID

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


def _load_events_df(
    engine: Engine,
    organization_id: UUID,
    days: Optional[int],
    cloud_account_id: Optional[UUID] = None,
) -> pd.DataFrame:
    """
    Load audit events for the specified organization, optional cloud account, and lookback window.

    Args:
        engine: SQLAlchemy engine
        organization_id: Filter events by this organization
        days: Lookback window in days (None = all history)
        cloud_account_id: Optional filter by specific cloud account

    Returns:
        DataFrame with columns: event_time, actor_identity, actor_ip_address, action_name
    """
    base_query = """
        SELECT
            event_time,
            actor_identity,
            actor_ip_address,
            action_name
        FROM audit_events
        WHERE organization_id = :org_id
    """
    params: Dict[str, Any] = {"org_id": str(organization_id)}

    if cloud_account_id:
        base_query += " AND cloud_account_id = :account_id"
        params["account_id"] = str(cloud_account_id)

    if days and days > 0:
        base_query += " AND event_time >= NOW() - INTERVAL :days_str"
        params["days_str"] = f"{int(days)} days"

    with engine.connect() as conn:
        df = pd.read_sql_query(text(base_query), conn, params=params)

    if "event_time" in df.columns and not pd.api.types.is_datetime64_any_dtype(
        df["event_time"]
    ):
        df["event_time"] = pd.to_datetime(df["event_time"], utc=True, errors="coerce")
    return df


def build_profiles(
    organization_id: UUID,
    threshold: float = THRESHOLD,
    days: int = DEFAULT_LOOKBACK_DAYS,
    cloud_account_id: Optional[UUID] = None,
) -> Dict[str, Dict[str, List[Any]]]:
    """
    Build statistically grounded behavior profiles per hybrid entity_id.

    Args:
        organization_id: Build profiles for this organization (required)
        threshold: Cumulative frequency threshold for pattern detection (default: 0.8)
        days: Lookback window in days (default: 30)
        cloud_account_id: Optional filter for specific cloud account

    Returns:
        Dictionary mapping entity_id -> {
            "common_hours": [int, ...],
            "common_ips": [str, ...],
            "common_actions": [str, ...],
        }

    Example:
        # Build profiles for all accounts in an organization
        profiles = build_profiles(org_id)

        # Build profiles for specific cloud account only
        profiles = build_profiles(org_id, cloud_account_id=account_id)

        # Custom threshold and lookback window
        profiles = build_profiles(org_id, threshold=0.9, days=14)
    """
    engine = _get_engine()
    df = _load_events_df(engine, organization_id, days, cloud_account_id)
    if df.empty:
        logger.warning(
            "No audit events found for organization_id=%s, cloud_account_id=%s",
            organization_id,
            cloud_account_id,
        )
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
                "organization_id": str(organization_id),
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

        logger.info(
            "Upserted %d entity profiles for organization_id=%s, cloud_account_id=%s",
            len(profiles),
            organization_id,
            cloud_account_id,
        )

    return profiles


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build entity behavioral profiles from audit events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build profiles for an organization (last 30 days)
  python -m risk_analysis_service.ml_engine.build_profiles --org-id abc123...

  # Build profiles for specific cloud account only
  python -m risk_analysis_service.ml_engine.build_profiles \\
      --org-id abc123... --account-id def456...

  # Custom threshold and lookback window
  python -m risk_analysis_service.ml_engine.build_profiles \\
      --org-id abc123... --threshold 0.9 --days 14
        """,
    )

    parser.add_argument(
        "--org-id",
        "--organization-id",
        dest="organization_id",
        required=True,
        help="Organization ID (UUID) to build profiles for",
    )
    parser.add_argument(
        "--account-id",
        "--cloud-account-id",
        dest="cloud_account_id",
        default=None,
        help="Optional: Cloud account ID (UUID) to filter by",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=THRESHOLD,
        help=f"Cumulative frequency threshold (default: {THRESHOLD})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_LOOKBACK_DAYS,
        help=f"Lookback window in days (default: {DEFAULT_LOOKBACK_DAYS})",
    )

    args = parser.parse_args()

    # Validate and parse UUIDs
    try:
        org_id = UUID(args.organization_id)
        account_id = UUID(args.cloud_account_id) if args.cloud_account_id else None
    except ValueError as e:
        print(f"Error: Invalid UUID format - {e}")
        exit(1)

    # Validate threshold
    if args.threshold <= 0 or args.threshold > 1:
        print("Error: threshold must be between 0 and 1")
        exit(1)

    # Validate days
    if args.days < 1:
        print("Error: days must be at least 1")
        exit(1)

    # Build profiles
    print(f"Building profiles for organization: {org_id}")
    if account_id:
        print(f"  Cloud account filter: {account_id}")
    print(f"  Lookback window: {args.days} days")
    print(f"  Threshold: {args.threshold}")
    print()

    profiles_dict = build_profiles(
        organization_id=org_id,
        threshold=args.threshold,
        days=args.days,
        cloud_account_id=account_id,
    )
    print(f"\n✅ Built {len(profiles_dict)} profiles and upserted into DB")
