# Next Best Action (NBA) Decision Engine & Playbooks

## 1. Overview

The **Next Best Action (NBA) Decision Engine** (`scripts/nba_engine.py`) translates complex graph findings, typology classifications, and Fraud Policy v1.0 governance rules into concrete, multi-stage operational playbooks.

---

## 2. Playbook Structure

Every generated playbook provides structured, actionable instructions across 5 dimensions:
1. **Primary Action:** Immediate operational decision (`BLOCK_CARD`, `BLOCK_ALL_LINKED_CARDS_AND_FILE_SAR`, `VERIFY_WITH_CUSTOMER`, `STEP_UP_AUTH`, `CLOSE_NO_FRAUD`).
2. **Containment Steps:** Real-time defensive actions (e.g. freezing linked cards, blacklisting device hardware fingerprints, terminating active banking sessions).
3. **Customer Communication:** Ready-to-dispatch SMS, push notification, or call-center copy tailored to the case.
4. **Financial Remediation:** Chargeback processing, fee reversals, and provisional credit instructions.
5. **Compliance & Governance:** SAR narrative filing requirements, approval routing (`auto`, `L1_analyst`, `L2_senior_manager`), and SLA deadlines.

---

## 3. Operational Playbook Matrix

| Fraud Signature | Approval Level | Resolution SLA | Primary Action | Key Containment & Governance |
| :--- | :--- | :--- | :--- | :--- |
| **Shared Device Proxy Syndicate** | `L2_senior_manager` | 24 Hours | `BLOCK_ALL_LINKED_CARDS_AND_FILE_SAR` | Multi-card freeze, device blacklisting, FinCEN SAR filing |
| **Card Testing Velocity Burst** | `auto` | 1 Hour | `BLOCK_CARD` | Automated instant card block, merchant terminal block |
| **Out-of-Region In-Person** | `L1_analyst` | 2 Hours | `VERIFY_WITH_CUSTOMER` | Temporary hold, 2-way SMS travel verification prompt |
| **CNP New Device Login** | `L1_analyst` | 1 Hour | `STEP_UP_AUTH` | In-app biometric / push OTP challenge |
| **Standard CNP Deviation** | `L1_analyst` | 4 Hours | `BLOCK_CARD` | Hard block, chargeback filing, card reissue |
| **Baseline Legitimate Activity** | `auto` | 1 Hour | `CLOSE_NO_FRAUD` | Release holds, update behavioral baseline in TigerGraph |

---

## 4. Verification & Testing

Tested in `tests/test_nba_engine.py`:
- Playbook generation across all 6 operational branches.
- Verification of containment steps, customer copy, and compliance actions.
