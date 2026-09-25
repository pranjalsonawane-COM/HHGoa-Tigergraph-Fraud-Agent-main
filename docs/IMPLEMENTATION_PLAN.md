# TigerGraph Agentic Fraud Investigation (HHGOA IEEE-CIS) — Implementation Plan

**Project:** Autonomous AI Fraud Investigation Agent & Next Best Action Recommender  
**Target Platform:** TigerGraph (Savanna / Community Edition) + Python + FastAPI + Next-Gen Analyst Dashboard  
**Dataset:** IEEE-CIS Vesta Fraud Detection with TigerGraph Hacker House Goa Overlay  

---

## Phase 1 — Dataset Preparation & Deterministic Preprocessing
- **Objective:** Clean, validate, and prepare data pipelines without altering original CSV files.
- **Tasks:**
  - Build a deterministic card-mapping utility to synthesize canonical `card_id` (`<customer_id>-K<n>`) across `transactions.csv` based on `customer_id` and unique `card2..card6` profiles, ensuring 100% agreement with `case_pack.csv` and `closed_cases_history.csv`.
  - Construct composite `DeviceProfile` identifiers (`DeviceInfo | id_30 | id_31 | id_33`) joining `identity.csv` and `transactions.csv`.
  - Partition temporal streams: Historical training/memory set (July 2 to Nov 2, 2016) vs. Benchmark evaluation set (Nov 12 to Dec 31, 2016).
  - Generate clean loading CSVs or streaming iterators formatted for high-throughput TigerGraph loading.
- **Verification:** Ensure all 20 flagged transactions and 14,955 historical case transactions match their exact target cards and customers.

---

## Phase 2 — TigerGraph Schema Definition
- **Objective:** Design and instantiate the graph schema in TigerGraph Savanna / Community Edition.
- **Tasks:**
  - Define Vertex Types:
    - `Customer (PRIMARY_ID customer_id STRING, total_cards INT, home_region STRING)`
    - `Card (PRIMARY_ID card_id STRING, card_network STRING, card_type STRING, is_active BOOL)`
    - `Transaction (PRIMARY_ID transaction_id STRING, amount DOUBLE, ts DATETIME, channel STRING, product_cd STRING, risk_score DOUBLE, addr1 STRING, addr2 STRING, p_email STRING, r_email STRING, is_flagged BOOL)`
    - `DeviceProfile (PRIMARY_ID device_id STRING, device_info STRING, device_type STRING, os STRING, browser STRING, screen STRING, proxy_status STRING)`
    - `BillingRegion (PRIMARY_ID region_id STRING, country_code STRING)`
    - `EmailDomain (PRIMARY_ID domain_name STRING, domain_type STRING)`
    - `ClosedCase (PRIMARY_ID case_id STRING, opened_at DATETIME, closed_at DATETIME, outcome STRING, pattern STRING, exposure_usd DOUBLE, report_filed BOOL, actions_taken STRING, analyst_notes STRING)`
  - Define Directed & Undirected Edges:
    - `OWNS (FROM Customer, TO Card)`
    - `MADE (FROM Card, TO Transaction)`
    - `FROM_DEVICE (FROM Transaction, TO DeviceProfile, id_15 STRING)`
    - `BILLED_IN (FROM Transaction, TO BillingRegion)`
    - `PURCHASER_EMAIL (FROM Transaction, TO EmailDomain)`
    - `RECIPIENT_EMAIL (FROM Transaction, TO EmailDomain)`
    - `NEXT (FROM Transaction, TO Transaction, delta_seconds INT)`
    - `INVOLVES (FROM ClosedCase, TO Transaction, is_first_fraud BOOL)`
    - `ON_CARD (FROM ClosedCase, TO Card)`
    - `CONNECTED_TO (FROM ClosedCase, TO Card)`
  - Compile the graph schema (`CREATE GRAPH FraudGraph(...)`).

---

## Phase 3 — High-Throughput Data Loading
- **Objective:** Load the 590,742 transactions, 144,432 identities, and 5,565 closed cases into TigerGraph.
- **Tasks:**
  - Write GSQL loading jobs (`LOAD JOB load_fraud_data FOR GRAPH FraudGraph`) with batching and error handling.
  - Ingest `Customer` and `Card` vertices and `OWNS` edges.
  - Ingest `Transaction`, `DeviceProfile`, `BillingRegion`, and `EmailDomain` vertices with associative edges.
  - Construct temporal `NEXT` edges chronologically linking transactions per card.
  - Ingest `ClosedCase` vertices and link them via `INVOLVES`, `ON_CARD`, and `CONNECTED_TO`.
- **Verification:** Execute vertex and edge count queries; verify complete data integrity against source CSVs.

---

## Phase 4 — GSQL Investigation Queries Development
- **Objective:** Implement parameterized, sub-second graph investigation queries for the agent.
- **Tasks:**
  - `get_customer_history(customer_id)`: Retrieve card list, primary billing regions, known devices, average spend, and transaction count.
  - `get_card_transactions_window(card_id, target_ts, window_hours)`: Retrieve preceding and succeeding transactions to identify velocity, card testing sequences, and burst activity.
  - `find_shared_device_ring(device_id, target_ts, window_days)`: Identify all cards and customers sharing the device profile; count confirmed fraud associations.
  - `check_region_anomaly(customer_id, region_id)`: Compare current billing region against cardholder's historical geographical distribution.
  - `find_similar_cases_by_entities(card_id, customer_id, device_id)`: Direct graph traversal to find prior closed investigations involving these entities.
  - Install and optimize all queries in TigerGraph.

---

## Phase 5 — Fraud Pattern Detection Algorithms
- **Objective:** Implement deterministic pattern recognition engines for known and emerging fraud typologies.
- **Tasks:**
  - **Pattern 1 (Card Testing):** Algorithm detecting 3+ sub-$5 authorizations within 1 hour followed by a larger attempt.
  - **Pattern 2 (Card-Not-Present Fraud):** Algorithm detecting anomalous online burst activity (> 2-4 transactions in 48h) inconsistent with cardholder baseline.
  - **Pattern 3 (CNP from New Device):** Integration of `id_15 = New` and proxy signals (`id_23`) with CNP transaction bursts.
  - **Pattern 4 (Out-of-Region Use):** Graph query comparing card-present `addr1` against cardholder home baseline while home transactions remain active.
  - **Pattern 5 (Account Takeover):** Detection of sudden simultaneous changes in device, email domain, and mixed channel authorization patterns.
  - **Pattern 6 (Undocumented Coordinated Rings):** Multi-card cross-customer device sharing algorithms (unmasking proxy syndicates and velocity smurfing under $500).

---

## Phase 6 — Historical Case Memory & Vector Indexing
- **Objective:** Build the case memory retrieval mechanism enabling the agent to learn from 5,565 closed cases.
- **Tasks:**
  - Extract and vectorize `analyst_notes` and case summaries from `closed_cases_history.csv` using text embeddings.
  - Set up a vector index (in TigerGraph Savanna Vector Search or local fast vector store) for semantic similarity retrieval.
  - Implement hybrid search: Graph structural neighborhood match + semantic embedding match.
  - Build dynamic memory update functionality: When the agent closes a case, it writes the new case record and embeddings back into memory.

---

## Phase 7 — GraphRAG Knowledge Grounding
- **Objective:** Ground the LLM with structured graph subgraphs and official regulatory documents.
- **Tasks:**
  - Ingest regulatory guidelines: FinCEN SAR narrative guidelines, FATF cyber-fraud reports, FFIEC red flag guidance, and Bank Fraud Policy v1.0.
  - Develop GraphRAG Context Assembler: Combines graph subgraphs, customer baseline metrics, matched historical case precedents, and policy rules into an LLM context payload.
  - Prevent raw data dumping: Summarize transaction sequences into structured, interpretable evidence objects.

---

## Phase 8 — TigerGraph MCP (Model Context Protocol) Integration
- **Objective:** Expose TigerGraph queries and capabilities as standardized MCP tools for AI agents.
- **Tasks:**
  - Configure TigerGraph MCP server (`tigergraph-mcp`) connecting to Savanna or Community Edition instance.
  - Expose tools: `get_customer_profile`, `get_card_window`, `check_shared_device`, `check_region_history`, `search_similar_cases`, `write_investigation_case`.
  - Validate tool schema, input validation, and execution latency.

---

## Phase 9 — Core AI Fraud Investigation Agent
- **Objective:** Build the autonomous reasoning agent utilizing LangGraph / ReAct agent architecture.
- **Tasks:**
  - Implement state machine workflow:
    1. **Trigger Ingestion:** Parse trigger type, score, and flagged transaction.
    2. **Hypothesis Generation:** Formulate initial fraud typologies.
    3. **Graph Exploration:** Dispatch MCP tool calls to gather graph evidence.
    4. **Memory Retrieval:** Retrieve similar historical cases from case memory.
    5. **Uncertainty Assessment:** Evaluate confidence, conflicting evidence, and need for additional signals.
  - Enforce stopping criteria: Stop when probability ≥ 0.85 or ≤ 0.15, verification settles, or further steps yield no change.

---

## Phase 10 — Controlled Evidence Gathering & Simulation
- **Objective:** Implement policy-governed evidence gathering workflows.
- **Tasks:**
  - Implement simulation module for allowed pre-decision evidence requests:
    - `customer_validation` (verify transaction with cardholder)
    - `step_up_auth` (request OTP or app confirmation)
    - `analyst_info` (request cross-card analyst review)
  - Generate contextually grounded simulated responses based on case attributes and historical baseline.
  - Log every evidence request in the mandatory `evidence_requests` schema (`type`, `asked_after_step`, `assumed_response`).

---

## Phase 11 — Next Best Action (NBA) Engine & Policy Rules
- **Objective:** Encode Bank Fraud Policy v1.0 (Rules R1 to R10) and approval routes.
- **Tasks:**
  - Deterministic evaluation of R1 (verify weak signals before blocking), R2 (customer denial), R3 (confirmation), R5 (card testing), R6 (shared device), R8 (escalation), R9 (undocumented), R10 (block all cards restriction).
  - Compute Initial Next Best Actions (pre-evidence).
  - Compute Final Next Best Actions (post-evidence) and document `what_changed`.
  - Assign strict approval routes: `auto`, `L1` (team lead), `L2` (fraud manager) based on policy exposure thresholds.

---

## Phase 12 — Case Management & SAR Narrative Generation
- **Objective:** Generate audit-ready internal case records and FinCEN-compliant SAR filings.
- **Tasks:**
  - Implement SAR generator adhering to FinCEN narrative guidelines: Who, What, When, Where, How, and Why (6 to 12 concise sentences).
  - Validate SAR triggers: Only file when fraud is confirmed/suspected AND exposure > $1,000, or shared device, or undocumented ring.
  - Package final output into `<case_id>.json` format with schema validation.
  - Write closed cases back to TigerGraph graph database (`written_to_graph: true`).

---

## Phase 13 — Backend Service (FastAPI)
- **Objective:** Create a lightweight, high-performance REST and streaming API.
- **Tasks:**
  - Endpoints:
    - `GET /api/cases`: List all 20 benchmark cases and their real-time investigation statuses.
    - `POST /api/investigate/{case_id}`: Trigger automated agent investigation for a case.
    - `GET /api/cases/{case_id}`: Retrieve full investigation dossier, evidence graph, SAR, and NBA.
    - `GET /api/graph/subgraph/{case_id}`: Stream nodes and links for interactive UI graph visualization.
  - Real-time event streaming (SSE / WebSockets) for agent step-by-step reasoning transparency.

---

## Phase 14 — Interactive Analyst Dashboard (Frontend)
- **Objective:** Provide a visually stunning, intuitive analyst UI demonstrating the entire investigation lifecycle.
- **Tasks:**
  - **Aesthetics:** Dark mode, glassmorphism, modern typography (Inter/Outfit), clean status badges.
  - **Core Views:**
    - *Case Queue & Filter View:* Overview of all cases with trigger types, risk scores, and statuses.
    - *Investigation Progression Stream:* Live ReAct reasoning trace showing tool calls, evidence found, and policy checks.
    - *Interactive Subgraph Visualizer:* Visual rendering of Customer, Card, Flagged Transaction, DeviceProfile, and connected cards.
    - *Evidence & Precedent Matrix:* Side-by-side display of retrieved similar past cases and claims.
    - *Next Best Action & Approval Panel:* Initial vs. Final action cards with approval badges (`auto`, `L1`, `L2`).
    - *SAR Narrative Viewer:* Formatted regulatory filing preview ready for submission.

---

## Phase 15 — Benchmark Testing & Answer File Validation
- **Objective:** Execute the automated agent on all 20 benchmark cases and validate answer compliance.
- **Tasks:**
  - Run agent pipeline across `HHG-001` through `HHG-020` in strict chronological sequence.
  - Export 20 JSON answer files to `cases/<case_id>.json`.
  - Validate JSON schema: Verify no missing fields, check ID validity, ensure consistency between `sar.file` and `FILE_REPORT` action, verify exposure calculations.
  - Calibrate fraud probability scores and check policy adherence.

---

## Phase 16 — Demonstration Video, Technical Blog & Submission
- **Objective:** Finalize all hackathon deliverables.
- **Tasks:**
  - Record 3–5 minute end-to-end demo video highlighting graph traversal, agentic uncertainty handling, case memory retrieval, and approval routing.
  - Write technical blog post covering architecture, GSQL queries, GraphRAG implementation, and lessons learned.
  - Draft social media post tagging @TigerGraphDB.
  - Final repository audit and README updates.
