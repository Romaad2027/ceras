from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt


def _resolve_project_root() -> Path:
    """
    Resolve the project root assuming this file lives in <root>/scripts/.
    """
    return Path(__file__).resolve().parent.parent


def _ensure_import_path() -> None:
    """
    Add project root to sys.path so local modules under `src/` are importable.
    """
    project_root = _resolve_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _resolve_artifacts_paths() -> Tuple[Path, Path]:
    """
    Resolve paths to model and scaler artifacts.
    Looks under src/risk_analysis_service/ml_engine/.
    """
    project_root = _resolve_project_root()
    artifacts_dir = project_root / "src" / "risk_analysis_service" / "ml_engine"
    model_path = artifacts_dir / "model.pkl"
    scaler_path = artifacts_dir / "scaler.pkl"
    return model_path, scaler_path


def _resolve_training_csv_path() -> Path:
    """
    Resolve path to training_data.csv with a robust search order:
      1) Current working directory
      2) Project root
    """
    cwd_candidate = Path.cwd() / "training_data.csv"
    if cwd_candidate.exists():
        return cwd_candidate.resolve()
    project_root = _resolve_project_root()
    root_candidate = project_root / "training_data.csv"
    if root_candidate.exists():
        return root_candidate.resolve()
                                                                        
    return root_candidate.resolve()


def main() -> None:
    """
    Generate a 2D PCA visualization of Isolation Forest predictions based on the
    exact same hourly-aggregated features used during training.
    Saves figure to 'isolation_forest_visualization.png' (300 dpi).
    """
    _ensure_import_path()

                                                             
    from src.risk_analysis_service.ml_engine.train_model import (
        preprocess_and_aggregate,
    )

                       
    model_path, scaler_path = _resolve_artifacts_paths()
    if not scaler_path.exists() or not model_path.exists():
        raise FileNotFoundError(
            f"Artifacts not found. Expected:\n  - {scaler_path}\n  - {model_path}"
        )
    scaler = joblib.load(scaler_path)
    model = joblib.load(model_path)

                                
    training_csv = _resolve_training_csv_path()

                                                                     
    features_df = preprocess_and_aggregate(str(training_csv))
    if features_df.empty:
        raise ValueError("Aggregated features are empty; cannot visualize results.")

                                         
    feature_columns = [
        "event_count",
        "failure_ratio",
        "unique_ips",
        "critical_actions_count",
        "is_night",
    ]
                                  
    for col in feature_columns:
        if col not in features_df.columns:
            features_df[col] = 0
    features_df = features_df.fillna(0)[feature_columns]

                       
    scaled_values = scaler.transform(features_df.values)

                               
    labels = model.predict(scaled_values)                        

                            
    pca = PCA(n_components=2, random_state=42)
    components_2d = pca.fit_transform(scaled_values)
    pca_df = pd.DataFrame(components_2d, columns=["PCA Component 1", "PCA Component 2"])
    pca_df["label"] = labels

                                                                                 
    x_vals = pca_df["PCA Component 1"].to_numpy()
    y_vals = pca_df["PCA Component 2"].to_numpy()
    x_low, x_high = np.percentile(x_vals, [1, 99])
    y_low, y_high = np.percentile(y_vals, [1, 99])
    x_pad = max((x_high - x_low) * 0.1, 1e-6)
    y_pad = max((y_high - y_low) * 0.1, 1e-6)
                                                                        
    rng = np.random.default_rng(17)
    jitter_x = max((x_high - x_low) * 0.015, 1e-3)
    jitter_y = max((y_high - y_low) * 0.015, 1e-3)
    pca_df["x_plot"] = x_vals + rng.uniform(-jitter_x, jitter_x, size=len(pca_df))
    pca_df["y_plot"] = y_vals + rng.uniform(-jitter_y, jitter_y, size=len(pca_df))

                 
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 7), dpi=100)

    normals = pca_df["label"] == 1
    anomalies = pca_df["label"] == -1

    ax.scatter(
        pca_df.loc[normals, "x_plot"],
        pca_df.loc[normals, "y_plot"],
        c="blue",
        alpha=0.5,
        s=18,
        label="Normal (1)",
        edgecolors="none",
    )
    ax.scatter(
        pca_df.loc[anomalies, "x_plot"],
        pca_df.loc[anomalies, "y_plot"],
        c="red",
        alpha=0.8,
        s=22,
        label="Anomaly (-1)",
        edgecolors="none",
    )

    ax.set_title("Isolation Forest Anomaly Detection (PCA Projection)", fontsize=14)
    ax.set_xlabel("PCA Component 1", fontsize=12)
    ax.set_ylabel("PCA Component 2", fontsize=12)
    ax.legend(frameon=True)
    ax.set_xlim(x_low - x_pad, x_high + x_pad)
    ax.set_ylim(y_low - y_pad, y_high + y_pad)

                   
    total_points = len(pca_df)
    anomaly_count = int(np.sum(anomalies))
    anomaly_pct = (anomaly_count / total_points) * 100 if total_points else 0.0
    textbox = (
        f"Total windows: {total_points}\n"
        f"Anomalies: {anomaly_count} ({anomaly_pct:.2f}%)"
    )
    ax.text(
        0.02,
        0.98,
        textbox,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round,pad=0.4", facecolor="white", alpha=0.8, edgecolor="gray"
        ),
    )

                    
    output_path = _resolve_project_root() / "isolation_forest_visualization.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved visualization to: {output_path}")


if __name__ == "__main__":
    main()
