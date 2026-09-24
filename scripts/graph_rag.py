"""
GraphRAG Multi-Hop Evidence & Policy Retrieval Engine.

Integrates TigerGraph graph traversal, Pattern Detection (R1-R10),
Case Memory semantic search, and Policy Rules into a unified, hallucination-proof context generator.
"""
import os
import sys
from typing import Dict, Any, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.query_engine import GraphQueryEngine
from scripts.pattern_detector import FraudPatternDetector
from scripts.case_memory import CaseMemoryEngine
from scripts.policy_engine import FraudPolicyEngine

class GraphRAGEngine:
    """Master GraphRAG orchestrator for fraud investigations."""

    def __init__(self, data_dir: Optional[str] = None):
        self.query_engine = GraphQueryEngine(data_dir=data_dir)
        self.case_memory = CaseMemoryEngine(data_dir=data_dir)
        self.policy_engine = FraudPolicyEngine()

    def investigate_alert(
        self,
        transaction_id: str,
        customer_id: Optional[str] = None,
        card_id: Optional[str] = None,
        alert_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full multi-hop GraphRAG investigation pipeline for a flagged transaction or alert.
        """
        # 1. Fetch Hop-1 Transaction & Neighborhood Context
        txn_ctx = self.query_engine.get_transaction_context(transaction_id)
        t = txn_ctx.get("transaction", {})
        
        target_cust_id = customer_id or t.get("customer_id", "") or txn_ctx.get("customer_id", "")
        target_card_id = card_id or t.get("card_id", "") or txn_ctx.get("card_id", "")
        txn_ts = alert_timestamp or t.get("ts", "") or txn_ctx.get("timestamp", "")
        dev_id = t.get("device_id", "") or txn_ctx.get("device_id", "")

        # 2. Fetch Hop-2 Graph Entities
        cust_profile = self.query_engine.get_customer_profile(target_cust_id) if target_cust_id else {}
        card_window = self.query_engine.get_card_window(target_card_id, transaction_id, window_hours=24) if target_card_id else {}
        device_sharing = self.query_engine.check_device_sharing(dev_id, transaction_id, target_card_id, lookback_days=0) if dev_id else {
            "device_id": "", "canonical_profile_str": "", "number_of_distinct_cards": 0,
            "number_of_distinct_customers": 0, "shared_cards": [], "connected_historical_cases": []
        }
        region_disc = self.query_engine.check_region_discrepancy(target_cust_id, transaction_id) if target_cust_id else {}
        prior_cases = self.query_engine.find_connected_prior_cases(
            target_cust_id, target_card_id, dev_id, before_ts=txn_ts
        )

        # 3. Fraud Pattern Detection
        pattern_res = FraudPatternDetector.detect_fraud_pattern(
            txn_ctx, cust_profile, card_window, device_sharing, region_disc, prior_cases
        )

        # 4. Semantic Case Memory Retrieval (with strict anti-leakage before_ts)
        query_text = (
            f"{pattern_res.get('pattern', '')} {t.get('channel', '')} "
            f"{device_sharing.get('canonical_profile_str', '')} "
            f"{t.get('product_cd', '')} {t.get('id_23', '')}"
        )
        precedents = self.case_memory.search_precedents(
            query_text=query_text,
            pattern=pattern_res.get("pattern"),
            customer_id=target_cust_id,
            card_id=target_card_id,
            before_ts=txn_ts,
            top_k=5
        )
        precedent_insights = self.case_memory.extract_precedent_insights(precedents)

        # 5. Fraud Policy Rule Evaluation (R1 - R10)
        policy_res = self.policy_engine.evaluate_policy(
            pattern_res, txn_ctx, cust_profile, device_sharing, precedent_insights
        )

        # 6. Synthesize Grounded GraphRAG Payload
        graph_rag_payload = {
            "transaction_id": transaction_id,
            "customer_id": target_cust_id,
            "card_id": target_card_id,
            "timestamp": txn_ts,
            "graph_context": {
                "transaction": txn_ctx,
                "customer_profile": cust_profile,
                "card_window": card_window,
                "device_sharing": device_sharing,
                "region_discrepancy": region_disc,
                "prior_connected_cases": prior_cases
            },
            "pattern_analysis": pattern_res,
            "case_memory": {
                "precedents": precedents,
                "insights": precedent_insights
            },
            "policy_compliance": policy_res,
            "summary": {
                "detected_pattern": pattern_res.get("pattern"),
                "fraud_probability": pattern_res.get("fraud_probability"),
                "exposure_usd": policy_res.get("exposure_usd"),
                "approval_route": policy_res.get("approval_route"),
                "sar_required": policy_res.get("sar_required"),
                "recommended_actions": policy_res.get("recommended_actions")
            }
        }

        # 7. Generate formatted text block for LLM prompts
        graph_rag_payload["grounded_prompt_context"] = self._format_prompt_context(graph_rag_payload)

        return graph_rag_payload

    def _format_prompt_context(self, payload: Dict[str, Any]) -> str:
        """Formats graph facts and policy citations into a structured Markdown text block."""
        s = payload["summary"]
        gc = payload["graph_context"]
        t = gc["transaction"].get("transaction", {})
        dev = gc["device_sharing"]
        reg = gc["region_discrepancy"]
        pat = payload["pattern_analysis"]
        pol = payload["policy_compliance"]
        mem = payload["case_memory"]["insights"]

        lines = [
            f"# GRAPHRAG INVESTIGATION DOSSIER: Transaction {payload['transaction_id']}",
            f"- **Customer ID:** {payload['customer_id']} | **Card ID:** {payload['card_id']}",
            f"- **Timestamp:** {payload['timestamp']} | **Amount:** ${float(t.get('amount', 0)):.2f} | **Channel:** {t.get('channel', 'N/A')}",
            f"- **Real-time Risk Score:** {t.get('risk_score', 'N/A')}",
            "",
            "## 1. Multi-Hop Graph Evidence",
            f"- **Device Profile:** {dev.get('canonical_profile_str', 'No device profile recorded')} ({dev.get('device_id', 'N/A')})",
            f"- **Device Sharing Links:** Shared across {dev.get('number_of_distinct_cards', 0)} cards and {dev.get('number_of_distinct_customers', 0)} customers",
            f"- **Connected Historical Cases:** {', '.join(dev.get('connected_historical_cases', [])) if dev.get('connected_historical_cases') else 'None'}",
            f"- **Billing Region:** {reg.get('current_region', 'N/A')} (Dominant Home Region: {reg.get('dominant_region', 'N/A')}, Discrepancy: {reg.get('region_changed', False)})",
            "",
            "## 2. Fraud Typology Analysis",
            f"- **Detected Typology:** `{pat.get('pattern')}` (Probability: {pat.get('fraud_probability', 0.0):.2f})",
            f"- **Pattern Description:** {pat.get('pattern_description') or 'Standard pattern matching behavioral signature'}",
            f"- **Affected Transactions:** {', '.join(pat.get('affected_txn_ids', []))}",
            "",
            "## 3. Policy Compliance & Approval Routing",
            f"- **Triggered Policy Rules:** {', '.join(pol.get('rule_ids', []))}",
            f"- **Approval Level:** `{pol.get('approval_route')}`",
            f"- **FinCEN SAR Required:** {'YES' if pol.get('sar_required') else 'NO'}",
            f"- **SAR Triggers:** {'; '.join(pol.get('sar_triggers', [])) if pol.get('sar_triggers') else 'None'}",
            f"- **Recommended Standard Actions:** {', '.join(pol.get('recommended_actions', []))}",
            "",
            "## 4. Case Memory Precedents",
            f"- **Historical Precedent Consensus:** `{mem.get('consensus_outcome')}` (Fraud Rate: {mem.get('fraud_rate', 0.0)*100:.1f}%)",
            f"- **Consensus Actions:** {', '.join(mem.get('common_actions', []))}",
            f"- **Key Historical Rationales:**"
        ]

        for rat in mem.get("key_rationales", []):
            lines.append(f"  - {rat}")

        return "\n".join(lines)
