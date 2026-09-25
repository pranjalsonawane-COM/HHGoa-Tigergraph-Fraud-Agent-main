"""
Unit tests for Case Management and Benchmark Answer Validation.
"""
import unittest
import os
import sys
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.case_manager import CaseManager

class TestCaseManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = CaseManager()
        cls.answers_dir = os.path.abspath(os.path.join(ROOT_DIR, 'answers'))

    def test_all_20_answers_exist_and_valid(self):
        """Verify all 20 benchmark answer JSON files exist and have valid structure."""
        expected_cases = [f"HHG-{i:03d}" for i in range(1, 21)]
        
        for cid in expected_cases:
            file_path = os.path.join(self.answers_dir, f"{cid}.json")
            self.assertTrue(os.path.exists(file_path), f"Missing answer file: {file_path}")

            with open(file_path, mode='r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate mandatory schema fields
            self.assertEqual(data["case_id"], cid)
            self.assertIn(data["verdict"], ("confirmed_fraud", "cleared", "uncertain"))
            self.assertGreater(data["confidence"], 0.0)
            self.assertLessEqual(data["confidence"], 1.0)
            self.assertIn(data["approval_route"], ("auto", "L1_analyst", "L2_senior_manager"))
            self.assertIsInstance(data["affected_txn_ids"], list)
            if data["verdict"] == "confirmed_fraud":
                self.assertGreater(len(data["affected_txn_ids"]), 0)
            self.assertIsInstance(data["exposure_usd"], (int, float))
            self.assertGreaterEqual(data["exposure_usd"], 0.0)
            self.assertIsInstance(data["sar_required"], bool)
            self.assertIsInstance(data["evidence"], list)
            self.assertGreater(len(data["evidence"]), 0)
            self.assertIn("playbook", data)

            # If SAR required, narrative must be non-empty
            if data["sar_required"]:
                self.assertGreater(len(data["sar_narrative"]), 50)

    def test_tigergraph_writeback_generation(self):
        """Verify generation of GSQL writeback statements for resolved cases."""
        file_path = os.path.join(self.answers_dir, "HHG-014.json")
        with open(file_path, mode='r', encoding='utf-8') as f:
            case_data = json.load(f)

        gsql = self.manager.generate_tigergraph_writeback_gsql([case_data])
        self.assertIn('INSERT INTO ClosedCase VALUES ("HHG-014"', gsql)
        self.assertIn('INSERT INTO ON_CARD VALUES ("HHG-014" ClosedCase, "C13487-K1" Card)', gsql)
        self.assertIn('INSERT INTO INVOLVES VALUES ("HHG-014" ClosedCase, "3478561" Transaction)', gsql)

if __name__ == '__main__':
    unittest.main()
