# TigerGraph Agentic Fraud Investigation (HHGOA IEEE-CIS) — Comprehensive Dataset & Domain Analysis

**Document Version:** 1.0  
**Project:** TigerGraph Agentic Fraud Investigation Agent (Hacker House Goa 2026)  
**Dataset:** Modified IEEE-CIS Fraud Detection (Vesta Corporation) with Synthetic Graph Overlay  

---

## 1. Dataset Overview

The dataset provides a realistic six-month credit card transaction monitoring and fraud investigation environment (spanning **July 2, 2016 through December 31, 2016**). It is built on the IEEE-CIS Fraud Detection benchmark originally published by Vesta Corporation.

### Key Modifications & Additions
1. **Removal of Ground Truth Fraud Flags:** The traditional binary `isFraud` column has been completely removed from all transaction records. Transactions are no longer explicitly marked as fraud.
2. **Real-time Model Risk Score:** A synthetic bank model prediction score (`risk_score`, float from `0.00` to `1.00`) is attached to each transaction. As specified in the documentation, this score is an *input trigger* and **not an answer**; high scores often reflect legitimate transactions (e.g., traveling cardholders, luxury purchases, new phones), and low scores occasionally hide sophisticated fraud (e.g., low-velocity testing, undocumented proxy rings).
3. **Graph-Enabling Overlay:**
   - `customer_id`: Synthetically linked customer identifier (e.g., `C12382`), derived from card issuer relationships.
   - Real-world calendar timestamps (`ts`): Spanning 6 months (`YYYY-MM-DD HH:MM:SS`).
   - Transaction channel (`channel`): Categorized as `in_person` or `online`.
   - Card identifiers: Formatted as `<customer_id>-K<n>` (e.g., `C12382-K1`, `C08623-K2`), distinguishing card profiles/reissues for a customer.
4. **Investigation History & Case Memory:**
   - 5,565 closed historical investigation cases from the first four months (July to October 2016), recording human analyst notes, outcomes, fraud typologies, confirmed fraud transaction IDs, and regulatory filing statuses.
5. **Benchmark Evaluation Cases (Case Pack):**
   - Exactly 20 unclosed cases from November and December 2016 that serve as the blind evaluation benchmark for the hackathon.

---

## 2. File-by-File Analysis

### Summary Statistics

| File Name | File Size | Row Count | Column Count | Primary Keys / Identifiers | Temporal Span |
|---|---|---|---|---|---|
| `README.md` | 38.6 KB | 473 lines | N/A | Documentation & Policy Guide | N/A |
| `case_pack.csv` | 3.5 KB | 20 data rows | 8 columns | `case_id` (`HHG-001` to `HHG-020`) | 2016-11-12 to 2016-12-29 |
| `closed_cases_history.csv` | 2.7 MB | 5,565 data rows | 15 columns | `case_id` (`CC-0001` to `CC-5565`) | 2016-07-02 to 2016-11-02 |
| `identity.csv` | 26.7 MB | 144,432 data rows | 41 columns | `TransactionID` | Covers online transactions |
| `transactions.csv` | 707.9 MB | 590,742 data rows | 397 columns | `TransactionID` | 2016-07-02 to 2016-12-31 |

---

### Detailed File Profiles

#### A. `case_pack.csv`
- **Purpose:** Represents the 20 test cases provided to the agent for automated investigation and evaluation.
- **Rows:** 20 rows (excluding header).
- **Columns (8):** `case_id`, `opened_at`, `trigger_type`, `trigger_text`, `flagged_txn_id`, `card_id`, `customer_id`, `risk_score`.
- **Triggers Breakdown:**
  - `risk_score` (11 cases): Initiated by the bank's automated machine learning detection model scoring above typical thresholds (scores range from 0.52 to 0.90).
  - `customer_report` (8 cases): Initiated by explicit cardholder notification disputing a specific charge.
  - `analyst_request` (1 case: HHG-014): Triggered by a senior fraud analyst identifying cross-card suspicious device activity (`risk_score` is only 0.05).
- **Key Relationships:**
  - `flagged_txn_id` joins to `transactions.csv:TransactionID`.
  - `customer_id` joins to `transactions.csv:customer_id`.
  - `card_id` identifies the active payment card.

#### B. `closed_cases_history.csv`
- **Purpose:** Past case repository representing "Case Memory". Provides ground truth for previous investigations conducted by human analysts between July and October 2016.
- **Rows:** 5,565 rows.
- **Columns (15):** `case_id`, `customer_id`, `card_id`, `opened_at`, `closed_at`, `outcome`, `pattern`, `first_fraud_txn_id`, `txn_ids`, `n_txns`, `exposure_usd`, `connected_card_ids`, `actions_taken`, `report_filed`, `analyst_notes`.
- **Distribution of Outcomes:**
  - `confirmed_fraud`: 4,665 cases (83.8%)
  - `cleared` (legitimate/false alarm): 900 cases (16.2%)
- **Distribution of Patterns:**
  - `card_not_present_fraud`: 1,404 cases
  - `account_takeover`: 1,205 cases
  - `card_not_present_new_device`: 1,076 cases
  - `out_of_region_use`: 955 cases
  - `none` (cleared / false alarm): 900 cases
  - `card_testing`: 16 cases
  - `undocumented`: 9 cases (critical for discovering emerging coordination patterns)
- **Regulatory Reporting:**
  - `report_filed`: Yes in 397 cases; No in 5,168 cases.
- **Action Combinations:**
  - Confirmed fraud: `CREATE_CASE|BLOCK_CARD` (with optional `|FILE_REPORT`)
  - Cleared cases: `VERIFY_WITH_CUSTOMER|CLOSE_NO_FRAUD`
- **Key Relationships:**
  - `customer_id`, `card_id` connect to customer and card entities.
  - `txn_ids` is a pipe-delimited list linking to 14,955 historical transactions.
  - `connected_card_ids` links to coordinated fraud rings across cards.

#### C. `identity.csv`
- **Purpose:** Captures browser, operating system, network connection, hardware profile, and behavioral identity verification attributes for card-not-present (`online`) transactions.
- **Rows:** 144,432 rows (each corresponding to a single online transaction).
- **Columns (41):** `TransactionID`, `id_01` through `id_38`, `DeviceType`, `DeviceInfo`.
- **Key Features:**
  - `DeviceType`: `desktop` (85,204), `mobile` (55,801), missing (3,427).
  - `DeviceInfo`: 2,799 distinct device strings (e.g., `Windows`, `iOS Device`, `MacOS`, `Trident/7.0`, `SM-G935F Build/NRD90M`).
  - `id_15`: New vs. Found device status (`Found`: 67,773, `New`: 61,754, `Unknown`: 11,653).
  - `id_23`: Proxy IP detection (`IP_PROXY:TRANSPARENT`: 3,492, `IP_PROXY:ANONYMOUS`: 1,185, `IP_PROXY:HIDDEN`: 611).
  - `id_30`: Client Operating System (e.g., `Windows 10`, `Windows 7`, `iOS 11.2.1`, `Android 7.0`).
  - `id_31`: Browser client (e.g., `chrome 63.0`, `mobile safari 11.0`, `ie 11.0 for desktop`).
  - `id_33`: Screen resolution (e.g., `1920x1080`, `1366x768`, `2220x1080`).
  - `id_34`: Identity match rating (e.g., `match_status:2`, `match_status:1`).
  - `id_01` to `id_11`: Numeric telemetry signals (e.g., IP rating, risk indicators, time on page).

#### D. `transactions.csv`
- **Purpose:** Core transaction ledger containing all card authorization attempts across the 6-month period.
- **Rows:** 590,742 rows.
- **Columns (397):**
  - Identifiers & Core Metadata (3): `TransactionID`, `TransactionDT`, `TransactionAmt`
  - Transaction Channel & Classification (2): `ProductCD`, `channel` (`online`: 151,072, `in_person`: 439,670)
  - Card Metadata (6): `card1` (issuer/card series), `card2`, `card3`, `card4` (network: visa 384,887, mastercard 189,298, amex 8,328, discover 6,652), `card5`, `card6` (type: debit 440,091, credit 149,035)
  - Billing & Geography (4): `addr1` (billing region code, e.g., 264.0, 444.0), `addr2` (billing country code; 87.0 is domestic), `dist1`, `dist2`
  - Email Domains (2): `P_emaildomain` (purchaser email domain), `R_emaildomain` (recipient email domain)
  - Behavioral Counts (14): `C1` to `C14` (count of addresses/phones/authorizations associated with payment entity)
  - Time Deltas (15): `D1` to `D15` (days since previous transaction, registration, or card activity)
  - Match Flags (9): `M1` to `M9` (address match, name match, etc.)
  - Vesta Engineered Graph/Model Signals (339): `V1` to `V339` (anonymized historical counts, ranking, velocity metrics)
  - Synthetic Additions (4): `customer_id` (13,553 unique customers), `ts` (timestamp), `channel` (online/in_person), `risk_score` (model probability 0.00-1.00)

---

## 3. Column Analysis & TigerGraph Suitability

A critical graph engineering decision is determining which columns belong as **Graph Vertices**, which as **Graph Edges**, which as **Vertex/Edge Attributes**, and which should remain in external/tabular storage or GraphRAG feature context.

| Column / Feature Group | Source File | Data Type | Fraud Utility | Graph Role / Storage Recommendation | Rationale |
|---|---|---|---|---|---|
| `customer_id` | `transactions`, `case_pack`, `closed_cases` | String (e.g., `C12382`) | Essential | **Primary Vertex (`Customer`)** | Central anchor of card ownership and customer history. |
| `card_id` | `case_pack`, `closed_cases`, derived | String (e.g., `C12382-K1`) | Essential | **Primary Vertex (`Card`)** | Links customer to transactions; distinguishes card reissues and multi-card portfolios. |
| `TransactionID` | `transactions`, `identity` | String / Int (e.g., `3514030`) | Essential | **Primary Vertex (`Transaction`)** | Core event vertex connecting cards, devices, domains, and regions. |
| `ts` | `transactions` | Datetime (`YYYY-MM-DD HH:MM:SS`) | Essential | **Transaction Vertex Attribute & Edge Attribute** | Critical for time-window queries (e.g., card testing bursts, velocity). |
| `TransactionAmt` | `transactions` | Float (USD) | Essential | **Transaction Vertex Attribute** | Required for calculating exposure, testing thresholds, structuring detection. |
| `channel` | `transactions` | Enum (`in_person`, `online`) | High | **Transaction Vertex Attribute** | Distinguishes CNP from card-present; triggers out-of-region vs new device policies. |
| `ProductCD` | `transactions` | Enum (`W`, `C`, `R`, `H`, `S`) | High | **Transaction Vertex Attribute** | Product code `W` = in_person (card-present). `C`/`R`/`H`/`S` = online CNP transactions. |
| `risk_score` | `transactions`, `case_pack` | Float (0.0 to 1.0) | High | **Transaction Vertex Attribute** | Initial trigger score. Used in rule R1 to evaluate weak signals. |
| `card1` to `card6` | `transactions` | Mixed (Int, Float, String) | High | **Card Vertex Attributes** | `card4` (network) and `card6` (type) stored on `Card`. `card1..card3` define issuer specs. |
| `DeviceInfo`, `id_30`, `id_31`, `id_33` | `identity` | Strings | Critical | **Composite Vertex (`DeviceProfile`)** | Composite: `DeviceInfo \| id_30 \| id_31 \| id_33`. Unmasks shared fraud rings. |
| `id_15` | `identity` | Enum (`New`, `Found`, `Unknown`) | Critical | **Transaction or Edge Attribute** | Direct indicator for pattern 3 (`card_not_present_new_device`). |
| `id_23` | `identity` | String (e.g., `IP_PROXY:ANONYMOUS`) | High | **DeviceProfile or Edge Attribute** | Unmasks anonymized proxy operations in coordinated syndicates. |
| `addr1` | `transactions` | Float/String (e.g., `264.0`) | Critical | **Vertex (`BillingRegion`)** | Connects transactions geographically; detects pattern 4 (`out_of_region_use`). |
| `addr2` | `transactions` | Float/String (87.0 = home) | Medium | **BillingRegion Attribute** | Flags international transactions. |
| `P_emaildomain`, `R_emaildomain` | `transactions` | String (e.g., `gmail.com`) | High | **Vertex (`EmailDomain`)** | Identifies shared recipient email domains linking multiple cards. |
| `case_id` | `closed_cases`, `case_pack` | String (e.g., `CC-0001`) | Essential | **Vertex (`ClosedCase` / `Case`)** | Case memory entity storing analyst findings, verdicts, and SAR filings. |
| `analyst_notes`, `summary` | `closed_cases` | Text | Critical | **Vector Store / GraphRAG & Case Attribute** | Embedded for semantic vector retrieval of similar past investigations. |
| `C1` to `C14`, `D1` to `D15`, `M1` to `M9` | `transactions` | Float / String | Secondary | **Feature Store / Vertex Attributes (Key Subset)** | Useful for LLM context on match discrepancies and velocity deltas. |
| `V1` to `V339` | `transactions` | Float | Low in Graph | **Keep in Parquet/Tabular or omit from Graph** | 339 anonymized Vesta floats add massive graph memory overhead with minimal agent interpretability. |

---

## 4. Entity Relationships

Based strictly on the dataset structure and foreign key correspondences, the following entity relationships exist:

```
[ Customer ] (customer_id)
      │
      │ OWNS
      ▼
   [ Card ] (card_id: <customer_id>-K<n>)
      │
      │ MADE
      ▼
[ Transaction ] (TransactionID) ─── NEXT ───► [ Transaction ]
   │       │         │
   │       │         └─── BILLED_IN ──────► [ BillingRegion ] (addr1)
   │       │
   │       └───────────── FROM_DEVICE ────► [ DeviceProfile ] (DeviceInfo + OS + browser + screen)
   │
   └───────────────────── PURCHASER_EMAIL ─► [ EmailDomain ] (P_emaildomain)
                         RECIPIENT_EMAIL ─► [ EmailDomain ] (R_emaildomain)

[ ClosedCase ] (case_id)
   │
   ├─── INVOLVES ───────► [ Transaction ]
   ├─── ON_CARD ────────► [ Card ]
   └─── CONNECTED_TO ───► [ Card ]
```

### Relationship Constraints & Data Mechanics
1. **Customer to Card:**
   - One Customer holds one or more Cards.
   - 13,553 customers exist across 590,742 transactions.
   - Analysis confirms that in `closed_cases_history.csv`, 1,913 distinct `card_id` values appear. Card IDs use suffix `-K1`, `-K2`, `-K3`.
   - In `transactions.csv`, `card1` is 1-to-1 with `customer_id`. Sub-cards (reissues or multi-cards) are distinguished by `card2`..`card6` (e.g., `-K1` corresponds to transactions where specific secondary card issuer fields are blank, whereas `-K2` corresponds to secondary values populated, or different physical debit/credit profiles under the same customer).
2. **Card to Transaction:**
   - Every transaction is made by exactly one Card owned by one Customer.
   - Sequential edge `NEXT` chains transactions chronologically by `ts` within each Card, enabling sub-second traversal of card-testing velocities and burst windows.
3. **Transaction to Identity / DeviceProfile:**
   - Only `online` transactions (`ProductCD` ∈ {`C`, `R`, `H`, `S`}) join to `identity.csv`.
   - `in_person` transactions (`ProductCD` = `W`) have **no identity record**.
   - A `DeviceProfile` is formed by combining `DeviceInfo`, `id_30` (OS), `id_31` (browser), and `id_33` (screen resolution).
   - When multiple cards across different customers connect to the **same** `DeviceProfile`, this constitutes a multi-card fraud syndicate or credential stuffing ring.
4. **Transaction to BillingRegion:**
   - `addr1` represents the anonymized billing region code.
   - `addr2` represents the billing country code (87.0 is domestic).
   - Legitimate customers establish a dense history with 1-2 billing regions. Transactions in a new region while normal activity continues at home represent out-of-region fraud or legitimate travel.
5. **ClosedCase to Entities:**
   - Connects to historical transactions (`INVOLVES`), the primary target card (`ON_CARD`), and associated cards identified in fraud rings (`CONNECTED_TO`).

---

## 5. Benchmark Case Structure (`case_pack.csv`)

The 20 benchmark cases (`HHG-001` through `HHG-020`) represent the unseen evaluation set from November and December 2016.

### Deep Dive into the 20 Evaluation Cases

| Case ID | Opened Timestamp | Trigger Type | Flagged Txn ID | Card ID | Cust ID | Risk Score | Flagged Txn Attributes | Context & Initial Signal |
|---|---|---|---|---|---|---|---|---|
| **HHG-001** | 2016-12-05 01:55:28 | `risk_score` | 3514030 | C12382-K1 | C12382 | 0.61 | $77.07, in_person, Prod W, addr1: 444.0 | In-person transaction in region 444.0. Model score 0.61. |
| **HHG-002** | 2016-11-22 23:27:07 | `risk_score` | 3478782 | C11891-K1 | C11891 | 0.79 | $292.36, online, Prod C, no addr | Online CNP charge. Model score 0.79. Needs history check. |
| **HHG-003** | 2016-12-10 15:01:21 | `customer_report` | 3530164 | C08623-K2 | C08623 | — (0.40) | $49.00, in_person, Prod W | Customer disputed $49 purchase. In-person channel. |
| **HHG-004** | 2016-12-29 07:53:54 | `customer_report` | 3583227 | C08106-K1 | C08106 | — (0.34) | $128.33, online, Prod C, id_15: New | Customer disputed $128.33 purchase. Online CNP, new device. |
| **HHG-005** | 2016-12-08 03:38:37 | `risk_score` | 3523199 | C02923-K1 | C02923 | 0.54 | $100.07, online, Prod R, iOS Device, New | Online purchase from new iOS device. Score 0.54. Single signal. |
| **HHG-006** | 2016-11-22 02:30:00 | `customer_report` | 3476682 | C07297-K1 | C07297 | — (0.25) | $482.12, online, Prod C, Trident/7.0, New | Customer disputes $482.12 charge. Model scored only 0.25! |
| **HHG-007** | 2016-12-05 03:46:14 | `risk_score` | 3514948 | C09933-K2 | C09933 | 0.87 | $111.92, in_person, Prod W, addr1: 264.0 | In-person charge in region 264.0. High model score 0.87. |
| **HHG-008** | 2016-12-20 03:08:56 | `customer_report` | 3558054 | C13171-K2 | C13171 | — (0.38) | $55.68, online, Prod C, id_15: Found | Customer disputes $55.68 charge. Device was marked Found. |
| **HHG-009** | 2016-12-28 17:10:53 | `customer_report` | 3581141 | C08299-K1 | C08299 | — (0.28) | $30.02, online, Prod S, id_15: Found | Customer disputes $30.02. Device was Found. Possible recurring? |
| **HHG-010** | 2016-12-02 18:18:27 | `risk_score` | 3506725 | C10434-K1 | C10434 | 0.90 | $1,000.03, online, Prod R, Windows, New | High amount ($1k), new Windows device, high model score 0.90. |
| **HHG-011** | 2016-12-29 06:27:44 | `customer_report` | 3583368 | C11923-K2 | C11923 | — (0.39) | $131.30, online, Prod C, SM-G610F, New | Customer disputes $131.30. New Samsung device. |
| **HHG-012** | 2016-12-18 05:00:31 | `risk_score` | 3553342 | C05876-K2 | C05876 | 0.55 | $30.91, in_person, Prod W, addr1: 494.0 | In-person in region 494.0. Score 0.55. Weak signal. |
| **HHG-013** | 2016-12-09 05:39:29 | `risk_score` | 3526826 | C07671-K2 | C07671 | 0.76 | $35.66, online, Prod C, Windows, New | Online CNP from new Windows device. Score 0.76. |
| **HHG-014** | 2016-11-22 20:11:00 | `analyst_request` | 3478561 | C13487-K1 | C13487 | — (0.05) | $74.96, online, Prod C, SM-G935F, New, Proxy | Analyst request: shared unusual device profile! Score is only 0.05. Matches closed case undocumented ring! |
| **HHG-015** | 2016-11-17 19:03:36 | `risk_score` | 3464869 | C03042-K1 | C03042 | 0.77 | $599.94, online, Prod R, Trident/7.0, New | Online $599.94 purchase, new Trident/IE device. Score 0.77. |
| **HHG-016** | 2016-12-12 01:39:08 | `customer_report` | 3534820 | C09988-K1 | C09988 | — (0.37) | $59.67, online, Prod C, Windows, New | Customer disputes $59.67. New Windows device. |
| **HHG-017** | 2016-11-12 00:46:24 | `risk_score` | 3450629 | C04570-K1 | C04570 | 0.57 | $100.09, online, Prod R, Windows, Found, Proxy | Online charge from proxy IP. Score 0.57. Needs investigation. |
| **HHG-018** | 2016-11-27 14:41:26 | `customer_report` | 3491361 | C02354-K2 | C02354 | — (0.48) | $39.08, in_person, Prod W | Customer disputes $39.08 in-person purchase. Card present clone? |
| **HHG-019** | 2016-12-01 22:28:53 | `risk_score` | 3503878 | C07987-K2 | C07987 | 0.90 | $99.92, online, Prod R, Windows, New | Online charge from new Windows device. High model score 0.90. |
| **HHG-020** | 2016-12-03 12:04:26 | `risk_score` | 3509359 | C12265-K2 | C12265 | 0.52 | $125.08, online, Prod R, Trident/7.0, New | Online charge, new Trident device. Score 0.52. Weak signal. |

### Expected Output Structure
For each case `<case_id>`, an exact answer JSON file `<case_id>.json` must be generated in `cases/` containing:
1. `case`: Internal record (`status`, `verdict`, `fraud_probability`, `pattern`, `pattern_description`, `affected_txn_ids`, `first_suspicious_txn_id`, `connected_card_ids`, `connected_device_profiles`, `exposure_usd`, `evidence`, `similar_prior_cases`, `summary`, `written_to_graph`, `graph_case_id`).
2. `evidence_requests`: List of simulated requests (`customer_validation`, `step_up_auth`, `analyst_info`) with step and assumed response.
3. `next_best_actions`: Initial recommendations (pre-evidence), final recommendations (post-evidence), and `what_changed`.
4. `sar`: Suspicious Activity Report (`file`: bool, `reason`, `narrative`, `subjects`, `total_amount_usd`, `activity_dates`).
5. Execution metadata: `stop_reason`, `tool_calls`, `tokens`, `latency_s`.

---

## 6. Historical Case Structure & Case Memory

The `closed_cases_history.csv` dataset contains 5,565 historical investigations spanning July to October 2016.

### Analysis of Historical Case Memory
- **4,665 Confirmed Fraud Cases:**
  - `card_not_present_fraud`: 1,404
  - `account_takeover`: 1,205
  - `card_not_present_new_device`: 1,076
  - `out_of_region_use`: 955
  - `card_testing`: 16
  - `undocumented`: 9
- **900 Cleared Cases (`pattern = none`):**
  - Analysts cleared alerts when cardholders confirmed travel, new phone purchases, or legitimate intentions.
  - Exposure is always `$0.00`. Actions taken: `VERIFY_WITH_CUSTOMER|CLOSE_NO_FRAUD`.
- **How Historical Cases Enable Case Memory:**
  1. **Graph Traversal Retrieval:** Graph queries look up whether an entity in the current case (such as a `DeviceProfile`, `BillingRegion`, or `customer_id`) appeared in prior closed cases.
  2. **Vector Similarity Search:** Embedding `analyst_notes` and case summaries allows semantic GraphRAG retrieval to match complex behavioral patterns (e.g., card-testing bursts or structured sub-$500 transactions).
  3. **Continuous Memory Ingestion:** As the agent finishes investigating an exam case, it writes the new case into TigerGraph (`written_to_graph: true`), allowing subsequent investigations to discover cross-case correlations within November and December 2016.

---

## 7. Fraud Patterns Analysis

The hackathon documentation specifies five known fraud patterns, along with undocumented patterns and legitimate cleared patterns:

### 1. Card Testing (`card_testing`)
- **Signature:** Three or more tiny online authorizations (often < $5.00) within a tight time window (under 1 hour) on a single card, immediately followed by a larger purchase attempt.
- **Data Footprint:** High velocity on `NEXT` edge; small `TransactionAmt`; CNP channel (`online`).
- **Policy Rule:** R5.
- **Required Actions:** `DECLINE_TRANSACTION` and `STEP_UP_AUTH`. If a purchase > $100 has cleared, recommend `BLOCK_CARD`.

### 2. Card-Not-Present Fraud (`card_not_present_fraud`)
- **Signature:** Stolen card number used online without physical card. Transactions differ from cardholder's baseline amounts and product categories, often appearing in bursts of 2 to 4 transactions within 48 hours.
- **Data Footprint:** `channel = online`, `ProductCD` ∈ {`C`, `R`, `H`, `S`}.
- **Policy Rule:** R1 to R4. Ambiguous on a single transaction; requires customer verification before blocking.

### 3. CNP Fraud from a New Device (`card_not_present_new_device`)
- **Signature:** Same as CNP fraud, but identity record explicitly marks device as `id_15 = New` for this account, or shows an anonymous proxy (`id_23`).
- **Data Footprint:** `channel = online`, `id_15 = New`, `DeviceType`, `DeviceInfo`.
- **Policy Rule:** Stronger than pattern 2, but people legitimately buy new devices. Verify if single signal; block if cardholder denies.

### 4. Out-of-Region Use (`out_of_region_use`)
- **Signature:** In-person (`ProductCD = W`, `channel = in_person`) purchases in a billing region (`addr1`) where the cardholder has no previous history, while normal activity continues simultaneously at home.
- **Data Footprint:** Discrepancy between historical dominant `addr1` and flagged `addr1`.
- **Policy Rule:** R2, R3. Note: Multiple consecutive days in one new region indicates legitimate travel, not cloning!

### 5. Account Takeover (`account_takeover`)
- **Signature:** Mixed-channel activity inconsistent with cardholder; anomalies in device credentials, email domains, or match flags (`M1..M9`), indicating stolen account credentials rather than just card details.
- **Data Footprint:** Sudden change of device, email domain, and mixed `in_person` and `online` usage.

### 6. Undocumented Patterns (`undocumented`)
- **Empirical Evidence from `closed_cases_history.csv`:**
  - *Pattern A (Shared Device Proxy Ring):* Multiple distinct cardholders experiencing unauthorized online purchases from the identical device profile (e.g., `Samsung SM-G935F on Chrome for Android behind an anonymous proxy`). Seen in cases `CC-2649`, `CC-2971`, `CC-2985`, `CC-3035`, and directly matching benchmark case **HHG-014**!
  - *Pattern B (Velocity Structuring / Smurfing):* Series of rapid online transactions (e.g., 4 purchases within 40 minutes) specifically pegged just under the $500 velocity limit (e.g., $475-$495) across different merchant channels (`CC-3748`, `CC-3841`, `CC-3907`, `CC-4086`, `CC-4124`).
- **Policy Rule:** R9. Requires `CREATE_CASE`, `FILE_REPORT`, `ESCALATE_TO_ANALYST`, and custom explanation.

### 7. Legitimate Activity (`none`)
- **Signature:** False alarms triggered by imperfect risk scores.
- **Examples:** Legitimate travel to a new region, legitimate phone upgrades, planned high-ticket purchases.
- **Policy Rule:** R3. Confirmed by customer validation -> `CLOSE_NO_FRAUD`.

---

## 8. Fraud Policy & Governance Rules

The agent must operate under **Fraud Policy Version 1.0**:

### Permitted Actions & Approval Matrix

| Action | Execution Route | Customer Impact | Purpose / Usage |
|---|---|---|---|
| `ALLOW_TRANSACTION` | `auto` | None | Flagged transaction is cleared to proceed. |
| `DECLINE_TRANSACTION` | `L1` (Team Lead) | Low | Decline the specific pending authorization only; card remains active. |
| `MONITOR_CARD` | `auto` | None | Raise card monitoring sensitivity for 72 hours. |
| `MONITOR_CONNECTED_CARDS` | `auto` | None | Place linked cards (same device ring, region cluster) under monitoring. |
| `WARN_CUSTOMER` | `auto` | None | Send security tip or recurring charge clarification. |
| `VERIFY_WITH_CUSTOMER` | `auto` | Low | Contact cardholder to confirm authorization before action. |
| `STEP_UP_AUTH` | `auto` | Low | Demand OTP or mobile biometric confirmation. |
| `BLOCK_CARD` | `L1` if exposure ≤ $2,500; `L2` if > $2,500 | High | Block card and initiate reissuance. |
| `BLOCK_ALL_CARDS` | `L2` (Fraud Manager) | Very High | Block every card held by the customer (requires R10). |
| `GENERATE_REPORT` | `auto` | None | Internal investigation record without opening formal case. |
| `CREATE_CASE` | `auto` | None | Open formal internal case in graph. Triggered if prob ≥ 0.30 or evidence requested. |
| `FILE_REPORT` | `L2` (Fraud Manager) | None | File SAR with financial intelligence unit/regulator. |
| `ESCALATE_TO_ANALYST` | `auto` | None | Transfer case to human fraud analyst with graph dossier. |
| `CLOSE_NO_FRAUD` | `auto` | None | Close case as legitimate false alarm. |

### Policy Rules Summary (R1 to R10)
- **R1 (Weak Signal Verification):** If based on a single signal (e.g., risk score alone) and fraud probability < 0.70, MUST recommend `VERIFY_WITH_CUSTOMER` or `STEP_UP_AUTH` before blocking. Blocking on one signal is a policy violation.
- **R2 (Customer Denial):** If cardholder denies transaction, recommend `BLOCK_CARD` and `CREATE_CASE`. Recommend `FILE_REPORT` if exposure > $1,000 or linked to shared device/compromise.
- **R3 (Customer Confirmation):** If cardholder confirms transaction, recommend `CLOSE_NO_FRAUD`.
- **R4 (No Response in 24h):** Recommend `MONITOR_CARD` and `DECLINE_TRANSACTION`. Escalate if exposure > $500.
- **R5 (Card Testing):** 3+ small authorizations within 1 hour followed by larger purchase: recommend `DECLINE_TRANSACTION` and `STEP_UP_AUTH`. If purchase > $100 already cleared, recommend `BLOCK_CARD`.
- **R6 (Shared Origin):** Multiple cards showing fraud from identical device profile, region, or recipient email: recommend `CREATE_CASE`, `FILE_REPORT`, and `MONITOR_CONNECTED_CARDS`.
- **R7 (Disputed Recurring):** Customer disputes charge matching their monthly recurring pattern: recommend `CREATE_CASE`, `VERIFY_WITH_CUSTOMER`, `WARN_CUSTOMER`. Do NOT block.
- **R8 (Uncertain & Exposed):** If verdict is `uncertain` and exposure > $500, or evidence conflicts: recommend `ESCALATE_TO_ANALYST`.
- **R9 (Undocumented Patterns):** Coordinated or repeated abuse not matching known typologies: recommend `CREATE_CASE`, `FILE_REPORT`, `ESCALATE_TO_ANALYST`. Describe pattern in narrative.
- **R10 (Multi-Card Block Restriction):** NEVER recommend `BLOCK_ALL_CARDS` unless at least two of customer's cards show confirmed fraud or credentials are confirmed compromised.

### Stopping Criteria
The agent must terminate an investigation when:
1. Fraud probability is ≥ 0.85 or ≤ 0.15, backed by at least two independent pieces of evidence.
2. A customer verification response settles the verdict.
3. Further investigation steps will not alter the defensible action (documented in `stop_reason`).

---

## 9. Proposed TigerGraph Vertices

To maximize GSQL performance and enable GraphRAG tool use, the graph schema is designed as follows:

| Vertex Name | Primary ID (`PRIMARY_ID`) | Attributes & Types | Description |
|---|---|---|---|
| `Customer` | `customer_id` (STRING) | `total_cards` (INT), `first_seen` (DATETIME), `home_region` (STRING) | The cardholder individual. |
| `Card` | `card_id` (STRING) | `card_network` (STRING), `card_type` (STRING), `issuer_bank` (STRING), `is_active` (BOOL) | The payment card (`<customer_id>-K<n>`). |
| `Transaction` | `transaction_id` (STRING) | `amount` (DOUBLE), `ts` (DATETIME), `channel` (STRING), `product_cd` (STRING), `risk_score` (DOUBLE), `addr1` (STRING), `addr2` (STRING), `p_email` (STRING), `r_email` (STRING), `is_flagged` (BOOL) | The financial transaction event. |
| `DeviceProfile` | `device_id` (STRING) | `device_info` (STRING), `device_type` (STRING), `os` (STRING), `browser` (STRING), `screen` (STRING), `proxy_status` (STRING) | Canonical hardware and browser fingerprint. |
| `BillingRegion` | `region_id` (STRING) | `country_code` (STRING) | The `addr1` billing region code. |
| `EmailDomain` | `domain_name` (STRING) | `domain_type` (STRING) | Domain from `P_emaildomain` or `R_emaildomain`. |
| `ClosedCase` | `case_id` (STRING) | `opened_at` (DATETIME), `closed_at` (DATETIME), `outcome` (STRING), `pattern` (STRING), `exposure_usd` (DOUBLE), `report_filed` (BOOL), `actions_taken` (STRING), `analyst_notes` (STRING) | Historical and closed investigation record. |

---

## 10. Proposed TigerGraph Edges

| Edge Name | Source Vertex | Target Vertex | Directed / Undirected | Edge Attributes | Purpose |
|---|---|---|---|---|---|
| `OWNS` | `Customer` | `Card` | Directed | `since` (DATETIME) | Connects customer to payment cards. |
| `MADE` | `Card` | `Transaction` | Directed | None | Connects card to its transactions. |
| `FROM_DEVICE` | `Transaction` | `DeviceProfile` | Directed | `id_15` (STRING) | Online transaction device linkage. |
| `BILLED_IN` | `Transaction` | `BillingRegion` | Directed | None | Geographic location linkage. |
| `PURCHASER_EMAIL` | `Transaction` | `EmailDomain` | Directed | None | Purchaser email association. |
| `RECIPIENT_EMAIL` | `Transaction` | `EmailDomain` | Directed | None | Recipient email association. |
| `NEXT` | `Transaction` | `Transaction` | Directed | `delta_seconds` (INT) | Temporal transaction chain for a card. |
| `INVOLVES` | `ClosedCase` | `Transaction` | Directed | `is_first_fraud` (BOOL) | Links case to transactions involved. |
| `ON_CARD` | `ClosedCase` | `Card` | Directed | None | Primary card investigated in case. |
| `CONNECTED_TO` | `ClosedCase` | `Card` | Directed | None | Linked cards identified in fraud ring. |

---

## 11. Proposed Graph Properties & Aggregations

To support rapid, low-latency investigations by the AI Agent:
1. **Customer Baseline Aggregates:**
   - Dominant billing region (`home_region`): Determined by highest count of in-person transactions.
   - Known devices list: Pre-computed set of `DeviceProfile` IDs associated with customer's cleared transactions.
   - Usual amount distribution: Mean and standard deviation of transaction amounts.
2. **Card Velocity Attributes:**
   - 1-hour and 24-hour transaction frequency and sum.
   - Count of distinct devices used in past 48 hours.
3. **Device Risk Metrics:**
   - `card_count`: Number of distinct cards that have ever transacted through this `DeviceProfile`.
   - `fraud_case_count`: Number of confirmed fraud cases linked to this device.

---

## 12. Required Investigation Queries (GSQL)

The dataset and schema directly support the following parametrized GSQL queries:

1. `get_customer_profile(STRING customer_id)`:
   - Returns all cards, home billing regions, known devices, average transaction amounts, and historical transaction volume.
2. `get_card_recent_window(STRING card_id, DATETIME target_ts, INT hours)`:
   - Traverses `MADE` and `NEXT` edges to retrieve transactions within `±hours` of the flagged transaction.
   - Detects card testing sequences (< $5 authorizations followed by high-value purchases).
3. `check_device_sharing(STRING device_id, DATETIME target_ts)`:
   - Traverses `FROM_DEVICE` backwards to find all other transactions and cards using the same device within a 30-day window.
   - Returns distinct customer count and flags cross-card fraud rings.
4. `check_region_discrepancy(STRING customer_id, STRING region_id)`:
   - Evaluates whether `region_id` matches the cardholder's historical billing regions or is a foreign out-of-region authorization.
5. `find_connected_prior_cases(STRING card_id, STRING device_id, STRING customer_id)`:
   - Traverses to `ClosedCase` vertices sharing the same customer, card, or device profile.
   - Returns prior case IDs, outcomes, patterns, and analyst notes.
6. `calculate_case_exposure(SET<STRING> txn_ids)`:
   - Computes total absolute USD exposure across all identified fraudulent transactions.

---

## 13. Case-Memory Approach

Case Memory is a core hackathon requirement to emulate senior human fraud analysts:
1. **Initial Memory Load:** 5,565 closed cases from `closed_cases_history.csv` are ingested into TigerGraph as `ClosedCase` vertices and connected to their respective entities.
2. **Hybrid Retrieval Architecture:**
   - **Graph-Structural Retrieval:** GSQL query traverses directly from current entities (Card, Device, Customer) to historical cases.
   - **Semantic GraphRAG Retrieval:** Case notes (`analyst_notes`) and trigger narratives are vectorized and indexed. Semantic search retrieves past cases exhibiting identical behavioral typologies (e.g., structuring, proxy abuse).
3. **Dynamic Memory Progression (Write-Back):**
   - When the agent resolves an exam case, it creates a new `Case` vertex in TigerGraph with status, verdict, pattern, affected transactions, and summary.
   - If case HHG-014 identifies a shared device ring, subsequent cases (e.g., HHG-015 or HHG-017) can discover HHG-014 as an active investigation in memory.

---

## 14. GraphRAG Sources & Context Assembly

GraphRAG bridges graph analytics and LLM reasoning. Rather than passing raw CSV rows to the LLM, GraphRAG provides grounded, structured evidence:
1. **Graph Evidence Subgraph:**
   - Flagged transaction metadata and adjacent temporal transactions.
   - Customer historical baseline (known devices, typical regions, average spend).
   - Device profile sharing statistics (number of connected cards, proxy status).
2. **Regulatory & Typology Knowledge Documents:**
   - FinCEN SAR Narrative Guidance & Account Takeover Advisories.
   - FATF Cyber-Enabled Fraud & Money Mule typologies.
   - Bank Fraud Policy v1.0 rules (R1 to R10, approval routes).
3. **Retrieved Case Memory:**
   - Top 2-3 most similar closed cases, their verified patterns, and analyst findings.

---

## 15. Machine Learning Analysis: Is a New ML Model Needed?

### Assessment
**No separate custom machine learning model training is needed or recommended for the core solution.**

### Rationale
1. **Pre-computed Model Scores Exist:** The dataset already provides a real-time detection model risk score (`risk_score`) for every single transaction.
2. **Deterministic Rules & Graph Traversal:** Fraud patterns (e.g., card testing bursts, shared devices, out-of-region use) are structural graph patterns that are identified with 100% precision via GSQL graph traversal algorithms.
3. **LLM as the Reasoning Engine:** Modern LLMs with GraphRAG excel at synthesizing graph evidence, assessing uncertainty, following policy rules (R1 to R10), and generating compliant FinCEN SAR narratives.
4. **Where ML Embeddings Add Real Value:**
   - Text embeddings (e.g., `text-embedding-004` or `all-MiniLM-L6-v2`) used exclusively for semantic similarity search over historical analyst case notes and policy documents.

---

## 16. Data Leakage Risks & Isolation Protocol

### Identified Risks
1. **Benchmark Set Contamination:** The 20 cases in `case_pack.csv` occur exclusively in **November and December 2016**. If any statistical baseline, device frequency table, or memory store aggregates transactions from November/December prior to running the agent, future information could leak into earlier decisions.
2. **Public Kaggle Data Exploitation:** The hackathon rules explicitly forbid attempting to de-anonymize or cross-reference the original public Kaggle dataset.
3. **Circular Reasoning / Verdict Bleed:** The agent must evaluate cases in chronological order, using only historical cases closed prior to the exam case's `opened_at` timestamp.

### Mitigation & Isolation Protocol
- **Strict Temporal Boundary:** Historical case memory is strictly partitioned to cases closed on or before `2016-11-02`.
- **Chronological Benchmark Processing:** Process the 20 benchmark cases in order of `opened_at` timestamp (HHG-017 on Nov 12 through HHG-004 on Dec 29).
- **Hermetic Pipeline:** Code and scripts rely strictly on local workspace files.

---

## 17. Recommended System Architecture

```
                 ┌──────────────────────────────────────┐
                 │       Analyst Web UI Dashboard      │
                 │   (Case progression, Graph viewer,   │
                 │   Evidence tree, NBA, SAR display)   │
                 └──────────────────▲───────────────────┘
                                    │ REST / SSE
                 ┌──────────────────▼───────────────────┐
                 │          FastAPI Backend             │
                 │   (Orchestration, Session state,     │
                 │   Audit trail, Action simulation)    │
                 └──────────────────▲───────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    │                                                               │
┌───▼───────────────────────────┐       ┌───────────────────────────▼───┐
│     AI Fraud Agent Engine     │       │     Case Memory & GraphRAG    │
│  (LangGraph / ReAct / Custom) │       │  (Vector Embeddings & Search) │
│ - Evidence synthesizer        │       │ - 5,565 closed case notes     │
│ - Policy engine (R1-R10)      │       │ - FinCEN / FATF typologies    │
│ - Uncertainty assessor        │       │ - Fraud Policy v1.0 rules     │
│ - Next Best Action selector   │       └───────────────▲───────────────┘
│ - SAR narrative generator     │                       │
└───▲───────────────────────────┘                       │
    │ Tools                                             │
┌───▼───────────────────────────────────────────────────▼───────────────┐
│                          TigerGraph MCP                               │
│  (Parametrized GSQL Queries, Graph Traversal, Graph Algorithms)       │
└───────────────────────────────▲───────────────────────────────────────┘
                                │ GSQL / REST
┌───────────────────────────────▼───────────────────────────────────────┐
│                     TigerGraph Savanna / CE                           │
│  Vertices: Customer, Card, Transaction, DeviceProfile, BillingRegion, │
│            EmailDomain, ClosedCase                                    │
│  Edges: OWNS, MADE, FROM_DEVICE, BILLED_IN, NEXT, INVOLVES, ON_CARD  │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 18. Questions & Ambiguities Discovered

1. **Card Identification Resolution:** `transactions.csv` does not have an explicit `card_id` column; it has `customer_id` and `card1..card6`. Analysis of `closed_cases_history.csv` confirms that card IDs use suffixes `-K1`, `-K2`, `-K3`. Sub-cards correspond to unique combinations of `card2`..`card6` under the same customer. During graph ingestion, `card_id` will be systematically synthesized using this deterministic mapping.
2. **Simulation of Evidence Requests:** As stated in the policy, customer and analyst responses are not provided in real-time. The agent must simulate realistic responses (e.g., "Customer states they did not make this purchase and still has the card" vs "Customer confirms legitimate travel") based on the case trigger, baseline discrepancy, and case outcome likelihood, explicitly recording this in `evidence_requests`.
3. **SAR Narrative Precision:** FinCEN regulatory compliance requires 6 to 12 complete sentences covering Who, What, When, Where, How, and Why. Our LLM prompt template must enforce strict adherence to this FinCEN standard.
