from pathlib import Path
from typing import Optional

import warnings
import numpy as np
import pandas as pd
from joblib import load
from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    """
    Loads persisted scaler and IsolationForest model and provides prediction API.
    """

    def __init__(
        self, model_path: Optional[str] = None, scaler_path: Optional[str] = None
    ):
        base_dir = Path(__file__).resolve().parent
        self._model_path = Path(model_path) if model_path else base_dir / "model.pkl"
        self._scaler_path = (
            Path(scaler_path) if scaler_path else base_dir / "scaler.pkl"
        )

        self.model: Optional[BaseEstimator] = None
        self.scaler: Optional[StandardScaler] = None

                     
        try:
            if self._scaler_path.exists():
                self.scaler = load(self._scaler_path)
            else:
                warnings.warn(
                    f"Scaler file not found at {self._scaler_path}. Predictions will be disabled."
                )
        except Exception as exc:
            warnings.warn(
                f"Failed to load scaler from {self._scaler_path}: {exc}. Predictions will be disabled."
            )

                    
        try:
            if self._model_path.exists():
                self.model = load(self._model_path)
            else:
                warnings.warn(
                    f"Model file not found at {self._model_path}. Predictions will be disabled."
                )
        except Exception as exc:
            warnings.warn(
                f"Failed to load model from {self._model_path}: {exc}. Predictions will be disabled."
            )

    def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Run inference on prepared feature DataFrame.
        Returns a DataFrame with a single column 'prediction' containing -1 (anomaly) or 1 (normal).
        If artifacts are missing or input invalid, returns a DataFrame filled with NaN predictions.
        """
        if not isinstance(features_df, pd.DataFrame):
            warnings.warn(
                "features_df is not a pandas DataFrame. Returning empty predictions."
            )
            return pd.DataFrame({"prediction": []})

        if features_df.empty:
            return pd.DataFrame(index=features_df.index, data={"prediction": []})

        if self.scaler is None or self.model is None:
            warnings.warn("Model or scaler is not loaded. Returning NaN predictions.")
            return pd.DataFrame(
                index=features_df.index,
                data={"prediction": np.full(len(features_df), np.nan)},
            )

                                                       
        features_clean = features_df.fillna(0)
        try:
            X_scaled = self.scaler.transform(features_clean.values)
            preds = self.model.predict(X_scaled)
        except Exception as exc:
            warnings.warn(f"Inference failed: {exc}. Returning NaN predictions.")
            return pd.DataFrame(
                index=features_df.index,
                data={"prediction": np.full(len(features_df), np.nan)},
            )

        return pd.DataFrame(index=features_df.index, data={"prediction": preds})
