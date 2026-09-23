from __future__ import annotations

from pathlib import Path
from threading import Lock

import joblib
import numpy as np
import pandas as pd

from app.services.config import MODEL_FEATURES, MODEL_FILE, MODEL_NAME, MODEL_VERSION


class ModelService:
    def __init__(self, model_path: Path = MODEL_FILE) -> None:
        self.model_path = Path(model_path)
        self._model = None
        self._lock = Lock()

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {self.model_path}. "
                "Place the exact rf_baseline_model.joblib produced by "
                "train_rf_baseline.py in backend/ml/."
            )

        with self._lock:
            if self._model is None:
                model = joblib.load(self.model_path)
                if not hasattr(model, "predict_proba"):
                    raise TypeError(
                        "Loaded model does not expose predict_proba(). "
                        "Expected the trained sklearn Pipeline."
                    )

                feature_names = getattr(model, "feature_names_in_", None)
                if feature_names is not None:
                    feature_names = list(feature_names)
                    if feature_names != MODEL_FEATURES:
                        raise ValueError(
                            "Loaded model feature schema does not match the "
                            "35-feature training contract.\n"
                            f"Expected: {MODEL_FEATURES}\n"
                            f"Found: {feature_names}"
                        )

                self._model = model

    def status(self) -> dict[str, object]:
        return {
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "artifact": self.model_path.name,
            "loaded": self._model is not None,
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        self.load()
        if list(X.columns) != MODEL_FEATURES:
            raise ValueError(
                "Feature column order does not match the trained model contract."
            )
        probabilities = self._model.predict_proba(X)[:, 1]
        probabilities = np.asarray(probabilities, dtype=float)
        if len(probabilities) != len(X):
            raise RuntimeError("Prediction row count does not match input row count.")
        if not np.isfinite(probabilities).all():
            raise RuntimeError("Model returned NaN or infinite probabilities.")
        if ((probabilities < 0) | (probabilities > 1)).any():
            raise RuntimeError("Model returned probability outside [0, 1].")
        return probabilities


_model_service: ModelService | None = None


def get_model_service() -> ModelService:
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service
