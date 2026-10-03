"""
water_quality_pipeline_dag.py
------------------------------
Orchestrates the two scripts that already exist in ml_pipeline/:

  1. data_pipeline.py  -> reshapes the raw .mat sensor data into a tidy table
  2. train.py           -> trains the pH regressor + hazard classifier and
                            writes the .joblib files FastAPI serves from

This DAG doesn't reimplement any ML logic — it just runs your existing,
already-tested scripts in order, with cwd set to ml_pipeline/ so their
relative file paths (models/, ../dataset/...) resolve the same way they do
when you run them by hand.

Trigger manually from the Airflow UI (schedule=None): this models a
"retrain on demand" workflow, which is the realistic version of retraining
for a project graded once rather than one that needs to run nightly.
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="water_quality_training_pipeline",
    description="Reshape raw sensor data, then train the pH regressor and hazard classifier",
    schedule=None,          # manual trigger only — see docstring above
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["water-quality", "ml"],
) as dag:

    reshape_data = BashOperator(
        task_id="reshape_data",
        bash_command="cd /opt/airflow/ml_pipeline && python data_pipeline.py",
    )

    train_models = BashOperator(
        task_id="train_models",
        bash_command=(
            "cd /opt/airflow/ml_pipeline && "
            "python train.py --mat-path /opt/airflow/dataset/water_dataset.mat"
        ),
    )

    reshape_data >> train_models
