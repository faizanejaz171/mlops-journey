import os
import mlflow
from mlflow.tracking import MlflowClient

TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI","http://localhost:5000")
EXPERIMENT   = "image-quality-classifier"
MODEL_NAME   = "image-quality-classifier"


def promote_best():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    exp = client.get_experiment_by_name(EXPERIMENT)
    if not exp:
        print("No experiment found."); return

    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.f1_score DESC"],
        max_results=1,
    )
    if not runs:
        print("No runs found."); return

    best   = runs[0]
    run_id = best.info.run_id
    f1     = best.data.metrics["f1_score"]
    print(f"Best run: {run_id[:8]} | F1={f1:.4f}")
    print(f"Params: {best.data.params}")

    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    best_ver = next((v.version for v in versions if v.run_id==run_id), None)
    if not best_ver:
        print("Version not found."); return

    for v in versions:
        if v.current_stage == "Production":
            client.transition_model_version_stage(
                name=MODEL_NAME, version=v.version, stage="Archived"
            )
            print(f"Archived previous production version {v.version}")

    client.transition_model_version_stage(
        name=MODEL_NAME, version=best_ver, stage="Production"
    )
    print(f"Promoted version {best_ver} to Production")


if __name__ == "__main__":
    promote_best()
