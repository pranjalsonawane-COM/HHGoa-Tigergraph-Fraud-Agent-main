"""
Unit tests for GraphRAG Multi-Hop & Policy Engine.
"""
import unittest
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.graph_rag import GraphRAGEngine
from scripts.policy_engine import FraudPolicyEngine

class TestGraphRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = GraphRAGEngine()

    def test_investigate_hhg014_syndicate(self):
        """Verify full GraphRAG dossier for HHG-014 (Device Syndicate)."""
        dossier = self.engine.investigate_alert(
            transaction_id="3478561",
            customer_id="C13487",
            card_id="C13487-K1",
            alert_timestamp="2016-11-22 16:11:00"
        )
        self.assertEqual(dossier["transaction_id"], "3478561")
        self.assertEqual(dossier["summary"]["detected_pattern"], "undocumented")
        self.assertTrue(dossier["summary"]["sar_required"])
        self.assertEqual(dossier["summary"]["approval_route"], "L2_senior_manager")
        
        # Check rule citations
        rule_ids = dossier["policy_compliance"]["rule_ids"]
        self.assertIn("R6", rule_ids)
        self.assertIn("R8", rule_ids)
        self.assertIn("R9", rule_ids)

        # Check prompt context
        prompt_txt = dossier["grounded_prompt_context"]
        self.assertIn("# GRAPHRAG INVESTIGATION DOSSIER: Transaction 3478561", prompt_txt)
        self.assertIn("SM-G935F", prompt_txt)
        self.assertIn("L2_senior_manager", prompt_txt)

    def test_investigate_hhg001_out_of_region(self):
        """Verify full GraphRAG dossier for HHG-001 (Out of region)."""
        dossier = self.engine.investigate_alert(
            transaction_id="3514030",
            customer_id="C12382",
            card_id="C12382-K1",
            alert_timestamp="2016-12-05 01:55:28"
        )
        self.assertEqual(dossier["summary"]["detected_pattern"], "out_of_region_use")
        rule_ids = dossier["policy_compliance"]["rule_ids"]
        self.assertIn("R1", rule_ids)
        self.assertIn("R2", rule_ids)
        self.assertIn("R3", rule_ids)
        self.assertIn("VERIFY_WITH_CUSTOMER", dossier["summary"]["recommended_actions"])

    def test_policy_card_testing_rules(self):
        """Verify Policy Engine rules for card testing."""
        pat = {"pattern": "card_testing", "exposure_usd": 250.0}
        txn = {"transaction": {"amount": 250.0, "risk_score": 0.85, "channel": "online"}}
        pol = FraudPolicyEngine.evaluate_policy(pat, txn, {}, {}, {})
        
        self.assertIn("R4", pol["rule_ids"])
        self.assertEqual(pol["approval_route"], "auto")
        self.assertIn("BLOCK_CARD", pol["recommended_actions"])
        self.assertFalse(pol["sar_required"])

    def test_policy_high_exposure_sar_trigger(self):
        """Verify Rule R9 mandatory SAR filing for exposure >= $10,000."""
        pat = {"pattern": "card_not_present_fraud", "exposure_usd": 14500.0}
        txn = {"transaction": {"amount": 14500.0, "risk_score": 0.92, "channel": "online"}}
        pol = FraudPolicyEngine.evaluate_policy(pat, txn, {}, {}, {})
        
        self.assertIn("R9", pol["rule_ids"])
        self.assertTrue(pol["sar_required"])
        self.assertEqual(pol["approval_route"], "L2_senior_manager")
        self.assertIn("FILE_SAR", pol["recommended_actions"])

if __name__ == '__main__':
    unittest.main()
