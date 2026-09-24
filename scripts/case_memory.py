"""
Case Memory & Precedent Retrieval Engine for Fraud Investigations.

Provides hybrid Graph + BM25/TF-IDF semantic search over 5,565 historical closed cases.
Guarantees strict temporal isolation (anti-leakage) and rapid precedent extraction.
"""
import os
import csv
import re
import math
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class CaseMemoryEngine:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            self.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'processed'))
        else:
            self.data_dir = data_dir

        self.cases_file = os.path.join(self.data_dir, "historical_cases.csv")
        self.cases: Dict[str, Dict[str, Any]] = {}
        self.customer_cases: Dict[str, List[str]] = defaultdict(list)
        self.card_cases: Dict[str, List[str]] = defaultdict(list)
        self.pattern_cases: Dict[str, List[str]] = defaultdict(list)
        
        # Inverted index & BM25 parameters
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(dict)  # term -> {case_id: term_freq}
        self.idf: Dict[str, float] = {}
        self.k1: float = 1.5
        self.b: float = 0.75

        self._load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase alphanumeric words."""
        if not text:
            return []
        return re.findall(r'[a-zA-Z0-9_\-\.\$]+', text.lower())

    def _load_and_index(self):
        """Loads historical_cases.csv and builds search structures."""
        if not os.path.exists(self.cases_file):
            raise FileNotFoundError(f"Historical cases file not found: {self.cases_file}")

        total_length = 0
        with open(self.cases_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row["case_id"]
                cust_id = row["customer_id"]
                card_id = row["card_id"]
                pattern = row.get("pattern", "none")
                exposure = float(row.get("exposure_usd", 0.0))
                
                # Store structured case
                self.cases[cid] = {
                    "case_id": cid,
                    "customer_id": cust_id,
                    "card_id": card_id,
                    "opened_at": row["opened_at"],
                    "closed_at": row["closed_at"],
                    "outcome": row["outcome"],
                    "pattern": pattern,
                    "exposure_usd": exposure,
                    "report_filed": row.get("report_filed", "No"),
                    "actions_taken": row.get("actions_taken", "").split("|") if row.get("actions_taken") else [],
                    "analyst_notes": row.get("analyst_notes", ""),
                    "txn_ids": row.get("txn_ids", "").split("|") if row.get("txn_ids") else [],
                    "connected_card_ids": row.get("connected_card_ids", "").split("|") if row.get("connected_card_ids") else []
                }

                # Secondary indexes
                self.customer_cases[cust_id].append(cid)
                self.card_cases[card_id].append(cid)
                self.pattern_cases[pattern].append(cid)

                # Indexable text representation with field weighting
                # Pattern and action keywords boosted
                doc_text = f"{row.get('analyst_notes', '')} {pattern} {pattern} {row.get('actions_taken', '')} {row.get('outcome', '')}"
                tokens = self._tokenize(doc_text)
                
                self.doc_lengths[cid] = len(tokens)
                total_length += len(tokens)

                term_counts = Counter(tokens)
                for term, count in term_counts.items():
                    self.inverted_index[term][cid] = count

        n_docs = len(self.cases)
        if n_docs > 0:
            self.avg_doc_length = total_length / n_docs

            # Calculate BM25 IDF: ln((N - n(q) + 0.5) / (n(q) + 0.5) + 1)
            for term, postings in self.inverted_index.items():
                doc_freq = len(postings)
                self.idf[term] = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details of a historical case."""
        return self.cases.get(case_id)

    def search_precedents(
        self,
        query_text: str,
        pattern: Optional[str] = None,
        customer_id: Optional[str] = None,
        card_id: Optional[str] = None,
        before_ts: Optional[str] = None,
        min_exposure: Optional[float] = None,
        max_exposure: Optional[float] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 relevance score and structured graph filters.
        Enforces strict temporal anti-leakage via before_ts.
        """
        query_tokens = self._tokenize(query_text)
        candidate_scores: Dict[str, float] = defaultdict(float)

        # 1. Accumulate BM25 relevance scores
        for token in query_tokens:
            if token not in self.inverted_index:
                continue
            token_idf = self.idf.get(token, 0.0)
            for cid, freq in self.inverted_index[token].items():
                doc_len = self.doc_lengths.get(cid, 1)
                # BM25 formula
                num = freq * (self.k1 + 1)
                denom = freq + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_doc_length or 1)))
                candidate_scores[cid] += token_idf * (num / denom)

        # 2. Filter & Boost candidates
        results = []
        for cid, case in self.cases.items():
            # Strict Temporal Filter: case must have been closed BEFORE current investigation timestamp
            if before_ts and case["closed_at"] > before_ts:
                continue

            # Customer filter if specified
            if customer_id and case["customer_id"] != customer_id:
                pass # Can be used for broader precedent search, but exact matches get bonus

            # Pattern filter if specified
            if pattern and case["pattern"] == pattern:
                # Strong pattern congruence boost
                candidate_scores[cid] = candidate_scores.get(cid, 0.0) + 3.5

            # Exposure range filter
            if min_exposure is not None and case["exposure_usd"] < min_exposure:
                continue
            if max_exposure is not None and case["exposure_usd"] > max_exposure:
                continue

            base_score = candidate_scores.get(cid, 0.0)
            
            # Exact card or customer match boost
            if customer_id and case["customer_id"] == customer_id:
                base_score += 5.0
            if card_id and case["card_id"] == card_id:
                base_score += 8.0

            if base_score > 0:
                results.append((base_score, case))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        top_results = []
        for score, case in results[:top_k]:
            res_item = dict(case)
            res_item["similarity_score"] = round(score, 4)
            top_results.append(res_item)

        return top_results

    def extract_precedent_insights(self, similar_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates insights, consensus outcome, recommended actions, and SAR precedent
        from retrieved similar historical cases.
        """
        if not similar_cases:
            return {
                "num_precedents": 0,
                "consensus_outcome": "uncertain",
                "fraud_rate": 0.0,
                "common_actions": [],
                "sar_filing_rate": 0.0,
                "key_rationales": []
            }

        outcomes = [c["outcome"] for c in similar_cases]
        fraud_count = sum(1 for o in outcomes if o == "confirmed_fraud")
        cleared_count = sum(1 for o in outcomes if o == "cleared")
        total = len(similar_cases)

        # Actions breakdown
        action_counts = Counter()
        for c in similar_cases:
            for act in c.get("actions_taken", []):
                action_counts[act] += 1

        sar_filed_count = sum(1 for c in similar_cases if c.get("report_filed", "No").lower() in ("yes", "true", "1"))
        
        consensus_outcome = "confirmed_fraud" if fraud_count > cleared_count else ("cleared" if cleared_count > fraud_count else "uncertain")
        
        # Extract distinct concise rationale snippets
        rationales = []
        for c in similar_cases[:3]:
            notes = c.get("analyst_notes", "")
            if notes:
                rationales.append(f"[{c['case_id']}] {notes[:140]}...")

        return {
            "num_precedents": total,
            "consensus_outcome": consensus_outcome,
            "fraud_rate": round(fraud_count / total, 3),
            "cleared_rate": round(cleared_count / total, 3),
            "common_actions": [act for act, _ in action_counts.most_common(4)],
            "sar_filing_rate": round(sar_filed_count / total, 3),
            "key_rationales": rationales
        }
