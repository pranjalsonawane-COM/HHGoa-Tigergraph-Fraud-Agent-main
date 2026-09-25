"""
TigerGraph Client & Driver for Fraud Investigation Agent.
Supports RESTPP API, Token Auth, GSQL Query Execution, and Local Schema Validation.
"""
import os
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional, List

class TigerGraphClient:
    def __init__(self, config_path: Optional[str] = None):
        self.config = {
            "host": os.getenv("TG_HOST", "http://127.0.0.1"),
            "restpp_port": os.getenv("TG_RESTPP_PORT", "9000"),
            "gsql_port": os.getenv("TG_GSQL_PORT", "14240"),
            "graph_name": os.getenv("TG_GRAPH", "FraudGraph"),
            "username": os.getenv("TG_USERNAME", "tigergraph"),
            "password": os.getenv("TG_PASSWORD", "tigergraph"),
            "secret": os.getenv("TG_SECRET", ""),
            "token": os.getenv("TG_TOKEN", ""),
            "use_tls": os.getenv("TG_USE_TLS", "false").lower() == "true"
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, mode='r', encoding='utf-8') as f:
                file_config = json.load(f)
                self.config.update(file_config)
                
        # Format base URL
        host = self.config["host"].rstrip("/")
        if not host.startswith("http://") and not host.startswith("https://"):
            scheme = "https://" if self.config["use_tls"] else "http://"
            host = scheme + host
        self.base_url = host
        self.restpp_url = f"{self.base_url}:{self.config['restpp_port']}"

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config["token"]:
            headers["Authorization"] = f"Bearer {self.config['token']}"
        return headers

    def ping(self) -> Dict[str, Any]:
        """Test connection to TigerGraph RESTPP server."""
        url = f"{self.restpp_url}/echo"
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=5) as response:
                return {"status": "connected", "response": json.loads(response.read().decode('utf-8'))}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def request_token(self) -> Optional[str]:
        """Request auth token using secret."""
        if not self.config["secret"]:
            return None
        url = f"{self.restpp_url}/requesttoken?secret={self.config['secret']}"
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode('utf-8'))
                if not res.get("error"):
                    self.config["token"] = res.get("results", {}).get("token", "")
                    return self.config["token"]
        except Exception as e:
            print(f"Error requesting token: {e}")
        return None

    def run_installed_query(self, query_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an installed GSQL query via RESTPP."""
        query_str = urllib.parse.urlencode(params)
        url = f"{self.restpp_url}/query/{self.config['graph_name']}/{query_name}?{query_str}"
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            return {"error": True, "code": e.code, "message": err_body}
        except Exception as e:
            return {"error": True, "message": str(e)}

    def get_vertex_count(self, vertex_type: str) -> Dict[str, Any]:
        """Queries vertex statistics for a specific vertex type."""
        url = f"{self.restpp_url}/graph/{self.config['graph_name']}/vertices/{vertex_type}?count_only=true"
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": True, "message": str(e)}

    def get_schema_summary(self) -> Dict[str, Any]:
        """Returns structured metadata of the FraudGraph schema."""
        return {
            "graph_name": self.config["graph_name"],
            "vertices": [
                "Customer", "Card", "Transaction", "DeviceProfile",
                "BillingRegion", "EmailDomain", "ClosedCase"
            ],
            "edges": [
                "OWNS", "MADE", "FROM_DEVICE", "BILLED_IN",
                "PURCHASER_EMAIL", "RECIPIENT_EMAIL", "NEXT",
                "INVOLVES", "ON_CARD", "CONNECTED_TO"
            ]
        }
