"""
Unit test for FraudGraph Data Loading, Edge Counts, and Graph Traversal.
"""
import unittest
import os
import json
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.graph_validator import run_graph_validation

class TestGraphTraversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.val_res = run_graph_validation()

    def test_vertex_counts(self):
        vc = self.val_res["vertex_counts"]
        self.assertEqual(vc["Customer"], 13553)
        self.assertEqual(vc["Card"], 14850)
        self.assertEqual(vc["Transaction"], 590742)
        self.assertEqual(vc["DeviceProfile"], 9708)
        self.assertEqual(vc["BillingRegion"], 332)
        self.assertEqual(vc["EmailDomain"], 60)
        self.assertEqual(vc["ClosedCase"], 5565)

    def test_primary_edge_counts(self):
        ec = self.val_res["edge_counts"]
        self.assertEqual(ec["OWNS"], 14850)
        self.assertEqual(ec["MADE"], 590742)
        self.assertEqual(ec["FROM_DEVICE"], 144432)
        self.assertEqual(ec["BILLED_IN"], 525003)
        self.assertEqual(ec["PURCHASER_EMAIL"], 496262)
        self.assertEqual(ec["RECIPIENT_EMAIL"], 137453)
        self.assertEqual(ec["NEXT"], 575892)
        self.assertEqual(ec["INVOLVES"], 14955)
        self.assertEqual(ec["ON_CARD"], 5565)
        self.assertEqual(ec["CONNECTED_TO"], 92)

    def test_integrity_zero_errors(self):
        self.assertEqual(self.val_res["integrity_errors"], 0)

    def test_hhg014_traversal_evidence(self):
        t = self.val_res["hhg014_traversal"]
        self.assertEqual(t["case_id"], "HHG-014")
        self.assertEqual(t["flagged_transaction"]["transaction_id"], "3478561")
        self.assertEqual(t["owning_card"]["card_id"], "C13487-K1")
        self.assertEqual(t["owning_customer"]["customer_id"], "C13487")
        self.assertEqual(t["device_profile"]["device_info"], "SM-G935F Build/NRD90M")
        
        # Check cross-card device connections
        sharing = t["cross_card_device_sharing"]
        self.assertGreater(len(sharing["connected_cards"]), 0)
        self.assertIn("CC-2649", [c["case_id"] for c in sharing["connected_historical_cases"]])

if __name__ == '__main__':
    unittest.main()
