# TigerGraph Connection & Deployment Guide

**Project:** TigerGraph Agentic Fraud Investigation (HHGOA IEEE-CIS)  
**Graph Name:** `FraudGraph`  
**Document Version:** 1.0  
**Updated:** 2026-09-19  

---

## 1. Connection Status & Environment Inspection

### Current Environment Status
- **Connection Status:** **NOT CONNECTED (Offline Validation Mode Active)**
- **Target Host:** Default localhost `http://127.0.0.1:9000` (no active local TigerGraph service detected on port 9000).
- **Environment Variables:** `TG_HOST`, `TG_USERNAME`, `TG_PASSWORD`, `TG_SECRET`, `TG_TOKEN` are not currently exported in the shell.
- **Local Preprocessed Data Status:** **READY (100% Validated in `data/processed/`)**.

---

## 2. Configuration Options for TigerGraph

To connect the agent and loading pipeline to a live TigerGraph instance (TigerGraph Cloud Savanna or Community Edition), choose one of the following methods:

### Option A: Configuration File (`tigergraph/config.json`)
Create a file at `tigergraph/config.json` (this file is automatically gitignored to protect credentials):

```json
{
  "host": "https://your-instance.i.tgcloud.io",
  "restpp_port": "9000",
  "gsql_port": "14240",
  "graph_name": "FraudGraph",
  "username": "tigergraph",
  "password": "YOUR_SECURE_PASSWORD",
  "secret": "YOUR_GRAPH_SECRET",
  "token": "YOUR_RESTPP_TOKEN",
  "use_tls": true
}
```

### Option B: Environment Variables
Export the following environment variables in your terminal before running commands:

```bash
# Windows PowerShell
$env:TG_HOST="https://your-instance.i.tgcloud.io"
$env:TG_USERNAME="tigergraph"
$env:TG_PASSWORD="YOUR_SECURE_PASSWORD"
$env:TG_GRAPH="FraudGraph"
$env:TG_SECRET="YOUR_GRAPH_SECRET"
$env:TG_USE_TLS="true"

# Linux / macOS Bash
export TG_HOST="https://your-instance.i.tgcloud.io"
export TG_USERNAME="tigergraph"
export TG_PASSWORD="YOUR_SECURE_PASSWORD"
export TG_GRAPH="FraudGraph"
export TG_SECRET="YOUR_GRAPH_SECRET"
export TG_USE_TLS="true"
```

---

## 3. Schema & Data Deployment Commands

When connected to a live TigerGraph instance, execute the following commands in sequence:

### Step 1: Deploy Schema
Using the GSQL Web Console or GSQL CLI:
```bash
gsql tigergraph/schema/schema.gsql
```
*Creates vertex types (`Customer`, `Card`, `Transaction`, `DeviceProfile`, `BillingRegion`, `EmailDomain`, `ClosedCase`) and directed edges (`OWNS`, `MADE`, `FROM_DEVICE`, `BILLED_IN`, `PURCHASER_EMAIL`, `RECIPIENT_EMAIL`, `NEXT`, `INVOLVES`, `ON_CARD`, `CONNECTED_TO`).*

### Step 2: Deploy Loading Job
```bash
gsql tigergraph/schema/loading_jobs.gsql
```
*Compiles the high-throughput loading job `load_fraud_graph` for `FraudGraph`.*

### Step 3: Run the High-Throughput Loading Job
```bash
gsql 'RUN LOADING JOB load_fraud_graph USING 
    f_cust="data/processed/customers.csv",
    f_cards="data/processed/cards.csv",
    f_txns="data/processed/transactions.csv",
    f_devs="data/processed/device_profiles.csv",
    f_regs="data/processed/billing_regions.csv",
    f_emails="data/processed/email_domains.csv",
    f_hist_cases="data/processed/historical_cases.csv",
    f_e_owns="data/processed/edges_owns.csv",
    f_e_made="data/processed/edges_made.csv",
    f_e_from_dev="data/processed/edges_from_device.csv",
    f_e_billed_in="data/processed/edges_billed_in.csv",
    f_e_email="data/processed/edges_email.csv",
    f_e_next="data/processed/edges_next.csv",
    f_e_case_inv="data/processed/edges_case_involves.csv",
    f_e_case_card="data/processed/edges_case_card.csv"'
```

---

## 4. Automated Python Deployment Utility

You can also run our automated deployment script:
```bash
python scripts/deploy_tigergraph.py
```
This script automatically pings the instance, validates authentication, applies the GSQL schema, runs the loading job, and executes graph verification checks.
