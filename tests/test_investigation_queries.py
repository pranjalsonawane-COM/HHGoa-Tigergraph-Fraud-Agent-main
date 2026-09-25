"""
Comprehensive Test Suite for Phase 4 GSQL Investigation Queries.
Tests all 7 queries across multiple benchmark cases, historical cases, and edge cases.
"""
import unittest
import os
import sys
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.query_engine import GraphQueryEngine

class TestInvestigationQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = GraphQueryEngine()
        cls.gsql_path = os.path.join(ROOT_DIR, "tigergraph", "queries", "investigation_queries.gsql")
        with open(cls.gsql_path, mode='r', encoding='utf-8') as f:
            cls.gsql_content = f.read()

    def test_gsql_syntax_declarations(self):
        """Verify all 7 queries are defined in investigation_queries.gsql."""
        expected_queries = [
            "get_customer_profile",
            "get_card_window",
            "check_device_sharing",
            "check_region_discrepancy",
            "find_connected_prior_cases",
            "calculate_case_exposure",
            "get_transaction_context"
        ]
        for q in expected_queries:
            self.assertIn(f"CREATE OR REPLACE QUERY {q}", self.gsql_content, f"Query {q} missing in investigation_queries.gsql")

    def test_query1_get_customer_profile(self):
        """Test get_customer_profile for customer C13487 (HHG-014) and C12382 (HHG-001)."""
        res = self.engine.get_customer_profile("C13487")
        self.assertEqual(res["customer_id"], "C13487")
        self.assertEqual(res["number_of_cards"], 1)
        self.assertIn("C13487-K1", res["card_ids"])
        self.assertGreater(res["total_transaction_count"], 0)
        self.assertGreater(res["total_transaction_amount"], 0)
        self.assertIn("191.0", res["distinct_billing_regions"])

        # Test customer C12382 (HHG-001)
        res1 = self.engine.get_customer_profile("C12382")
        self.assertEqual(res1["customer_id"], "C12382")
        self.assertIn("C12382-K1", res1["card_ids"])
        self.assertGreater(res1["total_transaction_count"], 0)

    def test_query2_get_card_window(self):
        """Test get_card_window for card C13487-K1 around txn 3478561."""
        res = self.engine.get_card_window(
            card_id="C13487-K1",
            ref_transaction_id="3478561",
            window_hours=48
        )
        self.assertEqual(res["card_id"], "C13487-K1")
        self.assertGreater(res["transaction_count"], 0)
        self.assertIn("burst_window_seconds", res)
        self.assertIn("small_auth_count", res)

    def test_query3_check_device_sharing(self):
        """Test check_device_sharing for HHG-014's device DEV_13b0f4b32516."""
        # Txn 3478561 uses device DEV_13b0f4b32516
        res = self.engine.check_device_sharing(
            device_id="DEV_13b0f4b32516",
            ref_transaction_id="3478561",
            lookback_days=0
        )
        self.assertEqual(res["device_id"], "DEV_13b0f4b32516")
        self.assertGreater(res["number_of_distinct_cards"], 1, "Device should be shared across multiple cards")
        self.assertGreater(res["number_of_distinct_customers"], 1, "Device should be shared across multiple customers")
        # Check historical cases retrieved through shared device
        self.assertIn("CC-2649", res["connected_historical_cases"])

    def test_query4_check_region_discrepancy(self):
        """Test check_region_discrepancy for customer C08623 (HHG-003)."""
        res = self.engine.check_region_discrepancy(
            customer_id="C08623",
            ref_transaction_id="3530164"
        )
        self.assertEqual(res["customer_id"], "C08623")
        self.assertIn("dominant_region", res)
        self.assertIn("historical_regions", res)
        self.assertIn("region_changed", res)

    def test_query5_find_connected_prior_cases_with_anti_leakage(self):
        """Test find_connected_prior_cases with strict temporal anti-leakage boundary."""
        # HHG-014 occurred on 2016-11-22. Historical cases must be <= 2016-11-22
        res = self.engine.find_connected_prior_cases(
            customer_id="C13487",
            card_id="C13487-K1",
            device_id="DEV_13b0f4b32516",
            before_ts="2016-11-22 16:11:00"
        )
        self.assertGreater(res["total_prior_cases_found"], 0)
        for case in res["prior_cases"]:
            # Ensure no case closed AFTER the target investigation date is returned
            self.assertLessEqual(case["closed_at"], "2016-11-22 16:11:00", "Temporal leakage detected!")

    def test_query6_calculate_case_exposure(self):
        """Test calculate_case_exposure for a set of transactions."""
        txns = ["3478561", "3460634", "3462636"]
        res = self.engine.calculate_case_exposure(txns)
        self.assertEqual(res["transaction_count"], 3)
        self.assertEqual(res["total_exposure_usd"], round(74.96 + 112.37 + 30.88, 2))
        self.assertEqual(res["earliest_transaction"], "2016-11-15 20:30:00")
        self.assertEqual(res["latest_transaction"], "2016-11-22 16:11:00")

    def test_query7_get_transaction_context(self):
        """Test get_transaction_context for flagged txn 3478561."""
        res = self.engine.get_transaction_context("3478561")
        self.assertFalse(res.get("error", False))
        self.assertEqual(res["card_id"], "C13487-K1")
        self.assertEqual(res["customer_id"], "C13487")
        self.assertEqual(res["amount"], 74.96)
        self.assertEqual(res["device_id"], "DEV_13b0f4b32516")
        self.assertIn("previous_transactions", res)
        self.assertIn("next_transactions", res)

    def test_edge_cases(self):
        """Test edge cases: unknown customer, unknown card, unknown txn, customer with multiple cards."""
        # 1. Unknown customer
        p_unknown = self.engine.get_customer_profile("C999999")
        self.assertEqual(p_unknown["total_transaction_count"], 0)
        self.assertEqual(p_unknown["number_of_cards"], 0)

        # 2. Unknown card
        w_unknown = self.engine.get_card_window("C999999-K1")
        self.assertEqual(w_unknown["transaction_count"], 0)

        # 3. Unknown transaction
        t_unknown = self.engine.get_transaction_context("99999999")
        self.assertTrue(t_unknown.get("error", False))

        # 4. Customer with multiple cards (C04597)
        p_multi = self.engine.get_customer_profile("C04597")
        self.assertGreater(p_multi["number_of_cards"], 1)
        self.assertIn("C04597-K1", p_multi["card_ids"])
        self.assertIn("C04597-K2", p_multi["card_ids"])

        # 5. Empty exposure query
        exp_empty = self.engine.calculate_case_exposure([])
        self.assertEqual(exp_empty["transaction_count"], 0)
        self.assertEqual(exp_empty["total_exposure_usd"], 0.0)

if __name__ == '__main__':
    unittest.main()
