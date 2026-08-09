"""Train anomaly detection and failure prediction models."""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(__file__).parent.parent / "ml" / "artifacts"


def generate_synthetic_data(n_normal: int = 2000, n_anomaly: int = 200) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    X_normal = rng.normal(0, 0.3, (n_normal, 9))
    y_normal = np.zeros(n_normal)

    X_anomaly = rng.normal(0, 0.3, (n_anomaly, 9))
    X_anomaly[:, 0] += rng.uniform(1.0, 2.5, n_anomaly)
    X_anomaly[:, 1] += rng.uniform(1.5, 3.0, n_anomaly)
    X_anomaly[:, 8] += rng.uniform(10, 30, n_anomaly)
    y_anomaly = np.ones(n_anomaly)

    X = np.vstack([X_normal, X_anomaly])
    y = np.concatenate([y_normal, y_anomaly])
    return X, y


def train_models() -> dict:
    logger.info("Generating synthetic training data...")
    X, y = generate_synthetic_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    logger.info("Training Isolation Forest (anomaly detection)...")
    anomaly_model = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
    anomaly_model.fit(X_train)

    logger.info("Training Random Forest (failure prediction)...")
    failure_model = RandomForestClassifier(n_estimators=100, random_state=42)
    failure_model.fit(X_train, y_train)

    y_pred = failure_model.predict(X_test)
    f1 = f1_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(anomaly_model, ARTIFACT_DIR / "anomaly_model.joblib")
    joblib.dump(failure_model, ARTIFACT_DIR / "failure_model.joblib")

    metrics = {
        "f1_score": round(f1, 4),
        "precision": round(report["1"]["precision"], 4),
        "recall": round(report["1"]["recall"], 4),
        "model_version": "1.0.0-trained",
    }
    with open(ARTIFACT_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("Models saved to %s", ARTIFACT_DIR)
    logger.info("Metrics: F1=%.4f, Precision=%.4f, Recall=%.4f", f1, metrics["precision"], metrics["recall"])
    return metrics


if __name__ == "__main__":
    train_models()
