from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib


def _default_training_csv_path() -> Path:
    """
    Resolve a sensible default path to training_data.csv.
    Prefer current working directory; fallback to project root relative to this file.
    """
    cwd_candidate = Path.cwd() / "training_data.csv"
    if cwd_candidate.exists():
        return cwd_candidate.resolve()
    file_dir = Path(__file__).resolve().parent
    project_root_candidate = (file_dir / "../../../training_data.csv").resolve()
    return project_root_candidate


def preprocess_and_aggregate(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load raw events CSV, construct hybrid identity, aggregate hourly behavior features.

    Hybrid identity:
      - Use actor_identity when present, non-empty, and not in {Anonymous, Unknown}
      - Otherwise, fallback to actor_ip_address

    Aggregated features per (1H window, entity_id):
      - event_count
      - failure_ratio
      - unique_ips
      - critical_actions_count
      - is_night (hour in [0..6] or [21..23] based on window start)

    Returns a DataFrame indexed by [event_time, entity_id].
    """
    csv_path = Path(file_path) if file_path else _default_training_csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(f"Training data not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    if "event_time" not in df.columns:
        raise ValueError("Input CSV must contain 'event_time' column.")
    df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")
    df = df.dropna(subset=["event_time"])

                                                                          
    for required_col in ["actor_identity", "actor_ip_address", "action_name"]:
        if required_col not in df.columns:
            df[required_col] = np.nan
                                                                          
    if "status" in df.columns and df["status"].notna().any():
        pass                  
    elif "event_status" in df.columns:
        df["status"] = df["event_status"]
    else:
        df["status"] = np.nan

                                                                        
    identity_series = df["actor_identity"].astype(str).str.strip()
    invalid_identity_values = {"", "nan", "none", "anonymous", "unknown"}
    is_valid_identity = df[
        "actor_identity"
    ].notna() & ~identity_series.str.lower().isin(invalid_identity_values)
    entity_id = np.where(
        is_valid_identity,
        identity_series,
        df["actor_ip_address"].astype(str).str.strip(),
    )
    df["entity_id"] = entity_id

                                    
    status_series = df["status"].astype(str).str.strip().str.upper()
    df["is_failure"] = status_series.eq("FAILURE")

    action_series = df["action_name"].astype(str).str.strip().str.lower()
    df["is_critical_action"] = action_series.str.startswith(("delete", "terminate"))

                                           
    grouped = df.groupby([pd.Grouper(key="event_time", freq="1h"), "entity_id"])

    features = grouped.agg(
        event_count=("event_time", "size"),
        failure_ratio=("is_failure", "mean"),
        unique_ips=("actor_ip_address", "nunique"),
        critical_actions_count=("is_critical_action", "sum"),
    )

                                             
    window_hours = features.index.get_level_values(0).hour
    is_night = ((window_hours <= 6) | (window_hours >= 21)).astype(int)
    features = features.assign(is_night=is_night)

                               
    features.index.set_names(["event_time", "entity_id"], inplace=True)
    return features


def train_and_save_model(
    features_df: pd.DataFrame,
) -> Tuple[IsolationForest, StandardScaler]:
    """
    Fill missing values, scale features, train IsolationForest, and persist artifacts.
    Saves:
      - model.pkl
      - scaler.pkl
    to the ml_engine directory.
    """
    if features_df.empty:
        raise ValueError("Features DataFrame is empty; cannot train model.")

    features_df = features_df.fillna(0)

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(features_df.values)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
    )
    model.fit(scaled_values)

    output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "model.pkl"
    scaler_path = output_dir / "scaler.pkl"

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    return model, scaler


if __name__ == "__main__":
    print("Starting preprocessing and aggregation...")
    aggregated_df = preprocess_and_aggregate()
    print(f"Aggregated feature shape: {aggregated_df.shape}")

    print("Training IsolationForest model and saving artifacts...")
    model, scaler = train_and_save_model(aggregated_df)

    artifacts_dir = Path(__file__).resolve().parent
    print("Artifacts saved:")
    print(f" - Model: {artifacts_dir / 'model.pkl'}")
    print(f" - Scaler: {artifacts_dir / 'scaler.pkl'}")
    print("Done.")
