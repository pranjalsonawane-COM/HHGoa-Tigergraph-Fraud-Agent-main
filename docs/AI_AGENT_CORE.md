# Autonomous AI Agent Core (ReAct State Machine)

## 1. Overview

The **Autonomous Fraud Investigation Agent** (`scripts/agent_core.py`) executes an 8-stage ReAct (Reasoning + Action) decision state machine to progress cases from initial alert ingestion to definitive next best action and FinCEN SAR filing.

---

## 2. ReAct State Machine Lifecycle

```
    ┌─────────────────────────┐
    │ 1. ALERT_INGESTION      │ ← Ingest alert, extract transaction, card & customer IDs
    └───────────┬─────────────┘
                ▼
    ┌─────────────────────────┐
    │ 2. GRAPH_TRAVERSAL      │ ← Multi-hop neighborhood traversal & device sharing check
    └───────────┬─────────────┘
                ▼
    ┌─────────────────────────┐
    │ 3. PATTERN_REASONING    │ ← Typology classifier (Syndicate, Testing, Out-of-Region, ATO)
    └───────────┬─────────────┘
                ▼
    ┌─────────────────────────┐
    │ 4. CASE_MEMORY_SEARCH   │ ← BM25 semantic precedent search with temporal anti-leakage
    └───────────┬─────────────┘
                ▼
    ┌─────────────────────────┐
    │ 5. POLICY_EVALUATION    │ ← Fraud Policy v1.0 (Rules R1-R10) & approval routing
    └───────────┬─────────────┘
                ▼
    ┌─────────────────────────┐
    │ 6. UNCERTAINTY & NBA    │ ← Formulate verdict & Next Best Action (auto, L1, L2)
    └───────────┬─────────────┘
                ▼
    ┌─────────────────────────┐
    │ 7. SAR_GENERATION       │ ← FinCEN-compliant SAR narrative (Who, What, Where, Why, How)
    └───────────┬─────────────┘
                ▼
    ┌─────────────────────────┐
    │ 8. RESOLUTION DOSSIER   │ ← Return grounded dossier & prepare TigerGraph writeback
    └─────────────────────────┘
```

---

## 3. Approval Routing & Next Best Action Matrix

| Case Type / Condition | Verdict | Approval Level | Next Best Action |
| :--- | :--- | :--- | :--- |
| **Card Testing Burst** | `confirmed_fraud` | `auto` | `BLOCK_CARD` |
| **Multi-Card Proxy Syndicate** | `confirmed_fraud` | `L2_senior_manager` | `BLOCK_CARD` + `FILE_SAR` |
| **Out-of-Region In-Person** | `uncertain` | `L1_analyst` | `VERIFY_WITH_CUSTOMER` |
| **CNP Unrecognized Device** | `uncertain` | `L1_analyst` | `STEP_UP_AUTH` |
| **Standard CNP Deviation** | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` |
| **Baseline Verified Activity** | `cleared` | `auto` | `CLOSE_NO_FRAUD` |

---

## 4. Verification & Testing

Tested in `tests/test_agent_core.py`:
- Full execution across multiple typologies.
- Verification of ReAct trace steps.
- FinCEN SAR narrative completeness.
