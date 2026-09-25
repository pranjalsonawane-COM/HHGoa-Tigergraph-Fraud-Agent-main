"""
Unit tests for Interactive Evidence Gathering & Simulation Engine.
"""
import unittest
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.agent_core import FraudInvestigationAgent
from scripts.evidence_simulator import EvidenceSimulator

class TestEvidenceSimulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = FraudInvestigationAgent()
        cls.simulator = EvidenceSimulator()

    def test_request_evidence_options_hhg001(self):
        """Verify evidence options generation for uncertain out-of-region case HHG-001."""
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
        self.assertEqual(dossier["verdict"], "uncertain")
        
        options_payload = self.simulator.request_evidence_options(dossier)
        self.assertEqual(options_payload["case_id"], "HHG-001")
        opts = options_payload["evidence_options"]
        self.assertGreaterEqual(len(opts), 2)
        
        # Verify customer_contact option
        cust_opt = next((o for o in opts if o["action_type"] == "customer_contact"), None)
        self.assertIsNotNone(cust_opt)
        self.assertIn("billing region", cust_opt["prompt"])

    def test_apply_travel_confirmed_evidence(self):
        """Verify applying travel confirmed evidence resolves HHG-001 to cleared."""
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
        
        resolved = self.simulator.apply_simulated_evidence(
            case_dossier=dossier,
            action_type="customer_contact",
            outcome_code="travel_confirmed",
            evidence_notes="Cardholder confirmed business trip to region 444.0."
        )
        self.assertEqual(resolved["verdict"], "cleared")
        self.assertEqual(resolved["next_best_action"], "CLOSE_NO_FRAUD")
        self.assertGreaterEqual(resolved["confidence"], 0.90)
        
        # Check trace step addition
        phases = [s["phase"] for s in resolved["trace_steps"]]
        self.assertIn("INTERACTIVE_EVIDENCE_GATHERING", phases)

    def test_apply_fraud_confirmed_evidence(self):
        """Verify applying fraud confirmed evidence resolves HHG-001 to confirmed_fraud."""
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
        
        resolved = self.simulator.apply_simulated_evidence(
            case_dossier=dossier,
            action_type="customer_contact",
            outcome_code="fraud_confirmed",
            evidence_notes="Cardholder did not travel to region 444.0; card data compromised."
        )
        self.assertEqual(resolved["verdict"], "confirmed_fraud")
        self.assertEqual(resolved["next_best_action"], "BLOCK_CARD")
        self.assertIn("BLOCK_CARD", resolved["recommended_actions"])

if __name__ == '__main__':
    unittest.main()
