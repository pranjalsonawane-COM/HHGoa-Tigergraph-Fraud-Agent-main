"""
Unit tests for Case Memory & Precedent Retrieval Engine.
"""
import unittest
import os
import sys
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.case_memory import CaseMemoryEngine

class TestCaseMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.memory = CaseMemoryEngine()

    def test_total_indexed_cases(self):
        """Verify all 5,565 historical cases are loaded and indexed."""
        self.assertEqual(len(self.memory.cases), 5565)
        self.assertGreater(len(self.memory.inverted_index), 1000)
        self.assertGreater(self.memory.avg_doc_length, 10.0)

    def test_precedent_search_proxy_syndicate(self):
        """Search for proxy/device syndicate precedents matching HHG-014 characteristics."""
        results = self.memory.search_precedents(
            query_text="SM-G935F anonymous proxy shared device ring",
            pattern="undocumented",
            before_ts="2016-11-22 16:11:00",
            top_k=5
        )
        self.assertGreaterEqual(len(results), 1)
        # Verify retrieved cases were closed prior to timestamp
        for r in results:
            self.assertLessEqual(r["closed_at"], "2016-11-22 16:11:00")
            self.assertIn("outcome", r)
        
        # Test insight extraction
        insights = self.memory.extract_precedent_insights(results)
        self.assertEqual(insights["consensus_outcome"], "confirmed_fraud")
        self.assertIn("BLOCK_CARD", insights["common_actions"])

    def test_anti_leakage_temporal_filter(self):
        """Verify no future cases leak into historical search."""
        cutoff = "2016-08-01 00:00:00"
        results = self.memory.search_precedents(
            query_text="unrecognized online purchase card not present",
            before_ts=cutoff,
            top_k=10
        )
        for r in results:
            self.assertLessEqual(r["closed_at"], cutoff)

    def test_precedent_search_out_of_region(self):
        """Search for out of region precedents."""
        results = self.memory.search_precedents(
            query_text="out of region travel billing confirmed",
            pattern="out_of_region_use",
            top_k=5
        )
        self.assertEqual(len(results), 5)
        insights = self.memory.extract_precedent_insights(results)
        self.assertGreaterEqual(insights["num_precedents"], 5)

    def test_retrieval_speed(self):
        """Ensure search executes rapidly under 100ms."""
        # Warmup
        _ = self.memory.search_precedents(query_text="warmup query", top_k=2)
        start = time.perf_counter()
        _ = self.memory.search_precedents(
            query_text="card testing small authorization amounts",
            pattern="card_testing",
            top_k=5
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertLess(elapsed_ms, 100.0)

if __name__ == '__main__':
    unittest.main()
