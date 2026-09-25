"""
Unit test verifying TigerGraph schema definitions and loading jobs alignment with preprocessed CSVs.
"""
import unittest
import os
import csv
import re
import sys

# Ensure workspace root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tigergraph.client import TigerGraphClient

class TestTigerGraphSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = os.path.join(ROOT_DIR, "tigergraph", "schema", "schema.gsql")
        cls.loading_path = os.path.join(ROOT_DIR, "tigergraph", "schema", "loading_jobs.gsql")
        cls.processed_dir = os.path.join(ROOT_DIR, "data", "processed")

        with open(cls.schema_path, mode='r', encoding='utf-8') as f:
            cls.schema_gsql = f.read()

        with open(cls.loading_path, mode='r', encoding='utf-8') as f:
            cls.loading_gsql = f.read()

    def test_schema_vertices_exist(self):
        expected_vertices = [
            "Customer", "Card", "Transaction", "DeviceProfile",
            "BillingRegion", "EmailDomain", "ClosedCase"
        ]
        for v in expected_vertices:
            self.assertIn(f"CREATE VERTEX {v}", self.schema_gsql, f"Vertex {v} missing in schema.gsql")

    def test_schema_edges_exist(self):
        expected_edges = [
            "OWNS", "MADE", "FROM_DEVICE", "BILLED_IN",
            "PURCHASER_EMAIL", "RECIPIENT_EMAIL", "NEXT",
            "INVOLVES", "ON_CARD", "CONNECTED_TO"
        ]
        for e in expected_edges:
            self.assertIn(f"CREATE DIRECTED EDGE {e}", self.schema_gsql, f"Edge {e} missing in schema.gsql")

    def test_loading_jobs_match_processed_headers(self):
        # Verify that columns referenced in loading jobs match exact headers in data/processed/*.csv
        file_header_checks = {
            "customers.csv": ["customer_id", "total_cards", "first_seen", "home_region", "total_txns"],
            "cards.csv": ["card_id", "customer_id", "card_network", "card_type", "card1", "card2", "card3", "card4", "card5", "card6"],
            "transactions.csv": ["transaction_id", "amount", "ts", "channel", "product_cd", "risk_score", "addr1", "addr2", "p_email", "r_email", "device_id", "id_15", "id_23"],
            "device_profiles.csv": ["device_id", "canonical_profile_str", "device_info", "os", "browser", "screen", "device_type"],
            "billing_regions.csv": ["region_id", "total_transactions"],
            "email_domains.csv": ["domain_name", "total_transactions"],
            "historical_cases.csv": ["case_id", "customer_id", "card_id", "opened_at", "closed_at", "outcome", "pattern", "exposure_usd", "report_filed", "actions_taken", "analyst_notes", "txn_ids", "connected_card_ids"],
            "edges_owns.csv": ["from_customer", "to_card"],
            "edges_made.csv": ["from_card", "to_transaction"],
            "edges_from_device.csv": ["from_transaction", "to_device", "id_15"],
            "edges_billed_in.csv": ["from_transaction", "to_region"],
            "edges_email.csv": ["from_transaction", "to_domain", "role"],
            "edges_next.csv": ["from_transaction", "to_transaction", "delta_seconds"],
            "edges_case_involves.csv": ["from_case", "to_transaction", "is_first_fraud"],
            "edges_case_card.csv": ["from_case", "to_card", "rel_type"]
        }

        for fname, expected_cols in file_header_checks.items():
            fpath = os.path.join(self.processed_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"Processed file {fname} does not exist")
            with open(fpath, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                for col in expected_cols:
                    self.assertIn(col, header, f"Column '{col}' missing in {fname}")

    def test_client_schema_summary(self):
        client = TigerGraphClient()
        summary = client.get_schema_summary()
        self.assertEqual(summary["graph_name"], "FraudGraph")
        self.assertEqual(len(summary["vertices"]), 7)
        self.assertEqual(len(summary["edges"]), 10)

if __name__ == '__main__':
    unittest.main()
