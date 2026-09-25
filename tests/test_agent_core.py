"""
Unit tests for Autonomous AI Agent Core (ReAct State Machine).
"""
import unittest
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.agent_core import FraudInvestigationAgent

class TestAgentCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = FraudInvestigationAgent()

    def test_run_investigation_hhg014_syndicate(self):
        """Verify full agent execution for HHG-014 (Device Syndicate)."""
        res = self.agent.run_investigation(
            case_id="HHG-014",
            trigger_type="risk_score",
            trigger_text="Real-time model scored transaction 3478561 ($74.96, online) at 0.05. Review and decide.",
            flagged_txn_id="3478561",
            card_id="C13487-K1",
            customer_id="C13487",
            opened_at="2016-11-22 16:11:00",
            initial_risk_score=0.05
        )
        self.assertEqual(res["case_id"], "HHG-014")
        self.assertEqual(res["pattern"], "undocumented")
        self.assertEqual(res["verdict"], "confirmed_fraud")
        self.assertEqual(res["approval_route"], "L2_senior_manager")
        self.assertEqual(res["next_best_action"], "BLOCK_CARD")
        self.assertTrue(res["sar_required"])
        self.assertGreater(len(res["sar_narrative"]), 100)
        self.assertIn("SM-G935F", res["sar_narrative"])
        
        # Verify 8 ReAct trace steps
        self.assertEqual(len(res["trace_steps"]), 7)
        phases = [s["phase"] for s in res["trace_steps"]]
        self.assertIn("ALERT_INGESTION", phases)
        self.assertIn("GRAPH_TRAVERSAL", phases)
        self.assertIn("PATTERN_REASONING", phases)
        self.assertIn("POLICY_EVALUATION", phases)
        self.assertIn("NEXT_BEST_ACTION", phases)
        self.assertIn("SAR_NARRATIVE_GENERATION", phases)

    def test_run_investigation_hhg001_uncertain_out_of_region(self):
        """Verify agent handles uncertain out-of-region case with step-up verification."""
        res = self.agent.run_investigation(
            case_id="HHG-001",
            trigger_type="risk_score",
            trigger_text="Real-time model scored transaction 3514030 ($77.07, in billing region 444.0) at 0.61. Review and decide.",
            flagged_txn_id="3514030",
            card_id="C12382-K1",
            customer_id="C12382",
            opened_at="2016-12-05 01:55:28",
            initial_risk_score=0.61
        )
        self.assertEqual(res["case_id"], "HHG-001")
        self.assertEqual(res["pattern"], "out_of_region_use")
        self.assertEqual(res["verdict"], "uncertain")
        self.assertEqual(res["next_best_action"], "VERIFY_WITH_CUSTOMER")
        self.assertIn("R2", res["triggered_rules"])
        self.assertIn("R3", res["triggered_rules"])

if __name__ == '__main__':
    unittest.main()
