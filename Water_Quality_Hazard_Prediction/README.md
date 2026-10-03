# Water Quality Hazard Prediction Engine

A microservice-based system for predicting next-day water pH and flagging
hazardous readings, built on real USGS sensor data from 36–37 monitoring
sites in Georgia, USA.

## Project structure

```
Water_Quality_Hazard_Prediction/
├── django_portal/     Django web portal (forms, results, prediction history)
├── ml_pipeline/        FastAPI microservice + training scripts + trained models
├── dataset/            Raw (.mat) and processed (.csv) dataset
├── notebook/           Jupyter notebook: full training & evaluation walkthrough
└── report/             (add your final report PDF/DOCX here before zipping)
```

## Architecture

- **`ml_pipeline/` (FastAPI, port 8001)** — stateless inference service. Loads
  a `RandomForestRegressor` (next-day pH forecast) and a
  `GradientBoostingClassifier` (binary hazard flag), both trained on the same
  8 sensor features. Exposes `POST /predict` and `GET /health`.
- **`django_portal/` (Django, port 8000)** — user-facing web portal. An async
  Django view validates the submitted reading, calls the FastAPI service over
  `httpx` without blocking the web server, and stores every prediction in its
  own database for the history page.

Django never touches the trained models directly — every reading crosses the
service boundary as a validated Pydantic payload, and the two services can be
deployed, scaled, or redeployed independently.

## Dataset

**UCI Machine Learning Repository — Water Quality Prediction (Dataset #733)**
https://archive.ics.uci.edu/dataset/733/water+quality+prediction-1

Daily sensor readings from 36–37 Georgia, USA monitoring sites (2016–2018),
11 raw features (conductance, pH, dissolved oxygen, temperature), collected
by the USGS. Citation:

> Zhao, L., Gkountouna, O., & Pfoser, D. (2019). Spatial Auto-regressive
> Dependency Interpretable Learning Based on Spatial Topological Constraints.
> *ACM Transactions on Spatial Algorithms and Systems*, 5(3), Article 19.
> https://doi.org/10.1145/3339823

The hazard label is a derived statistical proxy (IQR outlier rule on
training-split pH), since the dataset ships without a recoverable
normalization scaler — see `notebook/water_quality_model_training.ipynb`
Section 3 and `ml_pipeline/README.md` for the full explanation and caveats.

## Running it locally

```bash
# --- 1. ML microservice ---
cd ml_pipeline
pip install -r requirements.txt
uvicorn fastapi_service:app --host 0.0.0.0 --port 8001 --reload

# --- 2. Django portal (separate terminal) ---
cd django_portal
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

Then open **http://127.0.0.1:8000/** to submit a reading, and
**http://127.0.0.1:8000/history/** to see every prediction made so far.

To retrain the models from scratch (regenerates `ml_pipeline/models/`):

```bash
cd ml_pipeline
python train.py --mat-path ../dataset/water_dataset.mat
```

## Current model performance (held-out test split)

- **pH regression:** RMSE 0.0116, MAE 0.0066, R² 0.845
- **Hazard classification:** Accuracy 97.4%, Precision 0.82, **Recall 0.62**,
  F1 0.70, ROC-AUC 0.97

Recall is the number to watch: roughly 1 in 3 true hazard days is currently
missed. This is called out on the portal's result page and should be treated
as a known limitation, not hidden — see `ml_pipeline/README.md` for how to
trade precision for recall via the classifier's decision threshold.
