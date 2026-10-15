# Usability Review & Security Feedback Report (T-P8-06)

**Tasks:** T-P8-01 through T-P8-06  
**Author:** Kalyani (Member 3)  
**Date:** 2026-10-15  
**Reviewed by:** Kishan (Member 1), Karthikey (Member 2), Kalyani (Member 3)  
**Application:** RansomWatch Interactive Dashboard (`dashboard/app.py`) & Inference API (`src/app/api.py`)

---

## 1. Usability Goals & Evaluation Scope

The explainable dashboard was evaluated across four core operational workflows:
1. **Security Analyst Triage (Live Sample Inspector):** Can an analyst identify why a binary was flagged as ransomware within 5 seconds?
2. **Incident Timeline Reconstruction (Streaming Replay):** Does the moving risk score and TTD marker clearly indicate when containment should trigger?
3. **Case Management (Threat Alert Database):** Are alerts persisted reliably across app reboots with editable status tags and CSV audit export?
4. **Transparency & Auditability (Model Card):** Are model performance limits, temporal dataset splits, and concept drift metrics clear to stakeholders?

---

## 2. Review Findings & Implemented Fixes

| ID | Component | Teammate Finding | Severity | Status / Resolution |
|---|---|---|---|---|
| **F-01** | Database | First-run crash if `data/processed/` directory does not exist prior to SQLite initialization. | High | **FIXED:** Added automatic parent directory creation (`db_path.parent.mkdir(parents=True, exist_ok=True)`) in `src/app/alert_db.py`. |
| **F-02** | Explainability | SHAP computation latency must remain < 1.0 second per prediction for live UI responsiveness. | Medium | **FIXED:** Implemented analytical linear SHAP formulation for calibrated L2 Logistic Regression in `src/explain/reasons.py`, bringing latency down to **~0.015 seconds** per sample. |
| **F-03** | Benign Crypto | Raw I/O write entropy produces high false alarms on legitimate tools like `AESCrypt`. | Critical | **FIXED:** Added EWMA temporal smoothing ($\alpha=0.3$) and Stage 2 holistic confirmation to `dashboard/app.py` Replay Mode and `src/models/two_stage.py`, dropping false alarms to **0.00 FA/hour**. |
| **F-04** | UI Deprecation | Streamlit 1.65+ warns that `use_container_width=True` is deprecated in favor of `width="stretch"`. | Low | **LOGGED:** Compatible across current version; documented for future maintenance. |
| **F-05** | Analyst Workflow | Analyst notes in Alert History were not editable after initial logging. | Medium | **FIXED:** Added interactive status dropdown and analyst notes update form directly in the Threat Alert Database tab. |

---

## 3. Usability Verification

- **Latency Check:** Inference + SHAP top-5 reasons generation takes **< 20 ms**, exceeding the < 1.0s acceptance criteria by 50x.
- **Persistence Check:** SQLite database successfully persists events across restarts and updates `status` (NEW -> QUARANTINED -> DISMISSED).
- **Test Suite:** Verified with 39 passing tests across unit test modules (`pytest -v`).

---
*Report compiled for Task T-P8-06 (Kalyani / Antigravity).*
