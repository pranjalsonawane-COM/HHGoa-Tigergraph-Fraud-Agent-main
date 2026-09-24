"""
Autonomous Multi-Step AI Agent Core for Fraud Investigation.

Implements an autonomous ReAct State Machine:
Alert Ingestion -> Multi-Hop Traversal -> Pattern Reasoning -> Case Memory ->
Policy Evaluation -> Uncertainty Assessment -> Next Best Action -> SAR Narrative -> Resolution.
"""
import os
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.graph_rag import GraphRAGEngine
from scripts.case_memory import CaseMemoryEngine
from scripts.policy_engine import FraudPolicyEngine

class FraudInvestigationAgent:
    """Autonomous ReAct AI Agent for Fraud Investigation and Next-Best Action."""

    def __init__(self, data_dir: Optional[str] = None):
        self.graph_rag = GraphRAGEngine(data_dir=data_dir)
        self.case_memory = CaseMemoryEngine(data_dir=data_dir)
        self.policy_engine = FraudPolicyEngine()

    def run_investigation(
        self,
        case_id: str,
        trigger_type: str,
        trigger_text: str,
        flagged_txn_id: str,
        card_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        opened_at: Optional[str] = None,
        initial_risk_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes full autonomous multi-step investigation pipeline for an alert case.
        """
        trace_steps: List[Dict[str, Any]] = []

        # --- STEP 1: ALERT INGESTION ---
        step1_desc = f"Ingested alert {case_id} ({trigger_type}): {trigger_text}"
        trace_steps.append({
            "step": 1,
            "phase": "ALERT_INGESTION",
            "action": "ingest_alert",
            "observation": {
                "case_id": case_id,
                "trigger_type": trigger_type,
                "trigger_text": trigger_text,
                "flagged_txn_id": flagged_txn_id,
                "card_id": card_id,
                "customer_id": customer_id,
                "opened_at": opened_at,
                "risk_score": initial_risk_score
            }
        })

        # --- STEP 2: MULTI-HOP GRAPHRAG TRAVERSAL ---
        dossier = self.graph_rag.investigate_alert(
            transaction_id=flagged_txn_id,
            customer_id=customer_id,
            card_id=card_id,
            alert_timestamp=opened_at
        )
        gc = dossier["graph_context"]
        t = gc["transaction"].get("transaction", {})
        cust_prof = gc["customer_profile"]
        dev_sharing = gc["device_sharing"]
        reg_disc = gc["region_discrepancy"]

        trace_steps.append({
            "step": 2,
            "phase": "GRAPH_TRAVERSAL",
            "action": "traverse_neighborhood",
            "observation": {
                "customer_id": dossier["customer_id"],
                "card_id": dossier["card_id"],
                "amount": float(t.get("amount", 0.0) or 0.0),
                "channel": t.get("channel", "N/A"),
                "device_id": dev_sharing.get("device_id", "N/A"),
                "device_cards_count": dev_sharing.get("number_of_distinct_cards", 0),
                "region_discrepancy": reg_disc.get("region_changed", False),
                "connected_historical_cases": dev_sharing.get("connected_historical_cases", [])
            }
        })

        # --- STEP 3: FRAUD PATTERN REASONING ---
        pat = dossier["pattern_analysis"]
        detected_pattern = pat.get("pattern", "none")
        fraud_prob = float(pat.get("fraud_probability", 0.0))
        affected_txns = pat.get("affected_txn_ids", [flagged_txn_id])
        first_suspicious_txn = pat.get("first_suspicious_txn_id", flagged_txn_id)

        trace_steps.append({
            "step": 3,
            "phase": "PATTERN_REASONING",
            "action": "classify_typology",
            "observation": {
                "pattern": detected_pattern,
                "fraud_probability": fraud_prob,
                "affected_txns_count": len(affected_txns),
                "first_suspicious_txn": first_suspicious_txn,
                "evidence_claims": pat.get("evidence", [])
            }
        })

        # --- STEP 4: CASE MEMORY PRECEDENTS ---
        mem = dossier["case_memory"]["insights"]
        trace_steps.append({
            "step": 4,
            "phase": "CASE_MEMORY_RETRIEVAL",
            "action": "search_precedents",
            "observation": {
                "precedents_count": mem.get("num_precedents", 0),
                "consensus_outcome": mem.get("consensus_outcome", "uncertain"),
                "historical_fraud_rate": mem.get("fraud_rate", 0.0),
                "common_actions": mem.get("common_actions", []),
                "key_rationales": mem.get("key_rationales", [])
            }
        })

        # --- STEP 5: FRAUD POLICY EVALUATION (R1-R10) ---
        pol = dossier["policy_compliance"]
        approval_route = pol.get("approval_route", "L1_analyst")
        sar_required = pol.get("sar_required", False)
        exposure_usd = float(pol.get("exposure_usd", 0.0))
        recommended_actions = pol.get("recommended_actions", [])
        rule_ids = pol.get("rule_ids", [])

        trace_steps.append({
            "step": 5,
            "phase": "POLICY_EVALUATION",
            "action": "evaluate_rules",
            "observation": {
                "triggered_rule_ids": rule_ids,
                "approval_route": approval_route,
                "sar_required": sar_required,
                "exposure_usd": exposure_usd,
                "recommended_actions": recommended_actions
            }
        })

        # --- STEP 6: UNCERTAINTY ASSESSMENT & NEXT BEST ACTION ---
        # Determine whether conclusive or uncertain
        is_uncertain = False
        evidence_needed = None

        if trigger_type == "customer_report":
            # Direct inbound dispute from cardholder confirming unrecognized transaction
            verdict = "confirmed_fraud"
            confidence = max(fraud_prob, 0.92)
            nba = "BLOCK_CARD"
            is_uncertain = False
        elif detected_pattern == "undocumented" or detected_pattern == "card_testing":
            # Conclusive hard signal
            verdict = "confirmed_fraud"
            confidence = fraud_prob
            nba = "BLOCK_CARD"
        elif detected_pattern == "out_of_region_use":
            # Out of region requires cardholder travel confirmation under Rule R3
            is_uncertain = True
            evidence_needed = "VERIFY_WITH_CUSTOMER"
            verdict = "uncertain"
            confidence = fraud_prob
            nba = "VERIFY_WITH_CUSTOMER"
        elif detected_pattern == "card_not_present_new_device":
            is_uncertain = True
            evidence_needed = "STEP_UP_AUTH"
            verdict = "uncertain"
            confidence = fraud_prob
            nba = "STEP_UP_AUTH"
        elif detected_pattern == "card_not_present_fraud":
            verdict = "confirmed_fraud"
            confidence = fraud_prob
            nba = "BLOCK_CARD"
        else:
            verdict = "cleared"
            confidence = 0.90
            nba = "CLOSE_NO_FRAUD"

        trace_steps.append({
            "step": 6,
            "phase": "NEXT_BEST_ACTION",
            "action": "determine_nba",
            "observation": {
                "verdict": verdict,
                "confidence": confidence,
                "next_best_action": nba,
                "is_uncertain": is_uncertain,
                "additional_evidence_needed": evidence_needed
            }
        })

        # --- STEP 7: FINCEN SAR NARRATIVE GENERATION ---
        sar_narrative = ""
        if sar_required or exposure_usd >= 10000.0 or detected_pattern == "undocumented":
            sar_narrative = self.generate_sar_narrative(
                case_id=case_id,
                dossier=dossier,
                pattern=detected_pattern,
                exposure_usd=exposure_usd,
                affected_txns=affected_txns
            )

        trace_steps.append({
            "step": 7,
            "phase": "SAR_NARRATIVE_GENERATION",
            "action": "generate_sar",
            "observation": {
                "sar_filed": sar_required or bool(sar_narrative),
                "sar_narrative_length": len(sar_narrative)
            }
        })

        # --- STEP 8: FINAL CASE DOSSIER COMPILATION ---
        final_case_result = {
            "case_id": case_id,
            "opened_at": opened_at or dossier["timestamp"],
            "trigger_type": trigger_type,
            "flagged_txn_id": flagged_txn_id,
            "customer_id": dossier["customer_id"],
            "card_id": dossier["card_id"],
            "verdict": verdict,
            "confidence": confidence,
            "pattern": detected_pattern,
            "pattern_description": pat.get("pattern_description", ""),
            "affected_txn_ids": affected_txns,
            "first_suspicious_txn_id": first_suspicious_txn,
            "exposure_usd": exposure_usd,
            "approval_route": approval_route,
            "next_best_action": nba,
            "recommended_actions": recommended_actions,
            "triggered_rules": rule_ids,
            "sar_required": sar_required or bool(sar_narrative),
            "sar_narrative": sar_narrative,
            "evidence": pat.get("evidence", []),
            "trace_steps": trace_steps,
            "grounded_prompt_context": dossier["grounded_prompt_context"]
        }

        return final_case_result

    def generate_sar_narrative(
        self,
        case_id: str,
        dossier: Dict[str, Any],
        pattern: str,
        exposure_usd: float,
        affected_txns: List[str]
    ) -> str:
        """
        Generates a formal, FinCEN-compliant Suspicious Activity Report (SAR) narrative.
        Covers the 5 Ws (Who, What, When, Where, Why), Graph Topology, and Evidence Trails.
        """
        gc = dossier["graph_context"]
        t = gc["transaction"].get("transaction", {})
        dev = gc["device_sharing"]
        cust_id = dossier["customer_id"]
        card_id = dossier["card_id"]
        ts = dossier["timestamp"]
        dev_str = dev.get("canonical_profile_str", "Unknown Device")
        shared_cards = dev.get("number_of_distinct_cards", 0)
        connected_cases = dev.get("connected_historical_cases", [])

        narrative = (
            f"SUSPICIOUS ACTIVITY REPORT (SAR) NARRATIVE\n"
            f"Case Reference: {case_id}\n"
            f"Subject Customer: {cust_id} | Subject Card: {card_id}\n"
            f"Activity Period: {ts} | Cumulative Exposure: ${exposure_usd:.2f}\n"
            f"Primary Typology: {pattern.upper()}\n\n"
            f"1. EXECUTIVE SUMMARY:\n"
            f"Financial institution automated graph surveillance identified organized anomalous activity "
            f"involving customer {cust_id} and card {card_id}, resulting in cumulative suspicious exposure of ${exposure_usd:.2f} "
            f"across transaction(s) {', '.join(affected_txns)}.\n\n"
            f"2. GRAPH & DEVICE TOPOLOGY ANALYSIS:\n"
            f"Graph traversal revealed that transaction {t.get('transaction_id')} originated from device profile '{dev_str}' "
            f"(Device ID: {dev.get('device_id', 'N/A')}). Graph topological queries confirmed this exact device profile is "
            f"shared across {shared_cards} distinct cardholder accounts and is connected to {len(connected_cases)} previously "
            f"confirmed fraud case(s) ({', '.join(connected_cases[:4]) if connected_cases else 'N/A'}). Activity exhibited proxy masking characteristics (Proxy status: {t.get('id_23', 'N/A')}).\n\n"
            f"3. POLICY COMPLIANCE & ACTIONS TAKEN:\n"
            f"In accordance with Fraud Policy v1.0 (Rules R6, R8, R9), the institution initiated immediate defensive card blocks, "
            f"escalated the case to Senior Fraud Management (Level 2 Approval), and filed this formal FinCEN SAR.\n"
        )
        return narrative
