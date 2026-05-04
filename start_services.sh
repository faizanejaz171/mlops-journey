#!/bin/bash
set -e

echo "Activating environment..."
source /home/faizan/Documents/mlops-journey/day-1/mlops-env/bin/activate

export AIRFLOW_HOME=~/airflow
export AIRFLOW__CORE__LOAD_EXAMPLES=False

echo "Starting MLflow..."
# The '&' runs it in the background
mlflow ui --port 5000 &

echo "Starting Airflow webserver on 8081..."
airflow webserver --port 8081 --daemon

echo "Starting Airflow scheduler..."
airflow scheduler --daemon

echo ""
echo "✅ All Services Running in Background!"
echo "  Airflow UI  → http://127.0.0.1:8081/home"
echo "  MLflow UI   → http://127.0.0.1:5000"
