import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PROJECT_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH      = os.path.join(PROJECT_ROOT, "ml", "dataset.csv")
IMAGE_FOLDER   = os.path.join(PROJECT_ROOT, "test_images")
MLFLOW_URI     = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

default_args = {
    "owner":            "faizan",
    "retries":          1,
    "retry_delay":      timedelta(minutes=2),
    "email_on_failure": False,
}

dag = DAG(
    dag_id="image_quality_pipeline",
    description="Generate data → train classifier → promote best model",
    schedule="0 2 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["mlops", "image-quality", "cv"],
)


def task_generate_data(**context):
    """
    Task 1: scan image folder, extract features, save CSV.
    XCom pushes the output path so downstream tasks can use it.
    """
    from ml.generate_data import generate_dataset
    generate_dataset(IMAGE_FOLDER, DATA_PATH)
    context["ti"].xcom_push(key="data_path", value=DATA_PATH)
    print(f"Data generated: {DATA_PATH}")


def task_train_models(**context):
    """
    Task 2: run a small sweep of 4 parameter combinations.
    Logs every run to MLflow. Pushes best run_id via XCom.
    """
    import mlflow
    from ml.train import train_and_log

    os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_URI
    data_path = context["ti"].xcom_pull(key="data_path", task_ids="generate_data")

    configs = [
        {"n_estimators": 50,  "max_depth": 5,  "min_samples": 2},
        {"n_estimators": 100, "max_depth": 10, "min_samples": 2},
        {"n_estimators": 150, "max_depth": 15, "min_samples": 5},
        {"n_estimators": 200, "max_depth": 20, "min_samples": 2},
    ]

    best_f1  = -1
    best_cfg = None

    for cfg in configs:
        acc, f1 = train_and_log(
            data_path,
            cfg["n_estimators"],
            cfg["max_depth"],
            cfg["min_samples"],
        )
        print(f"Config {cfg} → acc={acc:.4f} f1={f1:.4f}")
        if f1 > best_f1:
            best_f1  = f1
            best_cfg = cfg

    print(f"Best config this run: {best_cfg} | F1={best_f1:.4f}")
    context["ti"].xcom_push(key="best_f1", value=best_f1)


def task_promote_best(**context):
    """
    Task 3: find the best run in MLflow by F1, promote to Production.
    Only promotes if F1 exceeds 0.7 — prevents a bad model going live.
    """
    best_f1 = context["ti"].xcom_pull(key="best_f1", task_ids="train_models")

    if best_f1 < 0.7:
        print(f"F1={best_f1:.4f} is below threshold 0.7 — skipping promotion.")
        return

    os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_URI
    from ml.promote_best import promote_best
    promote_best()
    print("Promotion complete.")


def task_health_check(**context):
    """
    Task 4: call the live API health endpoint to confirm
    the service is still running after pipeline completes.
    """
    import urllib.request
    api_url = os.getenv("API_URL", "http://localhost:8000")
    try:
        with urllib.request.urlopen(f"{api_url}/health", timeout=5) as resp:
            body = resp.read().decode()
            print(f"API health: {body}")
    except Exception as e:
        print(f"Health check failed (non-fatal): {e}")


with dag:
    generate = PythonOperator(
        task_id="generate_data",
        python_callable=task_generate_data,
    )

    train = PythonOperator(
        task_id="train_models",
        python_callable=task_train_models,
    )

    promote = PythonOperator(
        task_id="promote_best",
        python_callable=task_promote_best,
    )

    health = PythonOperator(
        task_id="health_check",
        python_callable=task_health_check,
    )

    generate >> train >> promote >> health
