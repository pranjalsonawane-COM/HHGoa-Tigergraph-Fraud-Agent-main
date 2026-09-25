"""
Unit tests for Next Best Action (NBA) Decision Engine.
"""
import unittest
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.agent_core import FraudInvestigationAgent
from scripts.nba_engine import NextBestActionEngine

class TestNBAEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = FraudInvestigationAgent()
        cls.nba = NextBestActionEngine()

    def test_nba_playbook_hhg014_syndicate(self):
        """Verify NBA playbook generation for HHG-014 (Device Syndicate)."""
        dossier = self.agent.run_investigation(
            case_id="HHG-014",
            trigger_type="risk_score",
            trigger_text="Real-time model scored transaction 3478561 ($74.96, online) at 0.05. Review and decide.",
            flagged_txn_id="3478561",
            card_id="C13487-K1",
            customer_id="C13487",
            opened_at="2016-11-22 16:11:00",
            initial_risk_score=0.05
        )
        playbook = self.nba.generate_nba_playbook(dossier)
        self.assertEqual(playbook["case_id"], "HHG-014")
        self.assertEqual(playbook["primary_action"], "BLOCK_ALL_LINKED_CARDS_AND_FILE_SAR")
        self.assertEqual(playbook["approval_route"], "L2_senior_manager")
        self.assertGreaterEqual(len(playbook["containment_steps"]), 3)
        self.assertGreaterEqual(len(playbook["compliance_actions"]), 2)
        
        # Verify SAR compliance action
        sar_action = next((a for a in playbook["compliance_actions"] if "SAR" in a), None)
        self.assertIsNotNone(sar_action)

    def test_nba_playbook_hhg001_uncertain_out_of_region(self):
        """Verify NBA playbook for uncertain out-of-region case HHG-001."""
        dossier = self.agent.run_investigation(
            case_id="HHG-001",
            trigger_type="risk_score",
            trigger_text="Real-time model scored transaction 3514030 ($77.07, in billing region 444.0) at 0.61. Review and decide.",
            flagged_txn_id="3514030",
            card_id="C12382-K1",
            customer_id="C12382",
            opened_at="2016-12-05 01:55:28",
            initial_risk_score=0.61
        )
        playbook = self.nba.generate_nba_playbook(dossier)
        self.assertEqual(playbook["case_id"], "HHG-001")
        self.assertEqual(playbook["primary_action"], "VERIFY_WITH_CUSTOMER")
        self.assertIn("billing region", playbook["customer_communication"]["message_copy"])

    def test_nba_playbook_cleared_case(self):
        """Verify NBA playbook for cleared case."""
        cleared_dossier = {
            "case_id": "HHG-TEST-CLEARED",
            "verdict": "cleared",
            "pattern": "none",
            "approval_route": "auto",
            "exposure_usd": 0.0,
            "card_id": "C00001-K1",
            "customer_id": "C00001",
            "flagged_txn_id": "3000001",
            "triggered_rules": []
        }
        playbook = self.nba.generate_nba_playbook(cleared_dossier)
        self.assertEqual(playbook["primary_action"], "CLOSE_NO_FRAUD")
        self.assertEqual(playbook["approval_route"], "auto")

if __name__ == '__main__':
    unittest.main()
