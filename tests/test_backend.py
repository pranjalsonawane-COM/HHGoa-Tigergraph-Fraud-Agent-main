"""
Unit tests for Backend REST API Endpoints.
"""
import unittest
import os
import sys
import json
import threading
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.server import run_server
from http.server import HTTPServer
from backend.server import FraudAgentRequestHandler

class TestBackendServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8888
        cls.httpd = HTTPServer(('localhost', cls.port), FraudAgentRequestHandler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_health_endpoint(self):
        """Verify GET /health returns 200 OK and healthy status."""
        url = f"http://localhost:{self.port}/health"
        with urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode('utf-8'))
            self.assertEqual(data["status"], "healthy")

    def test_stats_endpoint(self):
        """Verify GET /api/stats returns aggregate metrics."""
        url = f"http://localhost:{self.port}/api/stats"
        with urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode('utf-8'))
            self.assertEqual(data["total_benchmark_cases"], 20)
            self.assertEqual(data["graph_vertices_indexed"], 634810)

    def test_get_all_cases_endpoint(self):
        """Verify GET /api/cases lists all benchmark cases."""
        url = f"http://localhost:{self.port}/api/cases"
        with urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode('utf-8'))
            self.assertEqual(data["count"], 20)
            self.assertEqual(len(data["cases"]), 20)

    def test_get_single_case_endpoint(self):
        """Verify GET /api/cases/HHG-014 returns case details."""
        url = f"http://localhost:{self.port}/api/cases/HHG-014"
        with urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode('utf-8'))
            self.assertEqual(data["case_id"], "HHG-014")
            self.assertEqual(data["pattern"], "undocumented")
            self.assertTrue(data["sar_required"])

    def test_get_graph_topology_endpoint(self):
        """Verify GET /api/graph/3478561 returns nodes and links."""
        url = f"http://localhost:{self.port}/api/graph/3478561"
        with urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode('utf-8'))
            self.assertIn("nodes", data)
            self.assertIn("links", data)
            self.assertGreater(len(data["nodes"]), 0)

if __name__ == '__main__':
    unittest.main()
