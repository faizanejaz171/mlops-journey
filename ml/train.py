import os, argparse
import pandas as pd
import mlflow, mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score
)

TRACKING_URI    = os.getenv("MLFLOW_TRACKING_URI","http://localhost:5000")
EXPERIMENT_NAME = "image-quality-classifier"
FEATURES        = ["width","height","size_kb","blur_score","brightness","aspect_ratio"]


def load_data(csv_path):
    df = pd.read_csv(csv_path)
    X, y = df[FEATURES], df["label"]
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def train_and_log(csv_path, n_estimators, max_depth, min_samples):
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    X_tr, X_te, y_tr, y_te = load_data(csv_path)

    with mlflow.start_run():
        mlflow.set_tag("model_type", "RandomForest")
        mlflow.set_tag("engineer", "faizan")

        mlflow.log_param("n_estimators",     n_estimators)
        mlflow.log_param("max_depth",        max_depth)
        mlflow.log_param("min_samples_split",min_samples)
        mlflow.log_param("train_size",       len(X_tr))
        mlflow.log_param("test_size",        len(X_te))

        clf = RandomForestClassifier(
            n_estimators=n_estimators, max_depth=max_depth,
            min_samples_split=min_samples, random_state=42, n_jobs=-1
        )
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)

        acc  = accuracy_score(y_te, y_pred)
        f1   = f1_score(y_te, y_pred, zero_division=0)
        prec = precision_score(y_te, y_pred, zero_division=0)
        rec  = recall_score(y_te, y_pred, zero_division=0)

        mlflow.log_metric("accuracy",  round(acc,4))
        mlflow.log_metric("f1_score",  round(f1,4))
        mlflow.log_metric("precision", round(prec,4))
        mlflow.log_metric("recall",    round(rec,4))

        mlflow.sklearn.log_model(
            sk_model=clf,
            artifact_path="model",
            registered_model_name="image-quality-classifier",
        )

        rid = mlflow.active_run().info.run_id
        print(f"Run {rid[:8]} | n={n_estimators} d={max_depth} | acc={acc:.4f} f1={f1:.4f}")
        return acc, f1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data",          default="ml/dataset.csv")
    ap.add_argument("--n-estimators",  type=int, default=100)
    ap.add_argument("--max-depth",     type=int, default=10)
    ap.add_argument("--min-samples",   type=int, default=2)
    args = ap.parse_args()
    train_and_log(args.data, args.n_estimators, args.max_depth, args.min_samples)
