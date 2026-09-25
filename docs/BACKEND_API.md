# Backend REST API Server Documentation

## 1. Overview

The **TigerGraph Fraud Investigation Backend** (`backend/server.py`) provides a zero-dependency, production-grade REST API server built using Python's standard HTTP libraries. It exposes clean JSON endpoints for agent orchestration, case retrieval, live graph topology streaming, interactive evidence simulation, and serves the frontend dashboard.

---

## 2. API Endpoints

### 1. `GET /health`
Returns service health status.

### 2. `GET /api/stats`
Returns system-wide aggregate metrics:
- Total benchmark cases (20)
- Confirmed fraud, uncertain, and cleared breakdown
- SAR filings count
- Total financial loss exposure mitigated ($)
- Total graph vertices (634,810) and edges (2,505,246)
- Historical case memory size (5,565 closed cases)

### 3. `GET /api/cases`
Lists all 20 benchmark evaluation cases with high-level summary cards (verdict, pattern, exposure, approval route, SAR status).

### 4. `GET /api/cases/{case_id}`
Retrieves the comprehensive investigation dossier for a case:
- Entity identities (`customer_id`, `card_id`, `flagged_txn_id`)
- Detected fraud pattern & evidence claims
- Policy rule compliance (R1–R10)
- Multi-step ReAct trace
- Complete operational playbook
- FinCEN SAR narrative

### 5. `POST /api/investigate`
Runs autonomous end-to-end multi-hop GraphRAG investigation on any arbitrary transaction ID on demand.
```json
{
  "transaction_id": "3478561",
  "customer_id": "C13487",
  "card_id": "C13487-K1"
}
```

### 6. `POST /api/simulate-evidence`
Applies simulated evidence to resolve uncertain cases dynamically.
```json
{
  "case_id": "HHG-001",
  "action_type": "customer_contact",
  "outcome_code": "travel_confirmed",
  "evidence_notes": "Cardholder confirmed travel to region 444.0"
}
```

### 7. `GET /api/graph/{transaction_id}`
Returns node and link data (vertices, edges, colors, multi-card device links) formatted for interactive graph canvas rendering in the UI.

---

## 3. Starting the Backend Server

```bash
python backend/server.py
```
Default URL: `http://localhost:8000`
