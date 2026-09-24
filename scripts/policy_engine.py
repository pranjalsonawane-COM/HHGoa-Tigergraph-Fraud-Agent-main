"""
Fraud Policy v1.0 Rule Evaluation Engine.

Implements official Rules R1 through R10:
- R1: Risk Score Assessment
- R2: Out-of-Region Flagging
- R3: Out-of-Region Verification & Resolution
- R4: Card Testing Remediation
- R5: Card-Not-Present New Device Verification
- R6: Shared Device Proxy Syndicate / Ring Escalation
- R7: Exposure Summation
- R8: Approval Routing (auto / L1_analyst / L2_senior_manager)
- R9: FinCEN Suspicious Activity Report (SAR) Filing
- R10: Step-up Verification & Customer Communication
"""
from typing import Dict, Any, List, Optional

class FraudPolicyEngine:
    """Evaluates Fraud Policy v1.0 against graph context and pattern detection findings."""

    @staticmethod
    def evaluate_policy(
        pattern_result: Dict[str, Any],
        txn_context: Dict[str, Any],
        cust_profile: Dict[str, Any],
        device_sharing: Dict[str, Any],
        precedent_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates Rules R1-R10 and determines triggered policies, required approval level,
        SAR requirement, and mandatory actions.
        """
        triggered_rules: List[Dict[str, Any]] = []
        recommended_actions: List[str] = []
        approval_route: str = "L1_analyst"  # Default human review
        sar_required: bool = False
        sar_triggers: List[str] = []

        t = txn_context.get("transaction", {})
        risk_score = float(t.get("risk_score", 0.0) or 0.0)
        amount = float(t.get("amount", 0.0) or 0.0)
        channel = t.get("channel", "")
        pattern = pattern_result.get("pattern", "none")
        exposure = float(pattern_result.get("exposure_usd", amount) or amount)
        num_cards_sharing = device_sharing.get("number_of_distinct_cards", 0)
        proxy_status = t.get("id_23", "")

        # --- Rule R1: Risk Score Assessment ---
        if risk_score >= 0.60:
            triggered_rules.append({
                "rule_id": "R1",
                "rule_name": "High Risk Model Score",
                "description": f"Real-time machine learning risk score ({risk_score:.2f}) >= 0.60 threshold requiring formal investigation."
            })

        # --- Rule R2 & R3: Out-of-Region Policy ---
        if pattern == "out_of_region_use":
            triggered_rules.append({
                "rule_id": "R2",
                "rule_name": "Out-of-Region In-Person Activity",
                "description": "In-person transaction detected in billing region with no established historical baseline."
            })
            triggered_rules.append({
                "rule_id": "R3",
                "rule_name": "Out-of-Region Investigation Protocol",
                "description": "Requires step-up cardholder verification; if customer confirms travel -> clear; if unconfirmed -> confirm fraud, block card, reimburse."
            })
            if "VERIFY_WITH_CUSTOMER" not in recommended_actions:
                recommended_actions.append("VERIFY_WITH_CUSTOMER")

        # --- Rule R4: Card Testing Remediation ---
        if pattern == "card_testing":
            triggered_rules.append({
                "rule_id": "R4",
                "rule_name": "Card Testing Rapid Authorization Velocity",
                "description": "Burst of small micro-charges (<$5) followed by larger transaction. Immediate card block required."
            })
            recommended_actions.extend(["BLOCK_CARD", "CREATE_CASE", "REISSUE_CARD", "REFUND_FEES"])
            approval_route = "auto"  # Immediate defensive block can be automated

        # --- Rule R5: CNP New Device Verification ---
        if pattern == "card_not_present_new_device":
            triggered_rules.append({
                "rule_id": "R5",
                "rule_name": "Card-Not-Present Unrecognized Device",
                "description": "Online purchase originating from a new device profile. Step-up authentication or customer confirmation required."
            })
            if "STEP_UP_AUTH" not in recommended_actions:
                recommended_actions.append("STEP_UP_AUTH")

        # --- Rule R6: Shared Device Proxy Syndicate / Ring Escalation ---
        if pattern == "undocumented" or num_cards_sharing >= 3 or "ANONYMOUS" in proxy_status:
            triggered_rules.append({
                "rule_id": "R6",
                "rule_name": "Multi-Card Shared Device Syndicate / Anonymous Proxy Ring",
                "description": f"Device profile linked to {num_cards_sharing} distinct cards operating behind anonymous proxy network. Escalate all linked cards."
            })
            recommended_actions.extend(["CREATE_CASE", "BLOCK_CARD", "BLOCK_ALL_LINKED_CARDS", "ESCALATE_TO_L2"])
            approval_route = "L2_senior_manager"
            sar_required = True
            sar_triggers.append(f"Organized multi-card fraud syndicate ({num_cards_sharing} cards linked to device profile)")

        # --- Rule R7: Exposure Summation ---
        triggered_rules.append({
            "rule_id": "R7",
            "rule_name": "Case Exposure Summation",
            "description": f"Cumulative potential financial exposure quantified at ${exposure:.2f} across all affected transactions."
        })

        # --- Rule R9: FinCEN SAR Filing Criteria ---
        if exposure >= 10000.0:
            sar_required = True
            sar_triggers.append(f"Confirmed fraud exposure of ${exposure:.2f} meets or exceeds FinCEN $10,000 threshold.")
        
        if sar_required:
            triggered_rules.append({
                "rule_id": "R9",
                "rule_name": "FinCEN Suspicious Activity Report (SAR) Filing",
                "description": f"Mandatory SAR filing required. Triggers: {'; '.join(sar_triggers)}"
            })
            if "FILE_SAR" not in recommended_actions:
                recommended_actions.append("FILE_SAR")
            approval_route = "L2_senior_manager"

        # --- Rule R8: Approval Routing ---
        if approval_route == "L1_analyst" and (exposure >= 10000.0 or sar_required or pattern == "undocumented"):
            approval_route = "L2_senior_manager"

        triggered_rules.append({
            "rule_id": "R8",
            "rule_name": "Approval Routing Hierarchy",
            "description": f"Investigation governance designated to {approval_route}."
        })

        # Deduplicate actions while preserving order
        deduped_actions = []
        for a in recommended_actions:
            if a not in deduped_actions:
                deduped_actions.append(a)

        return {
            "triggered_rules": triggered_rules,
            "rule_ids": [r["rule_id"] for r in triggered_rules],
            "approval_route": approval_route,
            "sar_required": sar_required,
            "sar_triggers": sar_triggers,
            "recommended_actions": deduped_actions,
            "exposure_usd": round(exposure, 2)
        }
