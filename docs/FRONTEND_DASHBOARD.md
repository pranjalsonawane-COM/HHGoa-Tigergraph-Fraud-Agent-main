# Interactive Web UI Dashboard

## 1. Overview

The **TigerGraph Agentic Fraud Dashboard** (`frontend/index.html`, `frontend/style.css`, `frontend/app.js`) is a modern web application designed for fraud analysts and compliance managers.

Built using HTML5, Vanilla CSS (rich sleek dark mode, glassmorphism, glowing risk indicators), and Vanilla JavaScript, it offers zero-latency interactive investigation workflows, real-time graph visualization, and interactive evidence gathering.

---

## 2. Key Interface Components

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ TigerGraph FraudAgent [LIVE CE]                Search: [ Enter Txn ID... ] [Investigate] │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ BENCHMARK CASES: 20 | FRAUD: 12 | UNCERTAIN: 7 | SAR FILINGS: 1 | EXPOSURE: $1,698,599    │
├───────────────────────────┬─────────────────────────────────────────────────────────────┤
│ Case Explorer             │ Case HHG-014 Dossier  [CONFIRMED_FRAUD]  [L2_SENIOR_MANAGER]   │
│ [All] [Fraud] [Uncertain] │ Amount: $74.96  |  Confidence: 88%  |  SAR: YES (Mandatory)     │
│ ┌───────────────────────┐ │ ┌─────────────────────────────────────────────────────────┐ │
│ │ HHG-014 [FRAUD] [SAR] │ │ │ TigerGraph Multi-Hop Neighborhood Subgraph Canvas       │ │
│ │ Txn #3478561  $74.96  │ │ │ (Interactive nodes: Txn, Card, Customer, Device, Ring) │ │
│ ├───────────────────────┤ │ └─────────────────────────────────────────────────────────┘ │
│ │ HHG-001 [UNCERTAIN]   │ │ [Multi-Hop Evidence] [ReAct Trace] [NBA Playbook] [SAR]     │
│ │ Txn #3514030  $77.07  │ │ ┌───────────────────────────────────────────────────────┐   │
│ └───────────────────────┘ │ │ Primary Action: BLOCK_ALL_LINKED_CARDS_AND_FILE_SAR     │   │
│                           │ └───────────────────────────────────────────────────────┘   │
└───────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 3. Features & Interactive Workflows

1. **Benchmark Metrics Banner:** Displays real-time aggregate statistics (Total cases, Confirmed Fraud %, Uncertain count, FinCEN SAR filing count, Total mitigated exposure).
2. **Case Explorer & Filters:** Instant filtering by case status (`All`, `Fraud`, `Uncertain`, `SAR`).
3. **Interactive Graph Topology Canvas:** Real-time radial rendering of central transactions, cards, customers, devices, and multi-card syndicate links.
4. **Multi-Hop Evidence Inspector:** Displays grounded graph evidence claims with exact GSQL query citations and entity IDs.
5. **ReAct Trace Stepper:** Step-by-step audit log of the agent's 7-stage reasoning cycle.
6. **Next Best Action Operational Playbook:** Multi-tier operational directives covering containment, customer SMS copy, chargebacks, and compliance sign-off.
7. **FinCEN SAR Narrative Viewer:** One-click copy for formal regulatory filings.
8. **Interactive Evidence Gathering Simulator:** Test dynamic case re-evaluations live by simulating customer travel confirmation (`cleared`) or fraud confirmation (`confirmed_fraud`).
9. **On-Demand Transaction Investigator:** Input any transaction ID to run live multi-hop GraphRAG investigations.

---

## 4. Launching the Dashboard

1. Start the backend REST API server:
   ```bash
   python backend/server.py
   ```
2. Open your web browser to:
   `http://localhost:8000`
