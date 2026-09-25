# Fraud Pattern Detection Specifications & Typology Architecture

**Project:** TigerGraph Agentic Fraud Investigation (HHGOA IEEE-CIS)  
**Document Version:** 1.0  
**Implementation:** [`scripts/pattern_detector.py`](file:///d:/HHGOA-Fraud-Agent/scripts/pattern_detector.py)  

---

## 1. Fraud Typologies Overview

The Fraud Pattern Detection Engine processes graph signals from GSQL queries to classify activity into 7 canonical categories:

```
                          ┌──────────────────────────┐
                          │ Graph Query Signals      │
                          │ (GSQL Investigation Set) │
                          └─────────────┬────────────┘
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                      ▼
        [1. Card Testing]    [2. Device Syndicate]    [3. Out-of-Region]
        - 3+ sub-$5 auths    - Shared DeviceProfile   - In-person shift
        - < 1 hour window    - Anonymous Proxy Ring   - Home baseline check
        - Followed by > $5   - Multi-card links       - Single clone alert
                 │                      │                      │
                 └──────────────────────┼──────────────────────┘
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                      ▼
        [4. CNP New Device]     [5. General CNP]       [6. Legitimate]
        - Online channel       - Anomalous spend      - Matches baseline
        - id_15 = 'New'        - Baseline deviation   - Travel confirmed
        - Untrusted device     - Velocity spike       - Recurring charge
```

---

## 2. Detailed Typology Specifications

### Typology 1: `card_testing` (Policy R5)
* **Definition:** Stolen payment credentials verified via micro-authorizations prior to large fraud purchases.
* **Graph Signature:** $\ge 3$ online authorizations with `amount < 5.00` within $\le 60$ minutes, followed by a transaction $\ge 5.00$.
* **Probability Rating:** $0.85$
* **Required Next Actions:** `DECLINE_TRANSACTION`, `STEP_UP_AUTH` (or `BLOCK_CARD` if $> \$100$ cleared).

### Typology 2: `undocumented` (Policy R6, R9)
* **Definition:** Coordinated multi-card syndicates operating through shared hardware profiles and anonymous proxies.
* **Graph Signature:** $\ge 3$ distinct payment cards across $\ge 3$ distinct customers sharing an identical `DeviceProfile`, flagged by `id_23` (anonymous proxy) or linked to historical proxy fraud cases (`CC-2649`, `CC-2971`, etc.).
* **Probability Rating:** $0.88$
* **Required Next Actions:** `CREATE_CASE`, `FILE_REPORT`, `ESCALATE_TO_ANALYST`, `MONITOR_CONNECTED_CARDS`.

### Typology 3: `out_of_region_use` (Policy R2, R3)
* **Definition:** In-person card cloning or physical card theft used in an unfamiliar geographical region.
* **Graph Signature:** `channel == 'in_person'` with `addr1` differing from historical dominant `home_region` ($\le 2$ transactions in current region vs $\ge 10$ in home region).
* **Probability Rating:** $0.75$
* **Required Next Actions:** `VERIFY_WITH_CUSTOMER` (if single signal) or `BLOCK_CARD` + `CREATE_CASE` (if customer denies).

### Typology 4: `card_not_present_new_device`
* **Definition:** Unauthorized online purchase from an unrecognized device.
* **Graph Signature:** `channel == 'online'` with `id_15 == 'New'` or device not in customer baseline.
* **Probability Rating:** $0.65$ (reflects inherent uncertainty of legitimate phone upgrades).
* **Required Next Actions:** `VERIFY_WITH_CUSTOMER`, `STEP_UP_AUTH`.

### Typology 5: `card_not_present_fraud`
* **Definition:** Stolen card details used online without cardholder authorization.
* **Graph Signature:** `channel == 'online'` with amount significantly deviating from historical average.
* **Probability Rating:** $0.55 - 0.72$
* **Required Next Actions:** `VERIFY_WITH_CUSTOMER`, `STEP_UP_AUTH`.

### Typology 6: `none` (Legitimate Baseline)
* **Definition:** False alarm triggered by detection model risk scores.
* **Graph Signature:** Transaction conforms to historical spend averages, trusted device profiles, and dominant billing regions.
* **Probability Rating:** $0.10$
* **Required Next Actions:** `CLOSE_NO_FRAUD`, `ALLOW_TRANSACTION`.
