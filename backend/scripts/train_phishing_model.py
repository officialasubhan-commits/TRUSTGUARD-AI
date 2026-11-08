"""
Model Training and Evaluation Pipeline for TrustGuard AI.

Trains a Random Forest Classifier on structural and lexical URL features
using the identical feature schema extracted during live inference.
Evaluates precision, recall, F1, ROC-AUC, confusion matrix, and exports
versioned model artifacts and metadata.
"""

from __future__ import annotations

import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
except ImportError:
    # Bypass unused _cdnmf_fast dependency blocked on Windows Application Control
    from sklearn.ensemble._forest import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

# Ensure backend root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ml_feature_adapter import FEATURE_NAMES, extract_feature_vector  # noqa: E402
from app.services.url_analyzer import URLAnalyzer  # noqa: E402
from app.utils.url_normalizer import normalize_url  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("train_model")

DATA_FILE = BACKEND_DIR / "ml" / "data" / "phishing_dataset.csv"
MODEL_DIR = BACKEND_DIR / "ml" / "models"
MODEL_PATH = MODEL_DIR / "phishing_rf_v1.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
METRICS_PATH = MODEL_DIR / "metrics.json"

MODEL_VERSION = "rf-v1.0.0"
RANDOM_STATE = 42
TEST_SIZE = 0.20


def load_dataset(data_path: Path) -> Tuple[List[str], List[int]]:
    """Loads and validates raw URL and label records from CSV."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run prepare_dataset.py first.")

    urls: List[str] = []
    labels: List[int] = []

    with open(data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "url" not in reader.fieldnames or "label" not in reader.fieldnames:
            raise ValueError("Dataset CSV must contain 'url' and 'label' headers.")

        for row in reader:
            url = row["url"].strip()
            raw_label = row["label"].strip()
            if not url:
                continue
            try:
                label = int(raw_label)
                if label not in (0, 1):
                    continue
                urls.append(url)
                labels.append(label)
            except ValueError:
                continue

    logger.info("Loaded %d validated samples from %s", len(urls), data_path)
    return urls, labels


def extract_features_matrix(urls: List[str]) -> np.ndarray:
    """Extracts features for all URLs using the official URLAnalyzer and feature adapter."""
    analyzer = URLAnalyzer()
    matrix: List[List[float]] = []

    logger.info(
        "Extracting %d features for %d URLs using URLAnalyzer...", len(FEATURE_NAMES), len(urls)
    )
    for i, raw_url in enumerate(urls):
        try:
            norm_url = normalize_url(raw_url)
        except Exception:
            norm_url = raw_url

        analysis = analyzer.analyze(raw_url=raw_url, normalized_url=norm_url)
        features_dict = analysis["features"]
        vector = extract_feature_vector(features_dict)
        matrix.append(vector)

        if (i + 1) % 500 == 0 or (i + 1) == len(urls):
            logger.info("Extracted features for %d/%d samples...", i + 1, len(urls))

    return np.array(matrix, dtype=np.float64)


def train_and_evaluate():
    """Main training workflow with stratified train/test split and metric computation."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    urls, labels = load_dataset(DATA_FILE)
    y = np.array(labels, dtype=np.int32)

    # 2. Extract Feature Matrix
    X = extract_features_matrix(urls)

    # 3. Stratified Train / Test Split
    logger.info(
        "Performing stratified train/test split (test_size=%.2f, seed=%d)...",
        TEST_SIZE,
        RANDOM_STATE,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    logger.info("Training set: %d samples; Test set: %d samples", len(X_train), len(X_test))

    # 4. Train Scikit-Learn Random Forest Classifier
    logger.info(
        "Training RandomForestClassifier (n_estimators=100, max_depth=12, class_weight='balanced')..."
    )
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    clf.fit(X_train, y_train)

    # 5. Evaluate on Test Set
    logger.info("Evaluating model performance on unseen test split...")
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred).tolist()

    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]

    logger.info("================ MODEL EVALUATION RESULTS ================")
    logger.info("Accuracy:        %.4f (%d/%d)", acc, int(acc * len(y_test)), len(y_test))
    logger.info("Precision:       %.4f", prec)
    logger.info("Recall:          %.4f", rec)
    logger.info("F1 Score:        %.4f", f1)
    logger.info("ROC-AUC:         %.4f", roc_auc)
    logger.info("Confusion Matrix: TN=%d, FP=%d, FN=%d, TP=%d", tn, fp, fn, tp)
    logger.info("==========================================================")

    # 6. Extract Feature Importances
    importances = clf.feature_importances_
    feature_imp_dict: Dict[str, float] = {
        name: round(float(imp), 4) for name, imp in zip(FEATURE_NAMES, importances)
    }
    sorted_importances = dict(
        sorted(feature_imp_dict.items(), key=lambda item: item[1], reverse=True)
    )

    logger.info("Top 5 Predictive Features:")
    for name, weight in list(sorted_importances.items())[:5]:
        logger.info("  - %s: %.4f", name, weight)

    # 7. Persist Model Artifact
    logger.info("Saving trained model artifact to %s", MODEL_PATH)
    joblib.dump(clf, MODEL_PATH, compress=3)

    # 8. Persist Metadata & Metrics
    now_iso = datetime.now(timezone.utc).isoformat()
    metadata = {
        "model_version": MODEL_VERSION,
        "algorithm": "RandomForestClassifier",
        "n_estimators": 100,
        "max_depth": 12,
        "random_state": RANDOM_STATE,
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "total_dataset_size": len(urls),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "top_features": sorted_importances,
        "created_at": now_iso,
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    metrics_record = {
        "model_version": MODEL_VERSION,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        },
        "test_samples": len(y_test),
        "evaluated_at": now_iso,
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_record, f, indent=2)

    logger.info("Model artifacts, metadata, and evaluation metrics successfully saved.")


if __name__ == "__main__":
    train_and_evaluate()
