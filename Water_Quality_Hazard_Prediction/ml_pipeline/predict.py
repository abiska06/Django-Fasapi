"""
predict.py
----------
Inference layer for the hazard-prediction microservice. Loads the trained
pipelines once at import time and exposes a single `predict` function that
takes raw sensor readings and returns a pH forecast + hazard verdict.

Import this directly inside your FastAPI service, e.g.:

    from predict import predict, HazardInput

    @app.post("/predict")
    def predict_endpoint(payload: HazardInput):
        return predict(payload.dict())

Keeping this as a plain module (no FastAPI/Django imports) means it can be
unit-tested standalone and reused by either service.
"""

from pathlib import Path
from typing import TypedDict

import joblib
import json
import numpy as np
import pandas as pd

from data_pipeline import MODEL_FEATURES

_MODELS_DIR = Path(__file__).parent / "models"

_reg_pipe = joblib.load(_MODELS_DIR / "ph_regressor.joblib")
_clf_pipe = joblib.load(_MODELS_DIR / "hazard_classifier.joblib")
with open(_MODELS_DIR / "metadata.json") as f:
    _METADATA = json.load(f)


class HazardInput(TypedDict, total=False):
    conductance_max: float
    conductance_min: float
    conductance_mean: float
    ph_max: float
    ph_min: float
    do_max: float
    do_mean: float
    temp_mean: float


def _to_feature_row(payload: dict) -> pd.DataFrame:
    missing = [f for f in MODEL_FEATURES if f not in payload]
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    return pd.DataFrame([[payload[f] for f in MODEL_FEATURES]], columns=MODEL_FEATURES)


def predict(payload: dict) -> dict:
    """Run both models on one input row and return a combined verdict.

    Args:
        payload: dict with the 8 keys listed in HazardInput, values expected
            in the same normalized 0-1 scale the models were trained on
            (see README for how to fit/apply that scaler to raw sensor units).

    Returns:
        dict with predicted_ph, is_hazard (bool), hazard_probability (0-1),
        and the normalized-pH bounds used to define "hazard".
    """
    X = _to_feature_row(payload)

    predicted_ph = float(_reg_pipe.predict(X)[0])
    hazard_proba = float(_clf_pipe.predict_proba(X)[0, 1])
    is_hazard = bool(_clf_pipe.predict(X)[0])

    lo, hi = _METADATA["hazard_bounds_normalized_pH"]
    return {
        "predicted_ph": predicted_ph,
        "is_hazard": is_hazard,
        "hazard_probability": round(hazard_proba, 4),
        "hazard_bounds_normalized_pH": {"lower": lo, "upper": hi},
    }


if __name__ == "__main__":
    # Quick smoke test using a plausible mid-range sample
    sample = {
        "conductance_max": 0.05,
        "conductance_min": 0.05,
        "conductance_mean": 0.55,
        "ph_max": 0.88,
        "ph_min": 0.03,
        "do_max": 0.85,
        "do_mean": 0.58,
        "temp_mean": 0.6,
    }
    print(predict(sample))
