# GraphRAG Multi-Hop & Policy Engine

## 1. Overview

The **GraphRAG Engine** (`scripts/graph_rag.py`) is the core contextual intelligence engine powering the autonomous fraud investigation agent.

Rather than relying purely on vector similarity or unstructured document search, GraphRAG orchestrates a **3-Tier Grounding Pipeline**:
1. **Topological Multi-Hop Graph Traversal** (via TigerGraph RESTPP / GSQL): Extracts neighborhood subgraphs, device sharing links, temporal card windows, and connected historical fraud cases.
2. **Behavioral Typology & Pattern Detection** (`scripts/pattern_detector.py`): Categorizes anomalies into precise fraud signatures (Card Testing, Out-of-Region, Device Syndicate, etc.).
3. **Semantic Case Memory & Policy Grounding** (`scripts/case_memory.py` & `scripts/policy_engine.py`): Retrieves historical case precedents with consensus outcomes, standard-of-care actions, and evaluates strict governance rules (R1 through R10).

---

## 2. Multi-Hop Investigation Architecture

```
                                  INCOMING ALERT
                                (Transaction ID)
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
         Hop-1: Immediate Context              Hop-2: Graph Traversal
     ┌──────────────────────────────┐      ┌──────────────────────────────┐
     │ - Transaction Details & Risk │      │ - Customer Spending Baseline │
     │ - Direct Card / Customer     │      │ - Multi-Card Device Links    │
     │ - Device Profile & Proxy     │      │ - Billing Region Discrepancy │
     │ - Billing Region & Emails    │      │ - 24hr Card Velocity Window  │
     └──────────────┬───────────────┘      └──────────────┬───────────────┘
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       ▼
                   Hop-3: Pattern & Precedent Grounding
     ┌────────────────────────────────────────────────────────────────────┐
     │ 1. Fraud Typology Classifier (Card Testing, Syndicate, ATO, etc.)  │
     │ 2. Semantic Case Memory Precedents (Top-5 with strict anti-leakage)│
     │ 3. Fraud Policy v1.0 Rules Engine (R1 - R10)                       │
     └─────────────────────────────────┬──────────────────────────────────┘
                                       ▼
                     Unified Hallucination-Proof Dossier
                   & Grounded LLM Prompt Context Generation
```

---

## 3. Fraud Policy v1.0 Governance Rules (R1–R10)

| Rule ID | Rule Name | Trigger Condition | Mandatory Outcome / Action |
| :--- | :--- | :--- | :--- |
| **R1** | High Risk Model Score | $\text{risk\_score} \ge 0.60$ | Formal alert progression & investigation |
| **R2** | Out-of-Region Flagging | In-person charge in new billing region | Trigger out-of-region review protocol |
| **R3** | Out-of-Region Resolution | Travel confirmed vs unconfirmed | Clear alert vs confirm fraud & block card |
| **R4** | Card Testing Remediation | Micro-auth burst followed by high-ticket | Automated defensive card block (`auto`) |
| **R5** | CNP New Device Verification | Online purchase from unseen device (`id_15='New'`) | Step-up authentication / customer verification |
| **R6** | Shared Device Syndicate | $\ge 3$ cards sharing device or anonymous proxy | Block all linked cards, escalate to L2, file SAR |
| **R7** | Case Exposure Summation | All affected fraud transaction amounts | Loss summation across breach window |
| **R8** | Approval Hierarchy | Risk, Exposure, Syndicate involvement | Routing: `auto` vs `L1_analyst` vs `L2_senior_manager` |
| **R9** | FinCEN SAR Filing | $\text{exposure} \ge \$10,000$ OR multi-party syndicate | Mandatory SAR narrative filing |
| **R10** | Step-Up Verification | Uncertain signals | Contact cardholder / simulated evidence |

---

## 4. Grounded LLM Output Structure

The GraphRAG engine produces a formatted Markdown dossier passed directly to the LLM agent, guaranteeing that every assertion, entity link, and SAR narrative is backed by verifiable graph and policy evidence.
