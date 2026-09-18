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

    def _aggregate_to_raw(self, importances: np.ndarray) -> np.ndarray:
        """Fold transformed-space importances onto the 35 raw MODEL_FEATURES.

        The Random Forest importance is computed on the transformed feature
        space (imputed numerics, missing indicators, one-hot categoricals).
        This maps every transformed column to exactly one raw MODEL_FEATURE
        using the fitted preprocessor metadata positionally (never by parsing
        column-name strings, which is ambiguous for category values such as
        "E-Commerce" or "Mobile_App"):

        * numeric block: the first len(feature_names_in_) outputs are the
          imputed raw features (same names, in order); any remaining outputs
          are SimpleImputer missing-indicator columns whose parent raw feature
          is resolved via indicator_.features_ (index into the block's raw
          numeric feature list).
        * categorical block: OneHotEncoder columns appear as one contiguous
          run per raw feature, of length len(categories_[i]), in the block's
          raw categorical feature order.
        """
        named_steps = getattr(self._model, "named_steps", {})
        preprocessor = named_steps.get("preprocessing")
        if preprocessor is None:
            raise RuntimeError(
                "Model pipeline has no 'preprocessing' step; cannot map "
                "transformed importances to the 35 raw features."
            )

        raw_to_index = {name: i for i, name in enumerate(MODEL_FEATURES)}
        aggregates = np.zeros(len(MODEL_FEATURES), dtype=float)
        consumed = 0

        for block_name, transformer, _columns in preprocessor.transformers_:
            block_importances = importances[consumed : consumed + len(transformer.get_feature_names_out())]
            consumed += len(block_importances)

            if block_name == "numeric":
                imputer = transformer[-1]
                numeric_features = list(imputer.feature_names_in_)
                if len(block_importances) < len(numeric_features):
                    raise RuntimeError(
                        "Numeric block output is shorter than its raw feature list."
                    )
                imputed = block_importances[: len(numeric_features)]
                indicators = block_importances[len(numeric_features) :]
                for feature, value in zip(numeric_features, imputed):
                    if feature not in raw_to_index:
                        raise RuntimeError(
                            f"Numeric feature '{feature}' is not in MODEL_FEATURES."
                        )
                    aggregates[raw_to_index[feature]] += value
                indicator_features = getattr(imputer.indicator_, "features_", [])
                if len(indicators) != len(indicator_features):
                    raise RuntimeError(
                        "Numeric missing-indicator count does not match the "
                        "fitted MissingIndicator metadata."
                    )
                for feature_idx, value in zip(indicator_features, indicators):
                    parent = numeric_features[feature_idx]
                    if parent not in raw_to_index:
                        raise RuntimeError(
                            f"Missing-indicator parent '{parent}' is not in "
                            "MODEL_FEATURES."
                        )
                    aggregates[raw_to_index[parent]] += value

            elif block_name == "categorical":
                encoder = transformer[-1]
                categorical_features = list(transformer[0].feature_names_in_)
                category_counts = [len(categories) for categories in encoder.categories_]
                if sum(category_counts) != len(block_importances):
                    raise RuntimeError(
                        "Categorical block output count does not match the "
                        "fitted OneHotEncoder categories."
                    )
                position = 0
                for feature, count in zip(categorical_features, category_counts):
                    if feature not in raw_to_index:
                        raise RuntimeError(
                            f"Categorical feature '{feature}' is not in "
                            "MODEL_FEATURES."
                        )
                    aggregates[raw_to_index[feature]] += block_importances[
                        position : position + count
                    ].sum()
                    position += count

            else:
                raise RuntimeError(
                    f"Unexpected preprocessing block '{block_name}'; cannot "
                    "map its importances to MODEL_FEATURES."
                )

        if consumed != len(importances):
            raise RuntimeError(
                f"Mapped only {consumed} of {len(importances)} transformed "
                "importance values; preprocessor column counts are inconsistent."
            )
        if not np.isclose(aggregates.sum(), importances.sum(), rtol=1e-12, atol=1e-12):
            raise RuntimeError(
                "Aggregated importance sum diverged from the model's "
                "transformed importance sum."
            )
        return aggregates

    def feature_importances(self) -> np.ndarray:
        """Global feature_importances_ aligned to MODEL_FEATURES order.

        Used by the rule-based explanation heuristic. Handles a bare estimator
        whose importances are already aligned, or a sklearn Pipeline whose
        final step is the Random Forest (in which case the transformed-space
        importances are aggregated back onto the 35 raw features).
        """
        self.load()
        estimator = self._model
        named_steps = getattr(estimator, "named_steps", None)
        if named_steps is not None:
            estimator = list(named_steps.values())[-1]
        importances = getattr(estimator, "feature_importances_", None)
        if importances is None:
            raise RuntimeError(
                "Model does not expose feature_importances_. "
                "Explanation is unavailable for this artifact."
            )
        importances = np.asarray(importances, dtype=float)
        if importances.shape[0] != len(MODEL_FEATURES):
            importances = self._aggregate_to_raw(importances)
        if importances.shape[0] != len(MODEL_FEATURES):
            raise RuntimeError(
                "Feature importance length does not match the 35-feature "
                "training contract."
            )
        return importances

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
