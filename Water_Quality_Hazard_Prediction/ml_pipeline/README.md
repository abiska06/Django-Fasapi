# Water Quality Hazard Prediction — ML Pipeline

Trained on the UCI **Water Quality Prediction** dataset (Zhao et al., 2019):
37 Georgia, USA monitoring sites, 423 days, 11 normalized sensor features,
target = next-day pH.

## Files

| File | Purpose |
|---|---|
| `data_pipeline.py` | Loads the raw `.mat` file, reshapes it into a tidy table, engineers the hazard label. Shared by training and inference so preprocessing never drifts. |
| `train.py` | Trains a `RandomForestRegressor` (pH forecast) and a `GradientBoostingClassifier` (hazard flag), evaluates on the held-out test split, saves artifacts to `models/`. |
| `predict.py` | Loads the saved models once and exposes `predict(payload: dict) -> dict`. Framework-agnostic — no FastAPI/Django imports — so it's easy to unit test. |
| `fastapi_service.py` | Thin FastAPI wrapper around `predict.py`: `POST /predict`, `GET /health`. This is what Django will call. |
| `models/` | `ph_regressor.joblib`, `hazard_classifier.joblib`, `metadata.json` (metrics, feature importances, hazard thresholds). |

## Run it

```bash
pip install -r requirements.txt

# 1. Train (regenerates models/ from the raw .mat file)
python train.py --mat-path /path/to/water_dataset.mat

# 2. Serve
uvicorn fastapi_service:app --host 0.0.0.0 --port 8001 --reload
```

Test:
```bash
curl -X POST http://localhost:8001/predict -H "Content-Type: application/json" -d '{
  "conductance_max": 0.05, "conductance_min": 0.05, "conductance_mean": 0.55,
  "ph_max": 0.88, "ph_min": 0.03, "do_max": 0.85, "do_mean": 0.58, "temp_mean": 0.6
}'
```

## Current model performance (test split)

- **pH regression**: RMSE 0.0116, MAE 0.0066, R² 0.845
- **Hazard classification**: Accuracy 97.4%, Precision 0.82, Recall 0.62, F1 0.70, ROC-AUC 0.97
  (full numbers in `models/metadata.json`)

Recall (0.62) is the number to watch — it means ~38% of true hazard days are
currently missed. If you'd rather catch more hazards at the cost of more
false alarms, lower the classifier's decision threshold in `predict.py`
(currently the sklearn default 0.5) using `hazard_probability` instead of
`is_hazard`.

## Important caveats to resolve before production

1. **Hazard label is a statistical proxy, not a real safety threshold.**
   The dataset ships min-max normalized values with the original scaler
   discarded, so we can't recover true pH units. The current label flags
   values statistically far from the training IQR — swap in a real
   threshold (e.g. EPA's 6.5–8.5 pH safe band) as soon as you have the
   original min/max used to normalize the data, or a fresh unnormalized
   feed from your own sensors.
2. **Collinearity**: `temp_min`/`temp_max` (~0.98 corr with `temp_mean`) and
   `do_min` (~0.97 corr with `do_mean`) were dropped from `MODEL_FEATURES`
   to reduce redundancy — revisit if you bring in new features.
3. **Leakage check**: `ph_max` and `do_max` correlate strongly with the
   target (0.72 and 0.88) because they're same-day aggregate stats — verify
   your production feed timestamps these *before* the day you're
   forecasting, not concurrently with it.

## Suggested Django + FastAPI integration

- **FastAPI** (this service): stateless inference — `/predict`. Scale it
  independently, retrain/redeploy without touching Django.
- **Django**: owns users, sites/sensors metadata, and prediction history.
  On a new sensor reading, Django calls this service (`httpx`/`requests`),
  stores the returned verdict in its own DB, and drives the
  dashboard/alerts/admin UI.
