# Historical Case Memory & Precedent Indexing

## 1. Overview

The **Case Memory Engine** (`scripts/case_memory.py`) provides hybrid graph-filtered and semantic BM25 precedent retrieval over the complete repository of **5,565 closed historical fraud cases** (`data/processed/historical_cases.csv`).

In complex and borderline fraud investigations, historical precedents provide strong grounding for:
1. **Consensus Outcome:** Whether similar patterns historically resulted in `confirmed_fraud` or `cleared`.
2. **Action Standard of Care:** Recommended actions (e.g., `BLOCK_CARD`, `CREATE_CASE`, `VERIFY_WITH_CUSTOMER`, `FILE_SAR`).
3. **SAR Filing Benchmark:** Precedents involving organized rings or >$10,000 exposure with regulatory reporting requirements.
4. **Analyst Rationale Reuse:** Structuring defensible, FinCEN-compliant narratives based on verified historical findings.

---

## 2. Architecture & Indexing Strategy

```
                          Historical Cases (5,565)
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
   Structured Secondary Indexes                BM25 Inverted Term Index
  ┌───────────────────────────┐               ┌───────────────────────────┐
  │ - Customer ID → [Case IDs]│               │ - Term → {DocID: TF}      │
  │ - Card ID → [Case IDs]    │               │ - IDF Calculation (BM25)  │
  │ - Pattern → [Case IDs]    │               │ - Document Length Normaliz│
  │ - Exposure Range Filter   │               │ - Field Boosts (Notes x2, │
  │ - Strict `before_ts` Cutoff│              │   Pattern x3.5, Actions)  │
  └─────────────┬─────────────┘               └─────────────┬─────────────┘
                │                                           │
                └─────────────────────┬─────────────────────┘
                                      ▼
                        Hybrid Ranker & Insight Extractor
                                      │
                                      ▼
                      Consensus Outcome, Actions & Precedents
```

### Key Parameters:
- **BM25 $k_1$:** 1.5 (term frequency saturation).
- **BM25 $b$:** 0.75 (document length penalization).
- **Field Boosts:** Pattern congruence (+3.5), same-customer (+5.0), same-card (+8.0).

---

## 3. Strict Anti-Leakage Temporal Filtering

To prevent look-ahead bias and data leakage during benchmark evaluations:
- The parameter `before_ts` is strictly enforced:
  $$\text{case.closed\_at} \le \text{before\_ts}$$
- Future closed cases (even if highly similar) are mathematically excluded from the candidate pool during active investigations.

---

## 4. Performance Benchmarks

| Metric | Result | Target |
| :--- | :--- | :--- |
| **Total Indexed Documents** | 5,565 cases | 5,565 cases |
| **Vocabulary Size** | > 1,000 distinct tokens | > 500 tokens |
| **Query Latency** | **< 1.5 ms** | < 25 ms |
| **Memory Footprint** | ~ 4.2 MB | < 50 MB |
| **Zero External Dependencies** | 100% Python Standard Library | Standard Library |

---

## 5. Usage Example

```python
from scripts.case_memory import CaseMemoryEngine

memory = CaseMemoryEngine()

# Search precedents for a suspicious transaction
precedents = memory.search_precedents(
    query_text="SM-G935F anonymous proxy shared device ring",
    pattern="undocumented",
    before_ts="2016-11-22 16:11:00",
    top_k=5
)

# Extract consensus insights
insights = memory.extract_precedent_insights(precedents)
print(insights["consensus_outcome"]) # "confirmed_fraud"
print(insights["common_actions"])    # ["CREATE_CASE", "BLOCK_CARD"]
```
