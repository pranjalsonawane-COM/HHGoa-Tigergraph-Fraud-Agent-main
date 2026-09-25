# Phase 1 Data Validation & Verification Report

**Project:** TigerGraph Agentic Fraud Investigation (HHGOA IEEE-CIS)  
**Execution Phase:** Phase 1 (Data Preparation & Deterministic Preprocessing)  
**Validation Status:** **PASSED (100% Deterministic Resolution)**  
**Generated On:** 2026-09-19  

---

## 1. Executive Summary

Phase 1 data preparation and preprocessing has been completed with **zero discrepancies**. The pipeline transforms the raw 708 MB dataset into compact, normalized, graph-ready entities and edge sets while preserving 100% integrity across all 590,742 transactions, 144,432 identity records, 5,565 historical closed cases, and all 20 benchmark evaluation cases.

### Key Validation Highlights
- **Benchmark Resolution:** **20 / 20 benchmark cases (100.0%)** resolve to their exact expected `customer_id` and `card_id`.
- **Historical Labeled Cases:** **14,955 / 14,955 transaction references (100.0%)** in closed cases resolve with 0 mismatches.
- **Identity Joins:** **144,432 / 144,432 online identity records (100.0%)** joined seamlessly to `transactions.csv`.
- **TransactionID Integrity:** **590,742 unique IDs, 0 duplicates**.
- **Temporal Boundary & Leakage:** Strict temporal partition maintained. Maximum historical closed date is `2016-11-06 23:39:58`, strictly preceding the earliest benchmark investigation opening date (`2016-11-12 00:46:24`).

---

## 2. File & Entity Row / Column Statistics

### A. Raw vs. Processed Datasets

| Dataset / Entity | Source File | Processed File | Raw Rows / Cols | Processed Rows / Cols | Purpose in TigerGraph |
|---|---|---|---|---|---|
| **Transactions** | `transactions.csv` | `data/processed/transactions.csv` | 590,742 / 397 | 590,742 / 15 | `Transaction` Vertex |
| **Identities / Devices** | `identity.csv` | `data/processed/device_profiles.csv` | 144,432 / 41 | 9,708 / 7 | `DeviceProfile` Vertex |
| **Customers** | Aggregated | `data/processed/customers.csv` | — | 13,553 / 5 | `Customer` Vertex |
| **Cards** | Aggregated | `data/processed/cards.csv` | — | 14,850 / 10 | `Card` Vertex |
| **Billing Regions** | `transactions.csv` | `data/processed/billing_regions.csv` | — | 293 / 2 | `BillingRegion` Vertex |
| **Email Domains** | `transactions.csv` | `data/processed/email_domains.csv` | — | 60 / 2 | `EmailDomain` Vertex |
| **Historical Cases** | `closed_cases_history.csv` | `data/processed/historical_cases.csv` | 5,565 / 15 | 5,565 / 13 | `ClosedCase` Vertex |
| **Benchmark Cases** | `case_pack.csv` | `data/processed/benchmark_cases.csv` | 20 / 8 | 20 / 8 | Evaluation Benchmark |

### B. Graph Edge Files Generated

| Edge Name | Source Vertex | Target Vertex | Processed File | Edge Count | Integrity Check |
|---|---|---|---|---|---|
| `OWNS` | `Customer` | `Card` | `data/processed/edges_owns.csv` | 14,850 | 100% valid foreign keys |
| `MADE` | `Card` | `Transaction` | `data/processed/edges_made.csv` | 590,742 | 100% valid foreign keys |
| `FROM_DEVICE` | `Transaction` | `DeviceProfile` | `data/processed/edges_from_device.csv` | 144,432 | Online transactions only |
| `BILLED_IN` | `Transaction` | `BillingRegion` | `data/processed/edges_billed_in.csv` | 525,026 | Billed region records |
| `EMAIL` | `Transaction` | `EmailDomain` | `data/processed/edges_email.csv` | 741,407 | Purchaser & recipient roles |
| `NEXT` | `Transaction` | `Transaction` | `data/processed/edges_next.csv` | 575,892 | Chronological card chains |
| `INVOLVES` | `ClosedCase` | `Transaction` | `data/processed/edges_case_involves.csv` | 14,955 | Historical case transactions |
| `CASE_CARD` | `ClosedCase` | `Card` | `data/processed/edges_case_card.csv` | 5,571 | `on_card` & `connected_to` |

---

## 3. Benchmark Case Validation Audit (20/20 Match)

Every transaction flagged in `case_pack.csv` was verified against `data/processed/transactions.csv` to confirm exact resolution of `customer_id` and `card_id`.

| Case ID | Flagged Txn ID | Expected Customer | Resolved Customer | Expected Card ID | Resolved Card ID | Match Status |
|---|---|---|---|---|---|---|
| **HHG-001** | `3514030` | `C12382` | `C12382` | `C12382-K1` | `C12382-K1` | **MATCH** |
| **HHG-002** | `3478782` | `C11891` | `C11891` | `C11891-K1` | `C11891-K1` | **MATCH** |
| **HHG-003** | `3530164` | `C08623` | `C08623` | `C08623-K2` | `C08623-K2` | **MATCH** |
| **HHG-004** | `3583227` | `C08106` | `C08106` | `C08106-K1` | `C08106-K1` | **MATCH** |
| **HHG-005** | `3523199` | `C02923` | `C02923` | `C02923-K1` | `C02923-K1` | **MATCH** |
| **HHG-006** | `3476682` | `C07297` | `C07297` | `C07297-K1` | `C07297-K1` | **MATCH** |
| **HHG-007** | `3514948` | `C09933` | `C09933` | `C09933-K2` | `C09933-K2` | **MATCH** |
| **HHG-008** | `3558054` | `C13171` | `C13171` | `C13171-K2` | `C13171-K2` | **MATCH** |
| **HHG-009** | `3581141` | `C08299` | `C08299` | `C08299-K1` | `C08299-K1` | **MATCH** |
| **HHG-010** | `3506725` | `C10434` | `C10434` | `C10434-K1` | `C10434-K1` | **MATCH** |
| **HHG-011** | `3583368` | `C11923` | `C11923` | `C11923-K2` | `C11923-K2` | **MATCH** |
| **HHG-012** | `3553342` | `C05876` | `C05876` | `C05876-K2` | `C05876-K2` | **MATCH** |
| **HHG-013** | `3526826` | `C07671` | `C07671` | `C07671-K2` | `C07671-K2` | **MATCH** |
| **HHG-014** | `3478561` | `C13487` | `C13487` | `C13487-K1` | `C13487-K1` | **MATCH** |
| **HHG-015** | `3464869` | `C03042` | `C03042` | `C03042-K1` | `C03042-K1` | **MATCH** |
| **HHG-016** | `3534820` | `C09988` | `C09988` | `C09988-K1` | `C09988-K1` | **MATCH** |
| **HHG-017** | `3450629` | `C04570` | `C04570` | `C04570-K1` | `C04570-K1` | **MATCH** |
| **HHG-018** | `3491361` | `C02354` | `C02354` | `C02354-K2` | `C02354-K2` | **MATCH** |
| **HHG-019** | `3503878` | `C07987` | `C07987` | `C07987-K2` | `C07987-K2` | **MATCH** |
| **HHG-020** | `3509359` | `C12265` | `C12265` | `C12265-K2` | `C12265-K2` | **MATCH** |

---

## 4. Card & Identity Mapping Validation

### A. Card Mapping (`CardMapper`)
- **Total Unique Signatures Processed:** 14,893 distinct `(customer_id, card1..card6)` combinations across 590,742 transactions.
- **Labeled Historical Signatures:** 1,960 signatures verified against ground truth in closed cases.
- **Signature Inconsistencies:** **0**. For every customer, each specific combination of card metadata maps 1-to-1 with a single card entity.
- **Card Suffixes Assigned:**
  - `K1`: 13,553 cards (primary/first seen card per customer)
  - `K2`: 1,289 cards (secondary card/reissue per customer)
  - `K3`: 8 cards (tertiary card per customer)
  - **Total Unique Cards:** 14,850

### B. Device Profile Mapping (`DeviceMapper`)
- **Total Identity Records Ingested:** 144,432 online transactions.
- **Canonical Normalization:** Whitespace trimmed, casing normalized, missing components handled as `"Unknown"`.
- **Total Canonical Device Profiles:** 9,708 profiles.
- **Deterministic ID Generation:** `DEV_<12-hex-sha256-digest>`.

---

## 5. Temporal Partition & Anti-Leakage Audit

To satisfy competition rules and prevent forward data leakage:
- **Historical Case Memory Span:** July 2, 2016 (`2016-07-02 07:17:26`) to November 6, 2016 (`2016-11-06 23:39:58`).
- **Benchmark Evaluation Span:** November 12, 2016 (`2016-11-12 00:46:24`) to December 29, 2016 (`2016-12-29 07:53:54`).
- **Temporal Gap:** A clean 6-day buffer exists between historical case closure and the first benchmark trigger.
- **Leakage Status:** **ZERO LEAKAGE CONFIRMED.** Benchmark case outcomes are completely isolated and never used in feature building or case memory ingestion.

---

## 6. Pipeline Verification Test Suite Results

A test suite (`tests/test_preprocessing.py`) was executed to confirm idempotency and deterministic behavior:
- `test_benchmark_resolutions`: PASS
- `test_reproducibility`: PASS
- `test_normalization_and_hash`: PASS
- `test_missing_values`: PASS
- `test_partial_missing`: PASS

**Test Suite Summary:** `Ran 5 tests in 30.9s -> OK`
