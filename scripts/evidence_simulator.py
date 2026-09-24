"""
Interactive Evidence Gathering & Simulation Engine for Fraud Investigation.

Simulates customer contact, merchant inquiry, and device telemetry to resolve
uncertain investigation cases dynamically according to Fraud Policy v1.0 (Rules R3, R5, R10).
"""
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.agent_core import FraudInvestigationAgent
from scripts.policy_engine import FraudPolicyEngine

class EvidenceSimulator:
    """Simulates interactive evidence collection and recalculates case outcomes."""

    def __init__(self, data_dir: Optional[str] = None):
        self.agent = FraudInvestigationAgent(data_dir=data_dir)

    def request_evidence_options(self, case_dossier: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines the available interactive evidence options based on the case's detected pattern.
        """
        pattern = case_dossier.get("pattern", "none")
        options = []

        if pattern == "out_of_region_use":
            options.append({
                "action_type": "customer_contact",
                "channel": "SMS / Automated Call",
                "prompt": "Contact cardholder to verify out-of-region card-present activity in billing region",
                "simulated_outcomes": [
                    {
                        "outcome_code": "travel_confirmed",
                        "description": "Cardholder confirmed legitimate travel to the specified billing region.",
                        "resulting_verdict": "cleared",
                        "resulting_nba": "CLOSE_NO_FRAUD"
                    },
                    {
                        "outcome_code": "fraud_confirmed",
                        "description": "Cardholder confirmed they did NOT authorize this transaction and retained their card.",
                        "resulting_verdict": "confirmed_fraud",
                        "resulting_nba": "BLOCK_CARD"
                    }
                ]
            })

        elif pattern in ("card_not_present_new_device", "card_not_present_fraud"):
            options.append({
                "action_type": "step_up_auth",
                "channel": "Push Notification / In-App OTP",
                "prompt": "Send two-factor biometric/OTP push challenge for unrecognized device",
                "simulated_outcomes": [
                    {
                        "outcome_code": "auth_successful",
                        "description": "Cardholder successfully completed biometric step-up authentication on new device.",
                        "resulting_verdict": "cleared",
                        "resulting_nba": "CLOSE_NO_FRAUD"
                    },
                    {
                        "outcome_code": "auth_failed_or_denied",
                        "description": "Cardholder explicitly denied prompt or challenge timed out.",
                        "resulting_verdict": "confirmed_fraud",
                        "resulting_nba": "BLOCK_CARD"
                    }
                ]
            })

        # Generic merchant inquiry option available for all cases
        options.append({
            "action_type": "merchant_inquiry",
            "channel": "Merchant API / Order Verification",
            "prompt": "Inquire with merchant regarding fulfillment, shipping address, and delivery confirmation",
            "simulated_outcomes": [
                {
                    "outcome_code": "delivery_to_cardholder_address",
                    "description": "Merchant confirmed physical delivery to cardholder verified home address.",
                    "resulting_verdict": "cleared",
                    "resulting_nba": "CLOSE_NO_FRAUD"
                },
                {
                    "outcome_code": "instant_digital_goods_foreign_ip",
                    "description": "Instant high-risk digital code delivery to newly created unverified email.",
                    "resulting_verdict": "confirmed_fraud",
                    "resulting_nba": "BLOCK_CARD"
                }
            ]
        })

        return {
            "case_id": case_dossier.get("case_id"),
            "current_verdict": case_dossier.get("verdict"),
            "current_pattern": pattern,
            "evidence_options": options
        }

    def apply_simulated_evidence(
        self,
        case_dossier: Dict[str, Any],
        action_type: str,
        outcome_code: str,
        evidence_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Applies a simulated evidence outcome to an existing case dossier and recalculates final decision.
        """
        updated_dossier = dict(case_dossier)
        pattern = case_dossier.get("pattern", "none")
        exposure_usd = float(case_dossier.get("exposure_usd", 0.0))
        sar_required = case_dossier.get("sar_required", False)

        # Record simulation trace step
        sim_step = {
            "step": len(updated_dossier.get("trace_steps", [])) + 1,
            "phase": "INTERACTIVE_EVIDENCE_GATHERING",
            "action": action_type,
            "observation": {
                "outcome_code": outcome_code,
                "notes": evidence_notes or f"Simulated {action_type} returned '{outcome_code}'",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        updated_dossier.setdefault("trace_steps", []).append(sim_step)

        # Update verdicts and policy outcomes based on evidence
        if outcome_code in ("travel_confirmed", "auth_successful", "delivery_to_cardholder_address"):
            updated_dossier["verdict"] = "cleared"
            updated_dossier["confidence"] = 0.95
            updated_dossier["next_best_action"] = "CLOSE_NO_FRAUD"
            updated_dossier["recommended_actions"] = ["CLOSE_NO_FRAUD"]
            updated_dossier["is_uncertain"] = False
            updated_dossier["evidence_resolution"] = f"Evidence confirmed legitimate activity: {outcome_code}"

        elif outcome_code in ("fraud_confirmed", "auth_failed_or_denied", "instant_digital_goods_foreign_ip"):
            updated_dossier["verdict"] = "confirmed_fraud"
            updated_dossier["confidence"] = 0.98
            updated_dossier["next_best_action"] = "BLOCK_CARD"
            updated_dossier["recommended_actions"] = ["BLOCK_CARD", "REISSUE_CARD", "REIMBURSE_CUSTOMER"]
            if sar_required or exposure_usd >= 10000.0 or pattern == "undocumented":
                updated_dossier["recommended_actions"].append("FILE_SAR")
            updated_dossier["is_uncertain"] = False
            updated_dossier["evidence_resolution"] = f"Evidence confirmed unauthorized fraud: {outcome_code}"

        return updated_dossier
