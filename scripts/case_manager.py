"""
Case Manager & Benchmark Answer Generator for Hackathon Evaluation.

Processes all 20 benchmark evaluation cases (HHG-001 through HHG-020),
executes the full autonomous ReAct agent pipeline, generates official JSON answer files,
and prepares TigerGraph graph writeback payloads.
"""
import os
import sys
import csv
import json
from typing import Dict, Any, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.agent_core import FraudInvestigationAgent
from scripts.nba_engine import NextBestActionEngine

class CaseManager:
    """Manages investigation lifecycle and benchmark answer generation for all cases."""

    def __init__(self, data_dir: Optional[str] = None, output_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'processed'))
        self.output_dir = output_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'answers'))
        self.agent = FraudInvestigationAgent(data_dir=self.data_dir)
        self.nba = NextBestActionEngine()
        os.makedirs(self.output_dir, exist_ok=True)

    def process_all_benchmark_cases(self, case_pack_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Loads case_pack.csv, investigates all 20 benchmark cases, and generates answer JSON files.
        """
        if case_pack_path is None:
            case_pack_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'case_pack.csv'))

        if not os.path.exists(case_pack_path):
            raise FileNotFoundError(f"case_pack.csv not found at: {case_pack_path}")

        results: List[Dict[str, Any]] = []

        with open(case_pack_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row["case_id"]
                opened_at = row["opened_at"]
                trigger_type = row["trigger_type"]
                trigger_text = row["trigger_text"]
                flagged_tid = row["flagged_txn_id"]
                card_id = row.get("card_id", "")
                cust_id = row.get("customer_id", "")
                raw_score = row.get("risk_score", "")
                risk_score = float(raw_score) if raw_score else None

                # Execute autonomous agent investigation
                dossier = self.agent.run_investigation(
                    case_id=cid,
                    trigger_type=trigger_type,
                    trigger_text=trigger_text,
                    flagged_txn_id=flagged_tid,
                    card_id=card_id,
                    customer_id=cust_id,
                    opened_at=opened_at,
                    initial_risk_score=risk_score
                )

                # Generate operational NBA playbook
                playbook = self.nba.generate_nba_playbook(dossier)
                dossier["playbook"] = playbook

                # Build benchmark evaluation JSON payload
                answer_payload = {
                    "case_id": dossier["case_id"],
                    "opened_at": dossier["opened_at"],
                    "trigger_type": dossier["trigger_type"],
                    "flagged_txn_id": dossier["flagged_txn_id"],
                    "customer_id": dossier["customer_id"],
                    "card_id": dossier["card_id"],
                    "verdict": dossier["verdict"],
                    "confidence": round(float(dossier["confidence"]), 2),
                    "pattern": dossier["pattern"],
                    "pattern_description": dossier["pattern_description"],
                    "affected_txn_ids": dossier["affected_txn_ids"],
                    "first_suspicious_txn_id": dossier["first_suspicious_txn_id"],
                    "exposure_usd": round(float(dossier["exposure_usd"]), 2),
                    "approval_route": dossier["approval_route"],
                    "next_best_action": dossier["next_best_action"],
                    "recommended_actions": dossier["recommended_actions"],
                    "triggered_rules": dossier["triggered_rules"],
                    "sar_required": dossier["sar_required"],
                    "sar_narrative": dossier["sar_narrative"],
                    "evidence": dossier["evidence"],
                    "playbook": dossier["playbook"],
                    "trace_steps_count": len(dossier["trace_steps"])
                }

                # Save individual answer JSON file
                out_file = os.path.join(self.output_dir, f"{cid}.json")
                with open(out_file, mode='w', encoding='utf-8') as out_f:
                    json.dump(answer_payload, out_f, indent=2)

                results.append(answer_payload)

        return results

    def generate_tigergraph_writeback_gsql(self, resolved_cases: List[Dict[str, Any]]) -> str:
        """
        Generates GSQL INSERT statements to persist resolved benchmark cases into TigerGraph.
        """
        statements = []
        for c in resolved_cases:
            cid = c["case_id"]
            cust_id = c["customer_id"]
            card_id = c["card_id"]
            opened_at = c["opened_at"]
            closed_at = c.get("closed_at", opened_at)
            outcome = c["verdict"]
            pattern = c["pattern"]
            exposure = c["exposure_usd"]
            sar = "Yes" if c.get("sar_required") else "No"
            actions = "|".join(c.get("recommended_actions", []))
            notes = c.get("sar_narrative", "").replace('"', "'").replace("\n", " ")[:250]

            stmt = (
                f'INSERT INTO ClosedCase VALUES ("{cid}", "{cust_id}", "{card_id}", "{opened_at}", '
                f'"{closed_at}", "{outcome}", "{pattern}", {exposure}, "{sar}", "{actions}", "{notes}");\n'
                f'INSERT INTO ON_CARD VALUES ("{cid}" ClosedCase, "{card_id}" Card);\n'
            )
            for tid in c.get("affected_txn_ids", []):
                stmt += f'INSERT INTO INVOLVES VALUES ("{cid}" ClosedCase, "{tid}" Transaction);\n'
            statements.append(stmt)

        return "\n".join(statements)

if __name__ == '__main__':
    manager = CaseManager()
    print("Processing all 20 benchmark cases from case_pack.csv...")
    cases = manager.process_all_benchmark_cases()
    print(f"Successfully processed {len(cases)} benchmark cases and saved to answers/*.json")
