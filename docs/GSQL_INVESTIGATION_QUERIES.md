# TigerGraph GSQL Investigation Queries Documentation

**Project:** TigerGraph Agentic Fraud Investigation (HHGOA IEEE-CIS)  
**Graph Name:** `FraudGraph`  
**Document Version:** 1.0  
**GSQL File:** [`tigergraph/queries/investigation_queries.gsql`](file:///d:/HHGOA-Fraud-Agent/tigergraph/queries/investigation_queries.gsql)  
**Python Engine:** [`scripts/query_engine.py`](file:///d:/HHGOA-Fraud-Agent/scripts/query_engine.py)  

---

## 1. Overview & Query Architecture

The FraudGraph investigation suite exposes 7 high-performance, parameterized GSQL queries designed for sub-second execution by AI Agents, MCP endpoints, and human analysts.

### Key Design Principles:
- **Evidence-Only Outputs:** Queries extract factual, measurable graph patterns, topological structures, and temporal signals. They **never hardcode fraud labels** or make unilateral policy decisions.
- **Strict Anti-Leakage Safeguards:** Historical case memory traversals require a `before_ts` parameter, ensuring the agent cannot retrieve cases closed after the target transaction's investigation timestamp.
- **Indexed Graph Traversal:** 100% of traversals originate from primary IDs (`customer_id`, `card_id`, `device_id`, `transaction_id`), avoiding expensive full-graph scans.

---

## 2. Query Reference & Specification

---

### Query 1: `get_customer_profile`
* **Purpose:** Constructs a 360-degree historical baseline of the customer across all their cards, spending habits, known devices, dominant regions, and email domains.
* **Inputs:** `customer_id` (STRING)
* **Graph Traversal:** `Customer` —[`OWNS`]→ `Card` —[`MADE`]→ `Transaction`
* **Calculated Signals:**
  - `number_of_cards`: Total active cards held by the customer.
  - `total_transaction_count`: Historical transaction volume.
  - `average_transaction_amount`: Mean historical spend.
  - `min_transaction_amount` & `max_transaction_amount`: Spend boundaries.
  - `distinct_devices_used`: List of device profile IDs historically trusted by this account.
  - `distinct_billing_regions` & `billing_region_counts`: Geographical concentration.
  - `distinct_purchaser_email_domains` & `distinct_recipient_email_domains`.
* **Example Invocation:**
  ```sql
  RUN QUERY get_customer_profile("C13487")
  ```
* **Example JSON Result:**
  ```json
  {
    "customer_id": "C13487",
    "number_of_cards": 1,
    "card_ids": ["C13487-K1"],
    "total_transaction_count": 85,
    "total_transaction_amount": 4521.80,
    "average_transaction_amount": 53.20,
    "min_transaction_amount": 12.50,
    "max_transaction_amount": 499.00,
    "first_transaction_timestamp": "2016-07-05 11:20:10",
    "latest_transaction_timestamp": "2016-11-22 16:11:00",
    "distinct_devices_used": ["DEV_13b0f4b32516"],
    "distinct_billing_regions": ["191.0"],
    "billing_region_counts": {"191.0": 85},
    "distinct_purchaser_email_domains": ["yahoo.com"],
    "distinct_recipient_email_domains": ["gmail.com"]
  }
  ```
* **Performance Considerations:** Single-hop to multi-hop bounded by customer's transaction history ($O(k)$ where $k \le 1,500$ txns).

---

### Query 2: `get_card_window`
* **Purpose:** Inspects temporal velocity, rapid burst transactions, and card-testing patterns (< $5 small authorizations) in the vicinity of a reference transaction.
* **Inputs:**
  - `card_id` (STRING)
  - `ref_transaction_id` (STRING, optional)
  - `window_hours` (INT, default 24)
* **Graph Traversal:** `Card` —[`MADE`]→ `Transaction` (filtered by time delta `|t.ts - ref_ts| <= window_hours`)
* **Calculated Signals:**
  - `small_auth_count`: Number of online authorizations strictly under $5.00.
  - `small_auth_window_seconds`: Time difference in seconds between the first and last sub-$5 authorization.
  - `burst_window_seconds`: Time span of all window transactions.
  - `transactions`: List of transaction records in the window.
* **Example Invocation:**
  ```sql
  RUN QUERY get_card_window("C13487-K1", "3478561", 24)
  ```
* **Performance Considerations:** Highly filtered by card primary ID and timestamp interval.

---

### Query 3: `check_device_sharing`
* **Purpose:** Unmasks multi-card syndicates, shared hardware, and anonymous proxy rings by identifying all cards and customers sharing the exact same `DeviceProfile`.
* **Inputs:**
  - `device_id` (STRING)
  - `ref_transaction_id` (STRING, optional)
  - `ref_card_id` (STRING, optional)
  - `lookback_days` (INT, default 30)
* **Graph Traversal:** `DeviceProfile` —[`<FROM_DEVICE`]→ `Transaction` —[`<MADE`]→ `Card` —[`<ON_CARD` / `<CONNECTED_TO`]→ `ClosedCase`
* **Calculated Signals:**
  - `number_of_distinct_cards`: Number of cards sharing this device.
  - `number_of_distinct_customers`: Number of distinct customers sharing this device.
  - `connected_card_ids`: Full list of linked payment cards.
  - `connected_historical_cases`: Prior closed fraud investigations involving this device.
* **Example Invocation:**
  ```sql
  RUN QUERY check_device_sharing("DEV_13b0f4b32516", "3478561", "C13487-K1", 30)
  ```
* **Example JSON Result:**
  ```json
  {
    "device_id": "DEV_13b0f4b32516",
    "canonical_profile_str": "SM-G935F Build/NRD90M | Android 7.0 | chrome 62.0 for android | 1920x1080",
    "device_type": "mobile",
    "number_of_distinct_cards": 53,
    "number_of_distinct_customers": 52,
    "connected_card_ids": ["C13487-K1", "C03528-K1", "C09998-K1", "C06617-K1", "C09733-K1"],
    "transaction_count": 89,
    "first_seen": "2016-08-12 14:02:11",
    "last_seen": "2016-11-22 16:11:00",
    "connected_historical_cases": ["CC-2649", "CC-2971", "CC-2985", "CC-3035"]
  }
  ```

---

### Query 4: `check_region_discrepancy`
* **Purpose:** Evaluates whether a transaction's billing region differs from the customer's historical home baseline (detects out-of-region use vs. legitimate travel).
* **Inputs:**
  - `customer_id` (STRING)
  - `ref_transaction_id` (STRING, optional)
  - `ref_card_id` (STRING, optional)
* **Graph Traversal:** `Customer` —[`OWNS`]→ `Card` —[`MADE`]→ `Transaction` (historical `addr1` aggregations)
* **Calculated Signals:**
  - `current_region`: Billing region of the reference transaction.
  - `dominant_region`: Customer's primary baseline billing region.
  - `region_changed`: Boolean flag (`true` if current != dominant).
  - `current_region_transaction_count`: Historical familiarity with current region.
  - `region_first_seen` & `region_last_seen`: Temporal duration of activity in each region.
* **Example Invocation:**
  ```sql
  RUN QUERY check_region_discrepancy("C08623", "3530164", "C08623-K2")
  ```

---

### Query 5: `find_connected_prior_cases`
* **Purpose:** Retrieves historical closed fraud investigations connected to investigated entities (Card, Customer, or DeviceProfile).
* **Inputs:**
  - `customer_id` (STRING, optional)
  - `card_id` (STRING, optional)
  - `device_id` (STRING, optional)
  - `before_ts` (DATETIME / STRING, temporal filter)
* **Graph Traversal:**
  - `Card` —[`<ON_CARD` / `<CONNECTED_TO`]→ `ClosedCase`
  - `Customer` —[`OWNS`]→ `Card` —[`<ON_CARD` / `<CONNECTED_TO`]→ `ClosedCase`
  - `DeviceProfile` —[`<FROM_DEVICE`]→ `Transaction` —[`<MADE`]→ `Card` —[`<ON_CARD` / `<CONNECTED_TO`]→ `ClosedCase`
* **Anti-Leakage Safeguard:** Only cases where `closed_at <= before_ts` are returned. Future or active cases are excluded.
* **Example Invocation:**
  ```sql
  RUN QUERY find_connected_prior_cases("C13487", "C13487-K1", "DEV_13b0f4b32516", "2016-11-22 16:11:00")
  ```

---

### Query 6: `calculate_case_exposure`
* **Purpose:** Computes the exact absolute USD monetary exposure across a specified list of identified fraudulent transaction IDs.
* **Inputs:** `txn_ids` (SET<STRING>)
* **Graph Traversal:** Point lookup on `Transaction` vertices by ID.
* **Calculated Signals:**
  - `total_exposure_usd`: Sum of `ABS(amount)` across all valid transactions.
  - `transaction_count`: Count of confirmed transaction IDs.
  - `earliest_transaction` & `latest_transaction`: Temporal bounds of the fraud episode.
* **Example Invocation:**
  ```sql
  RUN QUERY calculate_case_exposure(["3478561", "3460634", "3462636"])
  ```

---

### Query 7: `get_transaction_context`
* **Purpose:** Foundational 360-degree starting-point query providing complete attribute context, device profile, and adjacent temporal transactions for an alert.
* **Inputs:** `transaction_id` (STRING)
* **Graph Traversal:** `Transaction` —[`PREV` / `NEXT`]→ `Transaction`, plus `FROM_DEVICE`, `BILLED_IN`, `PURCHASER_EMAIL`, `RECIPIENT_EMAIL`
* **Calculated Signals:**
  - Transaction amount, timestamp, channel, product code, model risk score, `id_15`, `id_23`.
  - Full `DeviceProfile` metadata.
  - Chronological preceding (`previous_transactions`) and succeeding (`next_transactions`) transactions on the same card.
* **Example Invocation:**
  ```sql
  RUN QUERY get_transaction_context("3478561")
  ```
