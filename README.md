# ⚡ TigerGraph Agentic Fraud Investigation Agent (HHGOA)

> **An Autonomous AI Agent for Fraud Investigation and Next-Best Action powered by TigerGraph GraphRAG, Hybrid Case Memory, and Fraud Policy v1.0 Governance.**

---

## 📌 Executive Summary

Fraud teams at financial institutions face intense pressure. Manual investigations—gathering transaction histories, tracing money movement, identifying connected accounts across device profiles, reviewing compliance policies, and drafting FinCEN Suspicious Activity Reports (SARs)—are fragmented, slow, and often complete only after funds are lost.

This project delivers an **Autonomous AI Agent for Fraud Investigation** powered by **TigerGraph** that:
1. **Traverses 634,810 Vertices & 2,505,246 Edges** to uncover multi-card device proxy syndicates (e.g. 52 cards sharing Samsung SM-G935F behind anonymous proxies in `HHG-014`).
2. **Retrieves Precedents from 5,565 Closed Cases** in sub-2ms using BM25 semantic search with strict temporal anti-leakage protection.
3. **Evaluates Fraud Policy v1.0 Rules R1–R10** deterministically to enforce human-in-the-loop approval hierarchies (`auto`, `L1_analyst`, `L2_senior_manager`).
4. **Simulates Interactive Evidence Gathering** (customer travel verification, step-up biometric auth) when signals are uncertain.
5. **Generates FinCEN-Compliant SAR Narratives** automatically for mandatory filings ($10,000+ exposure or organized rings).
6. **Exposes 7 Standard JSON-RPC Tools via TigerGraph Model Context Protocol (MCP)** for seamless integration with Claude Desktop, Antigravity, Cursor, and LangGraph.

---

## 🏗️ System Architecture & Graph Schema

```
                                  INCOMING ALERT / CASE
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
    TigerGraph Graph Engine                                  Semantic Case Memory
 ┌───────────────────────────┐                            ┌───────────────────────────┐
 │ - 13,553 Customers        │                            │ - 5,565 Closed Cases      │
 │ - 14,850 Cards            │                            │ - Sub-2ms BM25 Search     │
 │ - 590,742 Transactions    │                            │ - Anti-Leakage `before_ts`│
 │ - 9,708 Device Profiles   │                            │ - Consensus Insights      │
 │ - 332 Billing Regions     │                            └─────────────┬─────────────┘
 └─────────────┬─────────────┘                                          │
               │                                                        │
               └────────────────────────────┬───────────────────────────┘
                                            ▼
                           GraphRAG Multi-Hop Evidence Engine
                                            │
                                            ▼
                           Fraud Policy v1.0 Rules (R1 - R10)
                                            │
                                            ▼
                     Autonomous ReAct Agent & Next Best Action Playbooks
                                            │
                         ┌──────────────────┴──────────────────┐
                         ▼                                     ▼
                REST API Backend & UI                 Model Context Protocol
              (Interactive Web Dashboard)                 (MCP JSON-RPC)
```

### TigerGraph Schema (`tigergraph/schema/schema.gsql`)
- **7 Vertex Types:** `Customer`, `Card`, `Transaction`, `DeviceProfile`, `BillingRegion`, `EmailDomain`, `ClosedCase`.
- **10 Primary Directed Edge Types & Reverses:** `OWNS`/`OWNED_BY`, `MADE`/`MADE_BY`, `FROM_DEVICE`/`DEVICE_FOR_TXN`, `BILLED_IN`/`REGION_FOR_TXN`, `PURCHASER_EMAIL`/`PURCHASER_EMAIL_FOR_TXN`, `RECIPIENT_EMAIL`/`RECIPIENT_EMAIL_FOR_TXN`, `NEXT`/`PREV`, `INVOLVES`/`INVOLVED_IN_CASE`, `ON_CARD`/`CASE_ON_CARD`, `CONNECTED_TO`/`CONNECTED_TO_CASE`.

---

## 🚀 Quick Start & One-Click Demo

### 1. Prerequisites
- Python 3.9+ (Standard Library only - 0 required external pip packages for core agent and backend!)

### 2. Run Complete Pipeline & Launch Interactive Web Dashboard
```bash
python run_demo.py
```
This command will:
1. Initialize the Graph Query Engine and Case Memory.
2. Run autonomous investigations on benchmark cases `HHG-014` (Proxy Syndicate) and `HHG-001` (Out-of-Region).
3. Demonstrate interactive customer travel evidence simulation.
4. Launch the REST API server at `http://localhost:8000`.
5. Automatically open the **Interactive Fraud Dashboard** in your default web browser!

---

## 🧪 Running the Complete Test Suite

The codebase features a 100% passing test suite across 50 unit tests:
```bash
python -m unittest discover -s tests
```

---

## 📁 Repository Structure

```
HHGOA-Fraud-Agent/
├── cases/                      # Official 20 benchmark submission JSON files (HHG-001 to HHG-020)
├── answers/                    # Mirrored benchmark answers
├── backend/
│   └── server.py              # Zero-dependency REST API server & static file host
├── data/
│   ├── raw/                   # Raw CSV files (transactions.csv, identity.csv, etc.)
│   └── processed/             # Compact graph-ready files (634k vertices, 2.5M edges)
├── docs/                      # Comprehensive technical documentation
│   ├── DATASET_ANALYSIS.md
│   ├── TIGERGRAPH_CONNECTION.md
│   ├── GSQL_INVESTIGATION_QUERIES.md
│   ├── FRAUD_PATTERNS.md
│   ├── CASE_MEMORY.md
│   ├── GRAPHRAG_ENGINE.md
│   ├── TIGERGRAPH_MCP.md
│   ├── AI_AGENT_CORE.md
│   ├── EVIDENCE_SIMULATION.md
│   ├── NBA_DECISION_ENGINE.md
│   ├── BENCHMARK_ANSWERS.md
│   ├── BACKEND_API.md
│   ├── FRONTEND_DASHBOARD.md
│   └── EVALUATION_REPORT.md
├── frontend/                  # Modern interactive web dashboard (HTML5, CSS3, JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── mcp/
│   ├── server.py              # Model Context Protocol (MCP) JSON-RPC 2.0 server
│   └── mcp_config.json.template
├── scripts/                   # Core agent modules & preprocessing
│   ├── preprocessing/
│   │   ├── card_mapper.py     # Deterministic customer card mapping
│   │   └── device_mapper.py   # Device profile canonicalization
│   ├── query_engine.py        # Python RESTPP & local GSQL query engine
│   ├── pattern_detector.py    # Typology classifiers (Card Testing, Syndicate, ATO, etc.)
│   ├── case_memory.py         # Sub-2ms BM25 precedent search
│   ├── policy_engine.py       # Fraud Policy v1.0 rules evaluator (R1-R10)
│   ├── graph_rag.py           # Multi-hop GraphRAG evidence aggregator
│   ├── agent_core.py          # Autonomous ReAct decision state machine
│   ├── evidence_simulator.py  # Interactive evidence collection simulator
│   ├── nba_engine.py          # Operational playbook generator
│   ├── case_manager.py        # 20 benchmark case answer generator
│   └── evaluate_benchmarks.py # Benchmark metrics audit script
├── tigergraph/
│   ├── client.py              # TigerGraph RESTPP HTTP client driver
│   ├── config.json.template   # TigerGraph Savanna / CE credentials config
│   ├── schema/
│   │   ├── schema.gsql        # GSQL Graph Schema
│   │   └── loading_jobs.gsql  # GSQL Data Loading Jobs
│   └── queries/
│       └── investigation_queries.gsql # 7 Production GSQL Investigation Queries
├── tests/                     # 50 Unit tests covering 100% of pipeline components
├── case_pack.csv              # 20 Hackathon Evaluation Benchmark Cases
├── run_demo.py                # One-click interactive demo entrypoint
└── README.md
```

---

## 📊 Benchmark Evaluation Audit Results

Run the automated evaluation audit:
```bash
python scripts/evaluate_benchmarks.py
```

| Metric | Result | Target |
| :--- | :--- | :--- |
| **Total Benchmark Cases** | 20 Cases | 20 Cases |
| **Schema Compliance Rate** | **100.0%** | 100.0% |
| **Evidence Grounding Rate** | **100.0%** | > 95.0% |
| **Average Decision Confidence** | **85.0%** | > 80.0% |
| **FinCEN SAR Filing Accuracy** | **100.0%** | 100.0% |
| **Total Exposure Mitigated** | **$3,623.21** | -- |

---

## 🏆 Key Features & Innovations

1. **Deterministic Card Resolution:** Solved sub-card mapping (`card1`..`card6` $\rightarrow$ `customer_id-K<n>`) with 100.0% accuracy.
2. **Graph-Grounded Reasoning:** Every assertion is backed by explicit GSQL query references and entity IDs—eliminating LLM hallucinations.
3. **Strict Anti-Leakage Safeguard:** Enforces `closed_at <= before_ts` so future closed cases never contaminate active investigations.
4. **Interactive Evidence Gathering:** Dynamically simulates customer travel confirmation or biometric step-up challenges when initial signals are uncertain.
5. **Model Context Protocol (MCP):** Native JSON-RPC server allowing any MCP-compatible AI agent (Claude Desktop, Cursor, Antigravity) to query TigerGraph directly.

## Submission Artifact Notes

## Submission Artifact Notes

The repository keeps the existing architecture and benchmark outputs, with an additive audit layer for the HHGOA submission rubric. Each `cases/HHG-001.json` through `cases/HHG-020.json` now records the NBA before additional evidence, the controlled evidence request (when needed), and the post-evidence state or explicit conditional simulation branches. The same fields are mirrored in `answers/`.

Run `python scripts/submission_check.py` before publishing. The generated `tigergraph/generated/benchmark_case_writeback.gsql` contains the 20-case graph writeback payload. The JSON manifest intentionally says `ready_for_tigergraph_writeback` rather than claiming a remote TigerGraph write unless the team executes the GSQL against its configured Savanna/Community Edition deployment.
