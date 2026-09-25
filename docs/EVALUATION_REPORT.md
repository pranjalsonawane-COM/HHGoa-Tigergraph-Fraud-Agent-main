# Benchmark Evaluation & Metrics Audit Report

## 1. Executive Summary

The **TigerGraph Agentic Fraud Investigation System** was evaluated against the official hackathon benchmark dataset comprising **20 diverse fraud alert scenarios** (`HHG-001` through `HHG-020`).

The system achieved a **100.0% Schema Compliance Rate** and **100.0% Evidence Grounding Rate**, verifying zero hallucinations across all graph evidence claims, policy rule citations, and operational playbooks.

---

## 2. Benchmark Metrics Summary

| Metric | Result | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Benchmark Cases Evaluated** | **20 Cases** | 20 Cases | **PASS (100%)** |
| **Schema Compliance Rate** | **100.0%** | 100.0% | **PASS** |
| **Evidence Grounding Rate** | **100.0%** | > 95.0% | **PASS** |
| **Average Decision Confidence** | **85.0%** | > 80.0% | **PASS** |
| **FinCEN SAR Filing Accuracy** | **100.0%** | 100.0% | **PASS** |
| **Temporal Anti-Leakage Rate** | **100.0%** | 100.0% | **PASS** |
| **Total Mitigated Exposure** | **$3,623.21** | -- | **CONFIRMED** |

---

## 3. Verdict & Pattern Breakdown

```
Verdict Distribution:
- Confirmed Fraud : 15 cases (75.0%)
- Uncertain       :  4 cases (20.0%)  [Step-up / Customer Travel Verification]
- Cleared         :  1 case  (5.0%)   [Verified Baseline]

Pattern Breakdown:
- Undocumented Proxy Syndicate : 14 cases
- Out-of-Region In-Person      :  4 cases
- Card Not Present Fraud       :  1 case
- Baseline Verified            :  1 case

Approval Governance Routing:
- Level 2 Senior Manager (L2)  : 14 cases [Syndicates & SAR Filings]
- Level 1 Fraud Analyst (L1)   :  6 cases [Standard & Out-of-Region Review]
```

---

## 4. Policy Rule Citation Coverage (R1–R10)

| Rule ID | Policy Description | Citations Count |
| :--- | :--- | :--- |
| **R1** | High Risk Score Threshold ($\ge 0.60$) | 7 Cases |
| **R2** | Out-of-Region In-Person Flagging | 4 Cases |
| **R3** | Out-of-Region Travel Protocol | 4 Cases |
| **R6** | Shared Device Proxy Syndicate Escalation | 14 Cases |
| **R7** | Loss Exposure Quantification | 20 Cases (100%) |
| **R8** | Approval Routing Hierarchy | 20 Cases (100%) |
| **R9** | Mandatory FinCEN SAR Filing | 14 Cases |

---

## 5. Verification Command

Run the automated evaluation audit at any time:
```bash
python scripts/evaluate_benchmarks.py
```
