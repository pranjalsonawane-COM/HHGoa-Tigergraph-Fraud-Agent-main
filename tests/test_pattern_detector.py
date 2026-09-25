"""
Unit tests for Fraud Pattern Detection Engine.
"""
import unittest
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.query_engine import GraphQueryEngine
from scripts.pattern_detector import FraudPatternDetector

class TestPatternDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = GraphQueryEngine()

    def test_detect_undocumented_syndicate_hhg014(self):
        """HHG-014: Stolen cards on shared device SM-G935F behind anonymous proxy."""
        txn_ctx = self.engine.get_transaction_context("3478561")
        cust_prof = self.engine.get_customer_profile("C13487")
        card_win = self.engine.get_card_window("C13487-K1", "3478561", 24)
        dev_sharing = self.engine.check_device_sharing("DEV_13b0f4b32516", "3478561", "C13487-K1", 0)
        reg_disc = self.engine.check_region_discrepancy("C13487", "3478561")
        prior_cases = self.engine.find_connected_prior_cases("C13487", "C13487-K1", "DEV_13b0f4b32516", "2016-11-22 16:11:00")

        res = FraudPatternDetector.detect_fraud_pattern(
            txn_ctx, cust_prof, card_win, dev_sharing, reg_disc, prior_cases
        )
        self.assertEqual(res["pattern"], "undocumented")
        self.assertGreater(len(res["pattern_description"]), 10)
        self.assertGreaterEqual(res["fraud_probability"], 0.80)
        self.assertIn("3478561", res["affected_txn_ids"])

    def test_detect_out_of_region_hhg001(self):
        """HHG-001: In-person charge in region 444.0 away from baseline."""
        txn_ctx = self.engine.get_transaction_context("3514030")
        cust_prof = self.engine.get_customer_profile("C12382")
        card_win = self.engine.get_card_window("C12382-K1", "3514030", 24)
        dev_sharing = self.engine.check_device_sharing("", "3514030", "C12382-K1", 0)
        reg_disc = self.engine.check_region_discrepancy("C12382", "3514030")
        prior_cases = self.engine.find_connected_prior_cases("C12382", "C12382-K1", "", "2016-12-05 01:55:28")

        res = FraudPatternDetector.detect_fraud_pattern(
            txn_ctx, cust_prof, card_win, dev_sharing, reg_disc, prior_cases
        )
        self.assertEqual(res["pattern"], "out_of_region_use")
        self.assertGreaterEqual(res["fraud_probability"], 0.70)
        self.assertIn("3514030", res["affected_txn_ids"])

    def test_detect_cnp_new_device_hhg005(self):
        """HHG-005: Online transaction from new iOS device."""
        txn_ctx = self.engine.get_transaction_context("3523199")
        cust_prof = self.engine.get_customer_profile("C02923")
        card_win = self.engine.get_card_window("C02923-K1", "3523199", 24)
        dev_sharing = self.engine.check_device_sharing("DEV_c527e02b36b5", "3523199", "C02923-K1", 0)
        reg_disc = self.engine.check_region_discrepancy("C02923", "3523199")
        prior_cases = self.engine.find_connected_prior_cases("C02923", "C02923-K1", "DEV_c527e02b36b5", "2016-12-08 03:38:37")

        res = FraudPatternDetector.detect_fraud_pattern(
            txn_ctx, cust_prof, card_win, dev_sharing, reg_disc, prior_cases
        )
        self.assertEqual(res["pattern"], "card_not_present_new_device")
        self.assertIn("3523199", res["affected_txn_ids"])

    def test_detect_card_testing_synthetic(self):
        """Synthetic card testing pattern: 3 sub-$5 txns followed by large purchase."""
        card_win = {
            "small_auth_count": 3,
            "small_auth_window_seconds": 1200,
            "transactions": [
                {"transaction_id": "T1", "amount": 1.50, "channel": "online", "ts": "2016-11-10 10:00:00"},
                {"transaction_id": "T2", "amount": 2.20, "channel": "online", "ts": "2016-11-10 10:15:00"},
                {"transaction_id": "T3", "amount": 0.99, "channel": "online", "ts": "2016-11-10 10:25:00"},
                {"transaction_id": "T4", "amount": 250.00, "channel": "online", "ts": "2016-11-10 10:45:00"}
            ]
        }
        txn_ctx = {"transaction": {"transaction_id": "T4", "amount": 250.00, "channel": "online"}}
        is_p, prob, ev, aff, first = FraudPatternDetector.evaluate_card_testing(card_win, txn_ctx)
        self.assertTrue(is_p)
        self.assertEqual(prob, 0.85)
        self.assertEqual(first, "T1")
        self.assertEqual(len(aff), 4)

if __name__ == '__main__':
    unittest.main()
