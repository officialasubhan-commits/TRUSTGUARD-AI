"""
TrustGuard AI — Controlled Continuous Learning & Model Promotion Engine.

Implements a secure, anti-poisoning feedback ingestion and model improvement pipeline:
1. Strict Provenance Requirement: Only validated moderator findings, confirmed
   VirusTotal threat reports, and admin corrections are ingested. Unverified user
   claims are strictly rejected.
2. Deduplication & Sanitization: Checks against existing training datasets.
3. Promotion Gatekeeper: Retrained candidate models must pass evaluation against
   the incumbent production model before promotion.
4. Safe Rollback: Previous models are archived and instantly restorable.
"""
from __future__ import annotations

import csv
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import joblib

from app.services.ml_feature_adapter import FEATURE_NAMES_V2, extract_feature_vector
from app.services.url_analyzer import URLAnalyzer
from app.utils.url_normalizer import compute_url_hash, normalize_url

logger = logging.getLogger("trustguard.service.continuous_learning")

LabelProvenance = Literal[
    "MODERATOR_VERIFIED_REPORT",
    "VIRUSTOTAL_CONFIRMED_THREAT",
    "ADMINISTRATOR_CORRECTION",
    "BENCHMARK_SEED",
]

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "ml" / "data" / "phishing_dataset.csv"
FEEDBACK_QUEUE_PATH = BASE_DIR / "ml" / "data" / "verified_feedback_queue.jsonl"
MODEL_DIR = BASE_DIR / "ml" / "models"
ACTIVE_MODEL_PATH = MODEL_DIR / "phishing_rf_v2.joblib"
ROLLBACK_DIR = MODEL_DIR / "rollback_archive"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
METRICS_PATH = MODEL_DIR / "metrics.json"


class ContinuousLearningService:
    """Manages verified dataset expansion, model promotion gates, and safe rollbacks."""

    def __init__(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)

    def ingest_verified_sample(
        self,
        raw_url: str,
        label: int,
        provenance: LabelProvenance,
        verified_by: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingests a verified URL sample into the quarantined feedback queue.
        Enforces strict provenance, rejects unverified labels, and normalizes URLs.
        """
        if label not in (0, 1):
            raise ValueError("Label must be 0 (legitimate) or 1 (phishing).")

        # 1. Anti-Poisoning Check: Validate provenance
        allowed_provenance = (
            "MODERATOR_VERIFIED_REPORT",
            "VIRUSTOTAL_CONFIRMED_THREAT",
            "ADMINISTRATOR_CORRECTION",
            "BENCHMARK_SEED",
        )
        if provenance not in allowed_provenance:
            raise PermissionError(
                f"Unauthorized label provenance '{provenance}'. Unverified user labels are rejected to prevent model poisoning."
            )

        # 2. URL Normalization
        canonical_url = normalize_url(raw_url)
        url_hash = compute_url_hash(canonical_url)

        # 3. Deduplication against main dataset
        if self._is_already_in_dataset(canonical_url):
            return {
                "status": "DUPLICATE_IGNORED",
                "message": f"URL '{canonical_url}' is already present in the active training dataset.",
                "url": canonical_url,
            }

        # 4. Append to quarantined feedback queue with provenance metadata
        entry = {
            "url": canonical_url,
            "url_hash": url_hash,
            "label": label,
            "provenance": provenance,
            "verified_by": verified_by,
            "notes": notes or "",
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(FEEDBACK_QUEUE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        logger.info(
            "Ingested verified sample (%s, label=%d) into feedback queue with provenance '%s'.",
            canonical_url, label, provenance
        )

        return {
            "status": "QUEUED_FOR_RETRAINING",
            "message": "Verified sample successfully queued with complete audit provenance.",
            "url": canonical_url,
            "provenance": provenance,
        }

    def _is_already_in_dataset(self, canonical_url: str) -> bool:
        """Checks if a canonical URL already exists in the primary training dataset."""
        if not DATA_PATH.exists():
            return False

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("url", "").strip() == canonical_url:
                    return True
        return False

    def merge_feedback_into_dataset(self) -> int:
        """
        Merges queued verified samples into the primary training dataset.
        Returns the count of new unique samples merged.
        """
        if not FEEDBACK_QUEUE_PATH.exists():
            return 0

        queued_entries: List[Dict[str, Any]] = []
        with open(FEEDBACK_QUEUE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        queued_entries.append(json.loads(line))
                    except Exception:
                        continue

        if not queued_entries:
            return 0

        existing_urls = set()
        if DATA_PATH.exists():
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    existing_urls.add(r.get("url", "").strip())

        new_count = 0
        with open(DATA_PATH, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for entry in queued_entries:
                u = entry["url"]
                if u not in existing_urls:
                    writer.writerow([u, entry["label"]])
                    existing_urls.add(u)
                    new_count += 1

        # Clear processed queue
        FEEDBACK_QUEUE_PATH.unlink(missing_ok=True)
        logger.info("Merged %d new verified feedback records into %s", new_count, DATA_PATH)
        return new_count

    def evaluate_and_promote_model(
        self,
        candidate_model_path: Path,
        candidate_metrics: Dict[str, Any],
        candidate_version: str,
    ) -> Tuple[bool, str]:
        """
        Evaluates candidate model against current production model before promotion.
        Enforces strict safety criteria:
        1. F1 score must not degrade by more than 0.5%
        2. False Negative Rate must not increase by more than 1.0%
        3. Precision must remain >= 95%
        """
        if not ACTIVE_MODEL_PATH.exists():
            # First model: automatically promote
            self._archive_and_promote(candidate_model_path, candidate_version)
            return True, "Initial model promoted (no prior production baseline)."

        current_metrics = {}
        if METRICS_PATH.exists():
            try:
                with open(METRICS_PATH, "r", encoding="utf-8") as f:
                    current_metrics = json.load(f)
            except Exception:
                pass

        baseline_f1 = current_metrics.get("f1_score", 0.95)
        baseline_fnr = current_metrics.get("false_negative_rate", 0.05)

        cand_f1 = candidate_metrics.get("f1_score", 0.0)
        cand_fnr = candidate_metrics.get("false_negative_rate", 1.0)
        cand_prec = candidate_metrics.get("precision", 0.0)

        # Gate 1: Precision check (prevent false positives on legitimate sites)
        if cand_prec < 0.95:
            return False, f"Promotion Rejected: Candidate precision ({cand_prec:.2%}) is below safety threshold (95.0%)."

        # Gate 2: F1 degradation check
        if cand_f1 < (baseline_f1 - 0.005):
            return False, f"Promotion Rejected: Candidate F1 ({cand_f1:.4f}) degraded compared to baseline ({baseline_f1:.4f})."

        # Gate 3: False negative rate check (prevent undetected phishing)
        if cand_fnr > (baseline_fnr + 0.01):
            return False, f"Promotion Rejected: Candidate False Negative Rate ({cand_fnr:.2%}) is higher than baseline ({baseline_fnr:.2%})."

        # Gates passed: promote candidate and archive previous model
        self._archive_and_promote(candidate_model_path, candidate_version)
        return True, f"Promotion Approved: Candidate model {candidate_version} passed all benchmark gates."

    def _archive_and_promote(self, candidate_path: Path, new_version: str) -> None:
        """Archives current production model and promotes the candidate artifact."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if ACTIVE_MODEL_PATH.exists():
            archive_dest = ROLLBACK_DIR / f"phishing_model_archive_{timestamp}.joblib"
            shutil.copy2(ACTIVE_MODEL_PATH, archive_dest)
            logger.info("Archived prior production model to %s", archive_dest)

        shutil.copy2(candidate_path, ACTIVE_MODEL_PATH)
        # Also sync legacy path
        shutil.copy2(candidate_path, MODEL_DIR / "phishing_rf_v1.joblib")
        logger.info("Successfully promoted candidate model %s to active production.", new_version)

    def rollback_to_previous_model(self) -> Tuple[bool, str]:
        """Restores the most recent archived model from the rollback directory."""
        archives = sorted(ROLLBACK_DIR.glob("phishing_model_archive_*.joblib"))
        if not archives:
            return False, "No rollback model archives found in storage."

        latest_archive = archives[-1]
        shutil.copy2(latest_archive, ACTIVE_MODEL_PATH)
        shutil.copy2(latest_archive, MODEL_DIR / "phishing_rf_v1.joblib")
        logger.info("Rolled back production model from %s", latest_archive)
        return True, f"Successfully restored model from archive: {latest_archive.name}"
