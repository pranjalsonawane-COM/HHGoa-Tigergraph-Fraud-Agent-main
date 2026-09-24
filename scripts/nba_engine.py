"""
Next Best Action (NBA) Decision Engine & Operational Playbooks for Fraud Investigation.

Synthesizes graph evidence, detected typologies, case memory, and Fraud Policy v1.0 rules
into actionable containment, remediation, and compliance playbooks.
"""
import os
import sys
from typing import Dict, Any, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

class NextBestActionEngine:
    """Generates structured operational playbooks and Next Best Actions for fraud cases."""

    @staticmethod
    def generate_nba_playbook(case_dossier: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a comprehensive Next Best Action playbook including containment,
        customer communication, financial remediation, and regulatory compliance.
        """
        pattern = case_dossier.get("pattern", "none")
        verdict = case_dossier.get("verdict", "uncertain")
        approval_route = case_dossier.get("approval_route", "L1_analyst")
        sar_required = case_dossier.get("sar_required", False)
        exposure_usd = float(case_dossier.get("exposure_usd", 0.0))
        cust_id = case_dossier.get("customer_id", "")
        card_id = case_dossier.get("card_id", "")
        flagged_tid = case_dossier.get("flagged_txn_id", "")

        containment_steps: List[str] = []
        customer_comm_copy: str = ""
        financial_remediation: List[str] = []
        compliance_actions: List[str] = []
        sla_hours: int = 4

        # 1. Deterministic Playbook Branching by Verdict & Typology
        if verdict == "confirmed_fraud":
            if pattern == "undocumented":
                # Organized Syndicate / Proxy Ring
                primary_action = "BLOCK_ALL_LINKED_CARDS_AND_FILE_SAR"
                sla_hours = 24  # Complex L2 compliance review
                containment_steps = [
                    f"Immediate hard block on primary compromised card {card_id}",
                    "Identify and freeze all companion cards sharing device profile across graph",
                    "Add device hardware fingerprint and proxy IP ranges to real-time blacklists",
                    "Revoke active web/mobile banking sessions for affected accounts"
                ]
                customer_comm_copy = (
                    f"Dear Cardholder, we detected unauthorized activity on your card ending in {card_id[-4:] if len(card_id)>=4 else card_id}. "
                    "For your security, we have placed a hold on the card. A fraud specialist will contact you to reissue a new card."
                )
                financial_remediation = [
                    f"Process unauthorized transaction chargebacks totaling ${exposure_usd:.2f}",
                    "Issue provisional credit to affected cardholder(s)",
                    "Waive all associated late fees or overdraft charges"
                ]
                compliance_actions = [
                    "File FinCEN Suspicious Activity Report (SAR) under Rule R9 (Organized Proxy Syndicate)",
                    "Escalate case dossier to Senior Fraud Operations & Legal Compliance (Level 2 Approval)",
                    "Write finalized investigation dossier and syndicate links back to TigerGraph"
                ]

            elif pattern == "card_testing":
                primary_action = "BLOCK_CARD"
                sla_hours = 1
                approval_route = "auto"
                containment_steps = [
                    f"Immediate automated hard block on card {card_id}",
                    "Block repeated merchant authorization terminal IDs",
                    "Trigger automated card replacement workflow"
                ]
                customer_comm_copy = (
                    f"Alert: Suspicious rapid authorization attempts were detected on your card {card_id}. "
                    "Your card has been blocked to prevent loss. A replacement card has been ordered."
                )
                financial_remediation = [
                    f"Reverse micro-authorization charges and fraudulent transactions (${exposure_usd:.2f})",
                    "Waive foreign transaction and authorization fees"
                ]
                compliance_actions = [
                    "Log automated containment event to audit ledger",
                    "Record confirmed fraud card testing signature in TigerGraph"
                ]

            else:
                # Standard CNP Fraud / Confirmed Unauthorized
                primary_action = "BLOCK_CARD"
                sla_hours = 4
                containment_steps = [
                    f"Hard block compromised card {card_id}",
                    "De-authenticate suspicious online browser sessions",
                    "Order expedited replacement card"
                ]
                customer_comm_copy = (
                    f"Dear Customer, we confirmed unauthorized charges of ${exposure_usd:.2f} on your card. "
                    "We have blocked the card and initiated a full refund."
                )
                financial_remediation = [
                    f"Initiate card network chargebacks totaling ${exposure_usd:.2f}",
                    "Credit customer account in full",
                    "Reissue new card credentials"
                ]
                compliance_actions = [
                    "File FinCEN SAR if cumulative threshold >= $10,000" if sar_required else "Record internal fraud resolution in audit log",
                    "Update cardholder risk profile in TigerGraph"
                ]

        elif verdict == "uncertain":
            if pattern == "out_of_region_use":
                primary_action = "VERIFY_WITH_CUSTOMER"
                sla_hours = 2
                containment_steps = [
                    f"Place temporary security authorization hold on transaction {flagged_tid}",
                    "Dispatch automated SMS two-way travel verification prompt"
                ]
                customer_comm_copy = (
                    f"Did you attempt a purchase of ${exposure_usd:.2f} in billing region {case_dossier.get('graph_context', {}).get('region_discrepancy', {}).get('current_region', 'unknown')}? "
                    "Reply YES if this was you, or NO if you did not make this purchase."
                )
                financial_remediation = [
                    "Hold settlement pending cardholder response"
                ]
                compliance_actions = [
                    "Track verification response within 2-hour SLA window",
                    "Escalate to fraud block if customer denies or times out"
                ]

            elif pattern == "card_not_present_new_device":
                primary_action = "STEP_UP_AUTH"
                sla_hours = 1
                containment_steps = [
                    "Prompt in-app biometric or push OTP challenge for new device login",
                    "Restrict high-limit transfers until step-up auth completed"
                ]
                customer_comm_copy = (
                    "New device login detected. Please approve the push notification on your primary mobile device to authorize this transaction."
                )
                financial_remediation = [
                    "Release transaction hold upon biometric verification"
                ]
                compliance_actions = [
                    "Register device fingerprint in customer trusted profile upon successful authentication"
                ]

            else:
                primary_action = "MANUAL_ANALYST_REVIEW"
                sla_hours = 4
                containment_steps = ["Flag transaction for Level 1 analyst review queue"]
                customer_comm_copy = "Standard transaction review in progress."
                financial_remediation = ["None pending review"]
                compliance_actions = ["Log analyst triage review"]

        else:
            # Cleared / No Fraud
            primary_action = "CLOSE_NO_FRAUD"
            sla_hours = 1
            approval_route = "auto"
            containment_steps = [
                "Release all security holds on account and card",
                "Ensure uninterrupted cardholder purchasing capability"
            ]
            customer_comm_copy = (
                "Thank you for confirming your transaction. Your account is fully active and secure."
            )
            financial_remediation = [
                "Allow standard merchant settlement"
            ]
            compliance_actions = [
                "Close alert as legitimate cardholder activity",
                "Update customer behavioral baseline in TigerGraph"
            ]

        # 2. Compile Playbook Payload
        playbook = {
            "case_id": case_dossier.get("case_id"),
            "verdict": verdict,
            "pattern": pattern,
            "primary_action": primary_action,
            "approval_route": approval_route,
            "sla_hours": sla_hours,
            "containment_steps": containment_steps,
            "customer_communication": {
                "channel": "SMS / In-App Push" if verdict != "cleared" else "Email",
                "message_copy": customer_comm_copy
            },
            "financial_remediation": financial_remediation,
            "compliance_actions": compliance_actions,
            "sign_off_checklist": [
                f"Confirm policy rule alignment ({', '.join(case_dossier.get('triggered_rules', []))})",
                f"Verify financial exposure calculation (${exposure_usd:.2f})",
                "Validate customer notification dispatch",
                "Confirm TigerGraph graph resolution payload"
            ]
        }

        return playbook
