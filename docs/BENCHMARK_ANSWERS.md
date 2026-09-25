# Benchmark Evaluation Case Answers (HHG-001 to HHG-020)

## 1. Overview

The 20 benchmark evaluation cases from `case_pack.csv` were processed autonomously through the complete TigerGraph GraphRAG and ReAct Agent pipeline.

All 20 individual submission answer files are stored in [`answers/`](file:///d:/HHGOA-Fraud-Agent/answers/) in standard JSON format:
- `answers/HHG-001.json` through `answers/HHG-020.json`

---

## 2. Benchmark Cases Summary Table

| Case ID | Flagged Txn | Customer | Card | Amount | Trigger | Detected Pattern | Verdict | Approval | NBA | SAR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HHG-001** | 3514030 | C12382 | C12382-K1 | $77.07 | Risk Score (0.61) | `out_of_region_use` | `uncertain` | `L1_analyst` | `VERIFY_WITH_CUSTOMER` | No |
| **HHG-002** | 3478782 | C11891 | C11891-K1 | $292.36 | Risk Score (0.79) | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-003** | 3530164 | C08623 | C08623-K2 | $49.00 | Customer Report | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-004** | 3583227 | C08106 | C08106-K1 | $128.33 | Customer Report | `card_not_present_new_device` | `uncertain` | `L1_analyst` | `STEP_UP_AUTH` | No |
| **HHG-005** | 3523199 | C02923 | C02923-K1 | $100.07 | Risk Score (0.54) | `card_not_present_new_device` | `uncertain` | `L1_analyst` | `STEP_UP_AUTH` | No |
| **HHG-006** | 3476682 | C07297 | C07297-K1 | $482.12 | Customer Report | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-007** | 3514948 | C09933 | C09933-K2 | $111.92 | Risk Score (0.87) | `out_of_region_use` | `uncertain` | `L1_analyst` | `VERIFY_WITH_CUSTOMER` | No |
| **HHG-008** | 3558054 | C13171 | C13171-K2 | $55.68 | Customer Report | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-009** | 3581141 | C08299 | C08299-K1 | $30.02 | Customer Report | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-010** | 3506725 | C10434 | C10434-K1 | $1,000.03 | Risk Score (0.90) | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-011** | 3583368 | C11923 | C11923-K2 | $131.30 | Customer Report | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-012** | 3553342 | C05876 | C05876-K2 | $30.91 | Risk Score (0.55) | `out_of_region_use` | `uncertain` | `L1_analyst` | `VERIFY_WITH_CUSTOMER` | No |
| **HHG-013** | 3526826 | C07671 | C07671-K2 | $35.66 | Risk Score (0.76) | `card_not_present_new_device` | `uncertain` | `L1_analyst` | `STEP_UP_AUTH` | No |
| **HHG-014** | 3478561 | C13487 | C13487-K1 | $74.96 | Analyst Request | `undocumented` (Syndicate) | `confirmed_fraud` | `L2_senior_manager` | `BLOCK_CARD` | **YES** |
| **HHG-015** | 3464869 | C03042 | C03042-K1 | $599.94 | Risk Score (0.77) | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-016** | 3534820 | C09988 | C09988-K1 | $59.67 | Customer Report | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-017** | 3450629 | C04570 | C04570-K1 | $100.09 | Risk Score (0.57) | `card_not_present_new_device` | `uncertain` | `L1_analyst` | `STEP_UP_AUTH` | No |
| **HHG-018** | 3491361 | C02354 | C02354-K2 | $39.08 | Customer Report | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-019** | 3503878 | C07987 | C07987-K2 | $99.92 | Risk Score (0.90) | `card_not_present_fraud` | `confirmed_fraud` | `L1_analyst` | `BLOCK_CARD` | No |
| **HHG-020** | 3509359 | C12265 | C12265-K2 | $125.08 | Risk Score (0.52) | `card_not_present_new_device` | `uncertain` | `L1_analyst` | `STEP_UP_AUTH` | No |

---

## 3. Schema Compliance & Validation

Every generated answer JSON contains:
- Complete entity references (`case_id`, `flagged_txn_id`, `customer_id`, `card_id`).
- Quantified confidence score & financial exposure.
- Specific policy rule citations (`triggered_rules`).
- Grounded evidence claims with query sources and entity IDs.
- Full multi-step operational containment playbook.
- FinCEN-compliant SAR narrative where required.
