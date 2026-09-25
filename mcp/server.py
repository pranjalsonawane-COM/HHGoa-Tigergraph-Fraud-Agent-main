"""
TigerGraph Model Context Protocol (MCP) Server for Fraud Investigation.

Exposes TigerGraph graph traversal, GraphRAG, Case Memory, and Policy tools
to LLM Agents over standard MCP JSON-RPC 2.0 protocol.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.query_engine import GraphQueryEngine
from scripts.case_memory import CaseMemoryEngine
from scripts.graph_rag import GraphRAGEngine
from scripts.policy_engine import FraudPolicyEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tigergraph_mcp_server")

class TigerGraphMCPServer:
    """Standard Model Context Protocol Server for TigerGraph Fraud Investigation."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir
        self.query_engine = GraphQueryEngine(data_dir=data_dir)
        self.case_memory = CaseMemoryEngine(data_dir=data_dir)
        self.graph_rag = GraphRAGEngine(data_dir=data_dir)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns the list of available MCP tools and their JSON schemas."""
        return [
            {
                "name": "tigergraph_get_customer_profile",
                "description": "Retrieves cardholder profile, historical transaction velocity, average spending, dominant billing regions, known device profiles, and active cards.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Unique customer identifier (e.g., 'C13487', 'C12382')"
                        }
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "tigergraph_get_card_window",
                "description": "Retrieves transactions on a card in a specified time window before a reference transaction to detect rapid authorizations or card testing bursts.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "card_id": {
                            "type": "string",
                            "description": "Canonical card identifier (e.g., 'C13487-K1')"
                        },
                        "ref_transaction_id": {
                            "type": "string",
                            "description": "Target transaction ID to inspect window before"
                        },
                        "window_hours": {
                            "type": "integer",
                            "description": "Time window in hours prior to reference transaction (default: 24)",
                            "default": 24
                        }
                    },
                    "required": ["card_id", "ref_transaction_id"]
                }
            },
            {
                "name": "tigergraph_check_device_sharing",
                "description": "Queries the graph for all cards and customers sharing a device profile, and retrieves connected historical fraud cases.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Canonical device profile ID (e.g., 'DEV_13b0f4b32516')"
                        },
                        "ref_transaction_id": {
                            "type": "string",
                            "description": "Optional reference transaction ID",
                            "default": ""
                        },
                        "ref_card_id": {
                            "type": "string",
                            "description": "Optional reference card ID to exclude self",
                            "default": ""
                        },
                        "lookback_days": {
                            "type": "integer",
                            "description": "Days to look back (0 for all time)",
                            "default": 0
                        }
                    },
                    "required": ["device_id"]
                }
            },
            {
                "name": "tigergraph_check_region_discrepancy",
                "description": "Compares transaction billing region against customer historical dominant home region and calculates region frequency.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer identifier"
                        },
                        "ref_transaction_id": {
                            "type": "string",
                            "description": "Transaction ID to inspect"
                        }
                    },
                    "required": ["customer_id", "ref_transaction_id"]
                }
            },
            {
                "name": "tigergraph_find_connected_prior_cases",
                "description": "Finds prior closed fraud cases connected to customer, card, or shared device profile with temporal anti-leakage protection.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer identifier"
                        },
                        "card_id": {
                            "type": "string",
                            "description": "Card identifier"
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Device profile ID"
                        },
                        "before_ts": {
                            "type": "string",
                            "description": "ISO timestamp cutoff (e.g. '2016-11-22 16:11:00') preventing future leakage"
                        }
                    },
                    "required": ["before_ts"]
                }
            },
            {
                "name": "case_memory_search_precedents",
                "description": "Performs hybrid BM25 and graph search across 5,565 historical closed cases to extract consensus outcomes, standard actions, and SAR benchmarks.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query_text": {
                            "type": "string",
                            "description": "Free text query describing anomaly or device signature"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Optional fraud pattern filter (e.g., 'undocumented', 'card_testing', 'out_of_region_use')"
                        },
                        "before_ts": {
                            "type": "string",
                            "description": "Temporal cutoff timestamp"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of precedents to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query_text"]
                }
            },
            {
                "name": "graphrag_investigate_alert",
                "description": "Performs one-shot end-to-end multi-hop GraphRAG investigation, returning complete grounded dossier, detected typology, policy compliance (R1-R10), and LLM prompt context.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {
                            "type": "string",
                            "description": "Flagged transaction ID to investigate"
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Optional customer ID"
                        },
                        "card_id": {
                            "type": "string",
                            "description": "Optional card ID"
                        },
                        "alert_timestamp": {
                            "type": "string",
                            "description": "Optional alert timestamp for anti-leakage enforcement"
                        }
                    },
                    "required": ["transaction_id"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the requested tool by name with arguments."""
        if tool_name == "tigergraph_get_customer_profile":
            return self.query_engine.get_customer_profile(arguments.get("customer_id", ""))

        elif tool_name == "tigergraph_get_card_window":
            return self.query_engine.get_card_window(
                card_id=arguments.get("card_id", ""),
                ref_transaction_id=arguments.get("ref_transaction_id", ""),
                window_hours=int(arguments.get("window_hours", 24))
            )

        elif tool_name == "tigergraph_check_device_sharing":
            return self.query_engine.check_device_sharing(
                device_id=arguments.get("device_id", ""),
                ref_transaction_id=arguments.get("ref_transaction_id", ""),
                ref_card_id=arguments.get("ref_card_id", ""),
                lookback_days=int(arguments.get("lookback_days", 0))
            )

        elif tool_name == "tigergraph_check_region_discrepancy":
            return self.query_engine.check_region_discrepancy(
                customer_id=arguments.get("customer_id", ""),
                ref_transaction_id=arguments.get("ref_transaction_id", "")
            )

        elif tool_name == "tigergraph_find_connected_prior_cases":
            return self.query_engine.find_connected_prior_cases(
                customer_id=arguments.get("customer_id", ""),
                card_id=arguments.get("card_id", ""),
                device_id=arguments.get("device_id", ""),
                before_ts=arguments.get("before_ts", "")
            )

        elif tool_name == "case_memory_search_precedents":
            precedents = self.case_memory.search_precedents(
                query_text=arguments.get("query_text", ""),
                pattern=arguments.get("pattern"),
                before_ts=arguments.get("before_ts"),
                top_k=int(arguments.get("top_k", 5))
            )
            insights = self.case_memory.extract_precedent_insights(precedents)
            return {
                "precedents": precedents,
                "insights": insights
            }

        elif tool_name == "graphrag_investigate_alert":
            return self.graph_rag.investigate_alert(
                transaction_id=arguments.get("transaction_id", ""),
                customer_id=arguments.get("customer_id"),
                card_id=arguments.get("card_id"),
                alert_timestamp=arguments.get("alert_timestamp")
            )

        else:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

    def handle_json_rpc(self, request_json: str) -> str:
        """Handles a single JSON-RPC 2.0 MCP request string and returns the response string."""
        try:
            req = json.loads(request_json)
        except Exception as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            })

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tool_definitions()}
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                tool_result = self.execute_tool(tool_name, tool_args)
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_result, indent=2)
                            }
                        ]
                    }
                })
            except Exception as e:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": f"Tool execution failed: {str(e)}"}
                })

        elif method == "initialize":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "tigergraph-fraud-mcp-server",
                        "version": "1.0.0"
                    }
                }
            })

        elif method == "ping":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            })

        else:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })

    def run_stdio(self):
        """Runs MCP server loop over standard input/output."""
        logger.info("Starting TigerGraph MCP Server on stdio...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            response = self.handle_json_rpc(line)
            sys.stdout.write(response + "\n")
            sys.stdout.flush()

if __name__ == '__main__':
    server = TigerGraphMCPServer()
    server.run_stdio()
