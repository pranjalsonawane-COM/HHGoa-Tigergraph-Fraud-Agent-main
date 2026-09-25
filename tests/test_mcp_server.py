"""
Unit tests for TigerGraph Model Context Protocol (MCP) Server.
"""
import unittest
import os
import sys
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from mcp.server import TigerGraphMCPServer

class TestMCPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TigerGraphMCPServer()

    def test_mcp_initialize(self):
        """Verify standard MCP initialize handshake."""
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        res_str = self.server.handle_json_rpc(json.dumps(req))
        res = json.loads(res_str)
        self.assertEqual(res["id"], 1)
        self.assertIn("serverInfo", res["result"])
        self.assertEqual(res["result"]["serverInfo"]["name"], "tigergraph-fraud-mcp-server")

    def test_mcp_tools_list(self):
        """Verify all 7 investigation tools are properly defined and exposed."""
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        res_str = self.server.handle_json_rpc(json.dumps(req))
        res = json.loads(res_str)
        tools = res["result"]["tools"]
        self.assertEqual(len(tools), 7)
        tool_names = [t["name"] for t in tools]
        self.assertIn("tigergraph_get_customer_profile", tool_names)
        self.assertIn("tigergraph_get_card_window", tool_names)
        self.assertIn("tigergraph_check_device_sharing", tool_names)
        self.assertIn("tigergraph_check_region_discrepancy", tool_names)
        self.assertIn("tigergraph_find_connected_prior_cases", tool_names)
        self.assertIn("case_memory_search_precedents", tool_names)
        self.assertIn("graphrag_investigate_alert", tool_names)

    def test_mcp_call_customer_profile(self):
        """Verify calling tigergraph_get_customer_profile via MCP."""
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "tigergraph_get_customer_profile",
                "arguments": {"customer_id": "C13487"}
            }
        }
        res_str = self.server.handle_json_rpc(json.dumps(req))
        res = json.loads(res_str)
        self.assertEqual(res["id"], 3)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertEqual(data["customer_id"], "C13487")
        self.assertGreater(data.get("total_transaction_count", 0), 0)
        self.assertIn("C13487-K1", data.get("card_ids", []))

    def test_mcp_call_graphrag_investigate_alert(self):
        """Verify calling graphrag_investigate_alert via MCP."""
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "graphrag_investigate_alert",
                "arguments": {
                    "transaction_id": "3478561",
                    "customer_id": "C13487",
                    "card_id": "C13487-K1",
                    "alert_timestamp": "2016-11-22 16:11:00"
                }
            }
        }
        res_str = self.server.handle_json_rpc(json.dumps(req))
        res = json.loads(res_str)
        self.assertEqual(res["id"], 4)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertEqual(data["summary"]["detected_pattern"], "undocumented")
        self.assertEqual(data["summary"]["approval_route"], "L2_senior_manager")

    def test_mcp_invalid_tool_error(self):
        """Verify error handling for invalid tool invocation."""
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "non_existent_tool",
                "arguments": {}
            }
        }
        res_str = self.server.handle_json_rpc(json.dumps(req))
        res = json.loads(res_str)
        self.assertEqual(res["id"], 5)
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], -32603)

if __name__ == '__main__':
    unittest.main()
