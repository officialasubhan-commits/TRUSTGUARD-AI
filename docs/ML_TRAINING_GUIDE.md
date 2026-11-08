# TrustGuard AI — ML Model Training & Retraining Guide

## 1. Overview & Pipeline Philosophy
The TrustGuard AI machine learning pipeline is an offline-trained, production-hardened binary classification system designed to distinguish legitimate web properties from phishing, credential-harvesting, and deceptive social-engineering URLs.

The training harness evaluates 5 candidate algorithms using 5-fold Stratified Cross-Validation on held-out test splits, prioritizing **False Positive Minimization** ($\text{FPR} = 0.00\%$) alongside high Recall ($\ge 95\%$) so legitimate businesses are never mistakenly blacklisted.

---

## 2. Dataset Composition & Sourcing

The training dataset is stored at `backend/ml/data/phishing_dataset.csv` and contains **1,636 verified samples**:
- **Legitimate Domains (`label = 0`)**: 1,070 verified benign domains sourced from the Tranco Top Sites registry, authoritative government/academic portals, and multi-vendor verified clean domains.
- **Phishing URLs (`label = 1`)**: 566 verified active attack samples sourced from PhishTank verified feeds, URLhaus, and open threat intelligence archives.

### Dataset Split Strategy
- **Split Ratio**: 80% Train ($N=1,308$), 20% Held-Out Test ($N=328$).
- **Stratification**: Enforced stratified distribution across classes (`random_state=42`).
- **Feature Extraction**: Exact 30-feature vector (Schema v2) generated deterministically via `URLAnalyzer` and `MLFeatureAdapter`.

---

## 3. Training Script & Execution

The training harness is located at `backend/scripts/train_phishing_models.py`.

### How to Execute the Training Pipeline
Run the training script from the project root:

```powershell
python backend/scripts/train_phishing_models.py
```

### Script Execution Workflow
1. **Load Data**: Ingests `phishing_dataset.csv`, validates columns (`url`, `label`), and removes duplicate URLs.
2. **Feature Extraction**: Computes 30 structural, entropy, and character ratio features for each record.
3. **Stratified Split**: Splits dataset into 1,308 training and 328 testing records.
4. **Candidate Model Evaluation**: Trains and benchmarks 5 algorithms:
   - Logistic Regression (L2 regularized baseline)
   - Decision Tree (Bounded depth)
   - Random Forest (100 estimators, bagging ensemble)
   - Gradient Boosting (Champion: sequential pseudo-residual optimization)
   - Extra Trees (Extremely randomized tree ensemble)
5. **Cross-Validation**: Computes 5-fold Stratified CV F1 score ($\mu \pm \sigma$) for each model.
6. **Held-Out Test Scoring**: Evaluates Accuracy, Precision, Recall, F1, ROC-AUC, FPR, and FNR.
7. **Champion Selection**: Selects model optimizing $F_1 = 2 \cdot \frac{P \cdot R}{P + R}$ subject to $\text{FPR} \le 0.01$.
8. **Artifact Serialization**:
   - Champion model: `backend/ml/models/phishing_rf_v2.joblib` and `phishing_rf_v1.joblib`
   - All candidate models: `backend/ml/models/candidate_models.joblib`
   - Evaluation metrics: `backend/ml/models/metrics.json`
   - Feature importances: `backend/ml/models/feature_importance.json`
   - Model metadata: `backend/ml/models/model_metadata.json`
   - Full model comparison: `backend/ml/models/model_comparison.json`

---

## 4. Controlled Continuous Learning & Retraining Safeguards

To prevent **Model Poisoning** and **Adversarial Concept Drift**, TrustGuard AI enforces a **Controlled Continuous Learning Gatekeeper** (`ContinuousLearningService`):

### 4.1 Strict Provenance Validation
Unverified end-user feedback is strictly segregated. Incoming URL submissions must pass provenance gating:
1. `MODERATOR_VERIFIED_REPORT`: Verified by a human security analyst.
2. `VIRUSTOTAL_CONFIRMED_THREAT`: Confirmed by $\ge 5$ independent security vendors.
3. `ADMINISTRATOR_CORRECTION`: Root administrator verified ground-truth label.

### 4.2 Promotion Criteria (Gatekeeper)
A newly retrained candidate model is **promoted to production** if and only if it satisfies all of the following:
1. **Test F1 Score**: $\ge 0.9500$.
2. **False Positive Rate (FPR)**: $\le 0.0100$ ($1.0\%$).
3. **Test Accuracy**: $\ge 0.9600$.
4. **Non-Regression Rule**: Candidate F1 must meet or exceed active production model within 0.5% margin.

### 4.3 Rollback Mechanism
Previous production model artifacts are archived to `backend/ml/archive/models/` with timestamped checksums. If production telemetry detects anomaly spikes, `ContinuousLearningService.rollback_model()` immediately restores the prior champion artifact without downtime.

