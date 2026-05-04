from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

# Hardcoded exactly to your working local ports
MLFLOW_URI = "http://127.0.0.1:5000"
API_URL    = "http://127.0.0.1:8000"

default_args = {
    "owner": "faizan",
    "retries": 0,
    "email_on_failure": False,
}

dag = DAG(
    dag_id="model_monitor",
    description="Hourly: check API health and model registry status",
    schedule="0 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["monitoring", "mlops"],
)

def check_api_health(**context):
    import urllib.request, json
    try:
        with urllib.request.urlopen(f"{API_URL}/health", timeout=5) as r:
            data = json.loads(r.read())
            assert data.get("status") == "ok", f"Unexpected status: {data}"
            print(f"API healthy: {data}")
    except Exception as e:
        raise RuntimeError(f"API health check failed: {e}")

def check_model_registry(**context):
    import mlflow
    from mlflow.tracking import MlflowClient
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = MlflowClient()
    versions = client.search_model_versions("name='image-quality-classifier'")
    prod = [v for v in versions if v.current_stage == "Production"]
    if not prod:
        raise RuntimeError("No Production model found in registry!")
    v = prod[0]
    print(f"Production model: version={v.version} run_id={v.run_id[:8]}")
    context["ti"].xcom_push(key="model_version", value=v.version)

def log_monitoring_summary(**context):
    version = context["ti"].xcom_pull(key="model_version", task_ids="check_model_registry")
    print(f"Monitor run successful.")
    print(f"  API:   healthy")
    print(f"  Model: version {version} in Production")

with dag:
    api_check   = PythonOperator(task_id="check_api_health", python_callable=check_api_health)
    model_check = PythonOperator(task_id="check_model_registry", python_callable=check_model_registry)
    summary     = PythonOperator(task_id="log_summary", python_callable=log_monitoring_summary)

    api_check >> model_check >> summary
