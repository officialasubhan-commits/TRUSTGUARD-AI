# TrustGuard AI — Machine Learning Model Evaluation Report

**Evaluation Date**: 2026-11-08  
**Feature Schema**: Version 2.0.0 (30 Numerical Features)  
**Total Dataset**: 1,636 Verified URLs (1,070 Legitimate, 566 Phishing)  
**Train / Test Split**: 1,308 Train / 328 Held-Out Test (80/20 Stratified)  
**Champion Model**: Gradient Boosting (`backend/ml/models/phishing_rf_v2.joblib`)

---

## 1. Comparative Algorithm Benchmark

All models were evaluated using 5-Fold Stratified Cross-Validation on the training set and scored on the identical held-out test split of 328 samples (215 Legitimate, 113 Phishing).

| Metric | Logistic Regression | Decision Tree | Random Forest | Gradient Boosting (Champion) | Extra Trees |
|---|:---:|:---:|:---:|:---:|:---:|
| **5-Fold CV F1 (Mean $\pm$ Std)** | $0.9752 \pm 0.0078$ | $0.9708 \pm 0.0122$ | $0.9811 \pm 0.0058$ | **$0.9775 \pm 0.0096$** | $0.9730 \pm 0.0042$ |
| **Held-Out Test Accuracy** | 97.56% | 96.95% | 97.56% | **98.48%** | 97.26% |
| **Test Precision** | 100.00% | 99.05% | 99.07% | **100.00%** | 100.00% |
| **Test Recall** | 92.92% | 92.04% | 93.81% | **95.58%** | 92.04% |
| **Test F1 Score** | 0.9633 | 0.9541 | 0.9636 | **0.9774** | 0.9585 |
| **ROC-AUC Score** | 0.9873 | 0.9681 | 0.9968 | **0.9981** | 0.9972 |
| **False Positive Rate (FPR)** | 0.0000 | 0.0047 | 0.0047 | **0.0000** | 0.0000 |
| **False Negative Rate (FNR)** | 0.0708 | 0.0796 | 0.0619 | **0.0442** | 0.0796 |
| **Fit Latency (ms)** | 43.32 ms | 43.11 ms | 1,176.18 ms | 2,494.87 ms | 899.63 ms |
| **Inference Latency / Sample (ms)** | 0.20 ms | 0.25 ms | 35.90 ms | **1.45 ms** | 26.63 ms |

---

## 2. Confusion Matrices Breakdown (Held-Out Test Set: $N=328$)

### Gradient Boosting (Champion)
- **True Negatives (TN)**: 215 / 215 (100.0% clean rate)
- **False Positives (FP)**: **0 / 215 (0.00% false alarm rate)**
- **False Negatives (FN)**: 5 / 113 (4.42% miss rate)
- **True Positives (TP)**: 108 / 113 (95.58% detection rate)

$$\begin{pmatrix} \text{TN} = 215 & \text{FP} = 0 \\ \text{FN} = 5 & \text{TP} = 108 \end{pmatrix}$$

### Random Forest
$$\begin{pmatrix} \text{TN} = 214 & \text{FP} = 1 \\ \text{FN} = 7 & \text{TP} = 106 \end{pmatrix}$$

### Logistic Regression
$$\begin{pmatrix} \text{TN} = 215 & \text{FP} = 0 \\ \text{FN} = 8 & \text{TP} = 105 \end{pmatrix}$$

### Extra Trees
$$\begin{pmatrix} \text{TN} = 215 & \text{FP} = 0 \\ \text{FN} = 9 & \text{TP} = 104 \end{pmatrix}$$

### Decision Tree
$$\begin{pmatrix} \text{TN} = 214 & \text{FP} = 1 \\ \text{FN} = 9 & \text{TP} = 104 \end{pmatrix}$$

---

## 3. Champion Model Selection Rationale

Gradient Boosting was selected as the production champion because:
1. **Zero False Positives ($\text{FPR} = 0.00\%$)**: In security assessment, false positive accusations against legitimate domains ruin trust and brand reputation. Gradient Boosting yielded 0 false positives across all 215 held-out legitimate test domains.
2. **Superior F1 and ROC-AUC**: Attained **0.9774 F1 Score** and **0.9981 ROC-AUC**, outperforming Random Forest (0.9636 F1) and Logistic Regression (0.9633 F1).
3. **Lowest False Negative Rate**: Detected 108 of 113 phishing attacks ($\text{Recall} = 95.58\%$, $\text{FNR} = 4.42\%$), missing fewer attacks than all 4 alternatives.
4. **Fast Inference Latency**: At **1.45 ms per sample**, Gradient Boosting is 25x faster than Random Forest (35.90 ms), ensuring instantaneous response times in user browser sessions.

---

## 4. Top Feature Importances (Gini / MDI)

The table below details the top predictive features identified by the Gradient Boosting champion model:

| Rank | Feature Name | Importance Weight | Cumulative Contribution | Interpretation |
|:---:|--------------|:----------------:|:-----------------------:|----------------|
| 1 | `special_char_count` | 63.75% | 63.75% | Phishing URLs use heavy delimiter and parameter tokenization |
| 2 | `hostname_entropy` | 12.76% | 76.51% | High Shannon entropy differentiates DGA / randomized domains |
| 3 | `digit_count` | 10.78% | 87.29% | Elevated numeric frequency from session tokens and IP representations |
| 4 | `uses_https` | 6.28% | 93.57% | Scheme security boundary |
| 5 | `vowel_consonant_ratio` | 1.42% | 94.99% | Phonetic unnaturalness in machine-generated phishing domains |
| 6 | `has_suspicious_tld` | 1.32% | 96.31% | High abuse registrar concentration (.xyz, .top, .club) |
| 7 | `digit_letter_ratio` | 1.07% | 97.38% | Lexical density of digits vs natural language letters |
| 8 | `url_entropy` | 0.71% | 98.09% | Information density of overall target URL string |
| 9 | `url_length` | 0.47% | 98.56% | Total URL character length |
| 10 | `subdomain_count` | 0.32% | 98.88% | Subdomain nesting depth |
