# TigerGraph Model Context Protocol (MCP) Server

## 1. Overview

The **TigerGraph MCP Server** (`mcp/server.py`) provides a standard **Model Context Protocol (MCP)** JSON-RPC 2.0 interface. This allows any modern AI Agent, LLM platform, or IDE (such as Claude Desktop, Antigravity, Cursor, LangChain, AutoGen, ReAct agents) to directly invoke TigerGraph fraud investigation tools.

---

## 2. Available MCP Tools

| Tool Name | Purpose | Key Parameters |
| :--- | :--- | :--- |
| `tigergraph_get_customer_profile` | Retrieves cardholder baseline, total spend, transaction counts, known devices & dominant regions | `customer_id` (str) |
| `tigergraph_get_card_window` | Temporal velocity window & micro-authorization burst detection | `card_id` (str), `ref_transaction_id` (str), `window_hours` (int) |
| `tigergraph_check_device_sharing` | Multi-card syndicate detection across shared devices & proxy networks | `device_id` (str), `ref_transaction_id` (str), `lookback_days` (int) |
| `tigergraph_check_region_discrepancy` | In-person billing region anomaly detection vs. home region | `customer_id` (str), `ref_transaction_id` (str) |
| `tigergraph_find_connected_prior_cases` | Retrieves connected historical cases with strict anti-leakage protection | `customer_id` (str), `card_id` (str), `device_id` (str), `before_ts` (str) |
| `case_memory_search_precedents` | Hybrid BM25/graph precedent retrieval across 5,565 closed cases | `query_text` (str), `pattern` (str), `before_ts` (str), `top_k` (int) |
| `graphrag_investigate_alert` | One-shot end-to-end multi-hop GraphRAG investigation dossier | `transaction_id` (str), `alert_timestamp` (str) |

---

## 3. Client Configuration

### Claude Desktop / Antigravity / Cursor Configuration

Add the following to your `claude_desktop_config.json` or MCP settings:

```json
{
  "mcpServers": {
    "tigergraph-fraud-investigation": {
      "command": "python",
      "args": [
        "d:/HHGOA-Fraud-Agent/mcp/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

---

## 4. JSON-RPC Protocol Examples

### 1. List Available Tools (`tools/list`)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### 2. Invoke GraphRAG Investigation (`tools/call`)
```json
{
  "jsonrpc": "2.0",
  "id": 2,
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
```

---

## 5. Verification & Tests

The MCP server is tested with `tests/test_mcp_server.py`:
- Protocol handshake (`initialize`).
- Tool enumeration (`tools/list`).
- Real tool execution with GraphRAG and TigerGraph queries.
- Error handling for invalid tool names and missing arguments.
