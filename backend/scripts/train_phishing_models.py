"""
TrustGuard AI — Multi-Model Machine Learning Training & Evaluation Pipeline.

Trains, evaluates, and rigorously compares 5 classification algorithms:
1. Logistic Regression (Baseline linear classifier with L2 regularization)
2. Decision Tree (Interpretable tree classifier with controlled depth)
3. Random Forest (Bagging ensemble of decision trees)
4. Gradient Boosting (Sequential boosting ensemble)
5. Extra Trees (Extremely randomized trees ensemble)

Computes 5-fold Stratified Cross-Validation and held-out test metrics:
- Accuracy, Precision, Recall, F1-Score, ROC-AUC
- Confusion Matrix (TP, FP, TN, FN)
- False Positive Rate (FPR) & False Negative Rate (FNR)

Selects the champion model, saves versioned model artifacts, candidate models,
feature importances, and detailed comparison reports.
"""
from __future__ import annotations

import csv
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np

# Use direct subpackage imports for fast, robust resolution on Windows
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
try:
    from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
except ImportError:
    from sklearn.ensemble._forest import ExtraTreesClassifier, RandomForestClassifier
    from sklearn.ensemble._gb import GradientBoostingClassifier

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

# Ensure backend root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ml_feature_adapter import (
    FEATURE_NAMES_V2,
    FEATURE_SCHEMA_VERSION,
    extract_feature_vector,
)
from app.services.url_analyzer import URLAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("train_phishing_models")

DATA_FILE = BACKEND_DIR / "ml" / "data" / "phishing_dataset.csv"
MODEL_DIR = BACKEND_DIR / "ml" / "models"
MODEL_PATH = MODEL_DIR / "phishing_rf_v2.joblib"
LEGACY_MODEL_PATH = MODEL_DIR / "phishing_rf_v1.joblib"
CANDIDATE_MODELS_PATH = MODEL_DIR / "candidate_models.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
METRICS_PATH = MODEL_DIR / "metrics.json"
COMPARISON_PATH = MODEL_DIR / "model_comparison.json"
IMPORTANCE_PATH = MODEL_DIR / "feature_importance.json"

MODEL_VERSION = "rf-v2.0.0"
RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5


def load_dataset(data_path: Path) -> Tuple[List[str], List[int]]:
    """Loads and validates raw URL and label records from CSV."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}.")

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
    """Extracts the 30-feature Schema v2 matrix using URLAnalyzer."""
    analyzer = URLAnalyzer()
    matrix: List[List[float]] = []

    logger.info("Extracting %d features across %d URLs...", len(FEATURE_NAMES_V2), len(urls))
    for i, url in enumerate(urls):
        try:
            analysis = analyzer.analyze(raw_url=url, normalized_url=url)
            vector = extract_feature_vector(analysis["features"], target_feature_count=30)
            matrix.append(vector)
        except Exception as e:
            logger.warning("Feature extraction failed for sample %d (%s): %s", i, url, e)
            matrix.append([0.0] * len(FEATURE_NAMES_V2))

    return np.array(matrix, dtype=np.float32)


def train_and_evaluate_models() -> Dict[str, Any]:
    """
    Main training and evaluation routine comparing 5 candidate classification algorithms.
    """
    t_start = time.perf_counter()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Dataset
    urls, labels = load_dataset(DATA_FILE)
    X = extract_features_matrix(urls)
    y = np.array(labels, dtype=np.int32)

    total_samples = len(y)
    n_phishing = int(np.sum(y == 1))
    n_legitimate = int(np.sum(y == 0))
    logger.info("Dataset composition: %d Legitimate (0), %d Phishing (1)", n_legitimate, n_phishing)

    # 2. Stratified Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    logger.info("Training set: %d samples, Test set: %d samples", len(y_train), len(y_test))

    # Standard scaler for linear models
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 3. Candidate Algorithm Definitions
    candidates: Dict[str, Dict[str, Any]] = {
        "LogisticRegression": {
            "model": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, C=1.0),
            "use_scaled": True,
            "description": "Baseline linear classifier with L2 regularization",
        },
        "DecisionTree": {
            "model": DecisionTreeClassifier(max_depth=8, min_samples_split=4, random_state=RANDOM_STATE),
            "use_scaled": False,
            "description": "Interpretable tree classifier with depth bound",
        },
        "RandomForest": {
            "model": RandomForestClassifier(
                n_estimators=100, max_depth=12, min_samples_split=4, random_state=RANDOM_STATE, n_jobs=-1
            ),
            "use_scaled": False,
            "description": "Ensemble of bagging decision trees with feature sub-sampling",
        },
        "GradientBoosting": {
            "model": GradientBoostingClassifier(
                n_estimators=100, learning_rate=0.1, max_depth=5, random_state=RANDOM_STATE
            ),
            "use_scaled": False,
            "description": "Sequential boosting optimizing pseudo-residuals",
        },
        "ExtraTrees": {
            "model": ExtraTreesClassifier(
                n_estimators=100, max_depth=12, min_samples_split=4, random_state=RANDOM_STATE, n_jobs=-1
            ),
            "use_scaled": False,
            "description": "Extremely randomized trees ensemble for variance reduction",
        },
    }

    comparison_results: Dict[str, Any] = {}
    trained_artifacts: Dict[str, Any] = {}
    best_name: str = ""
    best_f1: float = -1.0
    best_model_obj: Any = None

    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    # 4. Train, Cross-Validate, and Test Each Candidate
    for name, config in candidates.items():
        logger.info("--- Evaluating candidate: %s ---", name)
        clf = config["model"]
        x_tr = X_train_scaled if config["use_scaled"] else X_train
        x_te = X_test_scaled if config["use_scaled"] else X_test

        # 5-Fold Stratified Cross Validation on Train Set
        t0_train = time.perf_counter()
        cv_scores = cross_val_score(clf, x_tr, y_train, cv=skf, scoring="f1")
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))

        # Fit model on full training set
        clf.fit(x_tr, y_train)
        fit_time_ms = round((time.perf_counter() - t0_train) * 1000, 2)
        trained_artifacts[name] = clf

        # Evaluate on Held-Out Test Set
        t0_infer = time.perf_counter()
        y_pred = clf.predict(x_te)
        infer_time_ms = round((time.perf_counter() - t0_infer) * 1000, 2)

        if hasattr(clf, "predict_proba"):
            y_proba = clf.predict_proba(x_te)[:, 1]
            roc_auc = round(float(roc_auc_score(y_test, y_proba)), 4)
        else:
            roc_auc = 0.0

        acc = round(float(accuracy_score(y_test, y_pred)), 4)
        prec = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
        rec = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
        f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)

        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

        # False Positive Rate (FPR) = FP / (FP + TN)
        fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
        # False Negative Rate (FNR) = FN / (FN + TP)  [Critical for security: missed phishing attacks]
        fnr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0

        metrics = {
            "algorithm": name,
            "description": config["description"],
            "cv_f1_mean": round(cv_mean, 4),
            "cv_f1_std": round(cv_std, 4),
            "test_accuracy": acc,
            "test_precision": prec,
            "test_recall": rec,
            "test_f1": f1,
            "test_roc_auc": roc_auc,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "confusion_matrix": {
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "true_positives": tp,
            },
            "fit_time_ms": fit_time_ms,
            "infer_time_ms": infer_time_ms,
        }
        comparison_results[name] = metrics
        logger.info(
            "[%s] Acc: %.4f | Prec: %.4f | Rec: %.4f | F1: %.4f | AUC: %.4f | FNR: %.4f | FPR: %.4f",
            name, acc, prec, rec, f1, roc_auc, fnr, fpr
        )

        # Champion selection: prioritize F1 score with lowest False Negative Rate
        if f1 > best_f1 or (f1 == best_f1 and fnr < comparison_results.get(best_name, {}).get("false_negative_rate", 1.0)):
            best_f1 = f1
            best_name = name
            best_model_obj = clf

    logger.info("=== CHAMPION MODEL SELECTED: %s (F1: %.4f) ===", best_name, best_f1)

    # 5. Extract Feature Importances for Champion (or tree models)
    feature_importances: Dict[str, float] = {}
    if hasattr(best_model_obj, "feature_importances_"):
        raw_importances = best_model_obj.feature_importances_
        feature_importances = {
            FEATURE_NAMES_V2[i]: round(float(raw_importances[i]), 4)
            for i in np.argsort(-raw_importances)
        }
    elif hasattr(best_model_obj, "coef_"):
        raw_coefs = np.abs(best_model_obj.coef_[0])
        feature_importances = {
            FEATURE_NAMES_V2[i]: round(float(raw_coefs[i]), 4)
            for i in np.argsort(-raw_coefs)
        }

    # 6. Save Versioned Model Artifacts
    champion_metrics = comparison_results[best_name]
    
    # Save active champion model
    joblib.dump(best_model_obj, MODEL_PATH)
    # Also overwrite standard legacy path so production inference service picks it up immediately
    joblib.dump(best_model_obj, LEGACY_MODEL_PATH)
    logger.info("Saved champion model to %s and %s", MODEL_PATH, LEGACY_MODEL_PATH)

    # Save candidate models for rollback & comparative inspection
    joblib.dump(trained_artifacts, CANDIDATE_MODELS_PATH)
    logger.info("Saved candidate model ensemble to %s", CANDIDATE_MODELS_PATH)

    # Save model metadata
    metadata = {
        "model_version": MODEL_VERSION,
        "selected_algorithm": best_name,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_count": len(FEATURE_NAMES_V2),
        "feature_names": FEATURE_NAMES_V2,
        "dataset_metadata": {
            "total_samples": total_samples,
            "legitimate_samples": n_legitimate,
            "phishing_samples": n_phishing,
            "train_samples": len(y_train),
            "test_samples": len(y_test),
            "test_split_ratio": TEST_SIZE,
            "random_state": RANDOM_STATE,
        },
        "top_features": dict(list(feature_importances.items())[:15]),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Save metrics
    metrics_summary = {
        "model_version": MODEL_VERSION,
        "selected_algorithm": best_name,
        "accuracy": champion_metrics["test_accuracy"],
        "precision": champion_metrics["test_precision"],
        "recall": champion_metrics["test_recall"],
        "f1_score": champion_metrics["test_f1"],
        "roc_auc": champion_metrics["test_roc_auc"],
        "false_positive_rate": champion_metrics["false_positive_rate"],
        "false_negative_rate": champion_metrics["false_negative_rate"],
        "cv_f1_mean": champion_metrics["cv_f1_mean"],
        "cv_f1_std": champion_metrics["cv_f1_std"],
        "confusion_matrix": champion_metrics["confusion_matrix"],
        "test_samples": len(y_test),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Save comparison report
    with open(COMPARISON_PATH, "w", encoding="utf-8") as f:
        json.dump(comparison_results, f, indent=2)

    # Save feature importances
    with open(IMPORTANCE_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_importances, f, indent=2)

    duration_s = round(time.perf_counter() - t_start, 2)
    logger.info("Multi-model training and evaluation pipeline completed in %.2fs", duration_s)

    return {
        "champion": best_name,
        "champion_metrics": champion_metrics,
        "comparison": comparison_results,
        "metadata": metadata,
        "duration_seconds": duration_s,
    }


if __name__ == "__main__":
    train_and_evaluate_models()
