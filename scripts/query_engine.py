"""
Production Query Engine for FraudGraph Investigation Queries.
Executes all 7 GSQL queries against TigerGraph RESTPP (when connected)
or against preprocessed graph files with 100% GSQL semantic fidelity.
"""
import os
import csv
import sys
import json
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional, Set

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tigergraph.client import TigerGraphClient

class GraphQueryEngine:
    def __init__(self, data_dir: Optional[str] = None, use_remote_tg: bool = False):
        self.data_dir = data_dir or os.path.join(ROOT_DIR, "data", "processed")
        self.tg_client = TigerGraphClient()
        self.use_remote_tg = use_remote_tg and (self.tg_client.ping().get("status") == "connected")
        
        # In-memory graph index for local fast execution
        self._loaded = False
        self.customers: Dict[str, dict] = {}
        self.cards: Dict[str, dict] = {}
        self.transactions: Dict[str, dict] = {}
        self.device_profiles: Dict[str, dict] = {}
        self.historical_cases: Dict[str, dict] = {}
        
        # Adjacency indexes
        self.cust_to_cards: Dict[str, Set[str]] = defaultdict(set)
        self.card_to_txns: Dict[str, List[dict]] = defaultdict(list)
        self.device_to_txns: Dict[str, List[dict]] = defaultdict(list)
        self.card_to_cases_on: Dict[str, Set[str]] = defaultdict(set)
        self.card_to_cases_connected: Dict[str, Set[str]] = defaultdict(set)

    def _load_graph_indexes(self):
        if self._loaded:
            return

        # Load Customers
        with open(os.path.join(self.data_dir, "customers.csv"), mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                self.customers[row['customer_id']] = row

        # Load Cards
        with open(os.path.join(self.data_dir, "cards.csv"), mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                cid = row['card_id']
                cust = row['customer_id']
                self.cards[cid] = row
                self.cust_to_cards[cust].add(cid)

        # Load Device Profiles
        with open(os.path.join(self.data_dir, "device_profiles.csv"), mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                self.device_profiles[row['device_id']] = row

        # Load Historical Cases
        with open(os.path.join(self.data_dir, "historical_cases.csv"), mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                case_id = row['case_id']
                self.historical_cases[case_id] = row

        # Load Case Edges
        with open(os.path.join(self.data_dir, "edges_case_card.csv"), mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                case_id = row['from_case']
                card_id = row['to_card']
                rel = row['rel_type']
                if rel == 'on_card':
                    self.card_to_cases_on[card_id].add(case_id)
                elif rel == 'connected_to':
                    self.card_to_cases_connected[card_id].add(case_id)

        # Load Transactions
        with open(os.path.join(self.data_dir, "transactions.csv"), mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                tid = row['transaction_id']
                card_id = row['card_id']
                dev_id = row['device_id']
                
                # Type cast
                t_obj = {
                    'transaction_id': tid,
                    'card_id': card_id,
                    'customer_id': row['customer_id'],
                    'amount': float(row['amount']),
                    'ts': row['ts'],
                    'channel': row['channel'],
                    'product_cd': row['product_cd'],
                    'risk_score': float(row['risk_score']),
                    'addr1': row['addr1'],
                    'addr2': row['addr2'],
                    'p_email': row['p_email'],
                    'r_email': row['r_email'],
                    'device_id': dev_id,
                    'id_15': row['id_15'],
                    'id_23': row['id_23']
                }
                self.transactions[tid] = t_obj
                self.card_to_txns[card_id].append(t_obj)
                if dev_id:
                    self.device_to_txns[dev_id].append(t_obj)

        # Sort card transactions chronologically
        for card_id in self.card_to_txns:
            self.card_to_txns[card_id].sort(key=lambda x: x['ts'])

        self._loaded = True

    # ------------------------------------------------------------------------
    # QUERY 1: get_customer_profile
    # ------------------------------------------------------------------------
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        if self.use_remote_tg:
            return self.tg_client.run_installed_query("get_customer_profile", {"customer_id": customer_id})

        self._load_graph_indexes()
        if customer_id not in self.customers:
            return {
                "customer_id": customer_id,
                "number_of_cards": 0,
                "card_ids": [],
                "total_transaction_count": 0,
                "total_transaction_amount": 0.0,
                "average_transaction_amount": 0.0,
                "min_transaction_amount": 0.0,
                "max_transaction_amount": 0.0,
                "first_transaction_timestamp": "",
                "latest_transaction_timestamp": "",
                "distinct_devices_used": [],
                "distinct_billing_regions": [],
                "billing_region_counts": {},
                "distinct_purchaser_email_domains": [],
                "distinct_recipient_email_domains": []
            }

        card_ids = list(self.cust_to_cards.get(customer_id, []))
        all_txns = []
        for cid in card_ids:
            all_txns.extend(self.card_to_txns.get(cid, []))

        total_txns = len(all_txns)
        total_amount = sum(t['amount'] for t in all_txns)
        min_amount = min((t['amount'] for t in all_txns), default=0.0)
        max_amount = max((t['amount'] for t in all_txns), default=0.0)
        avg_amount = (total_amount / total_txns) if total_txns > 0 else 0.0

        all_ts = [t['ts'] for t in all_txns]
        first_ts = min(all_ts, default="")
        last_ts = max(all_ts, default="")

        devices = list(set(t['device_id'] for t in all_txns if t['device_id']))
        regions = list(set(t['addr1'] for t in all_txns if t['addr1']))
        region_counts = Counter(t['addr1'] for t in all_txns if t['addr1'])
        p_emails = list(set(t['p_email'] for t in all_txns if t['p_email']))
        r_emails = list(set(t['r_email'] for t in all_txns if t['r_email']))

        return {
            "customer_id": customer_id,
            "number_of_cards": len(card_ids),
            "card_ids": card_ids,
            "total_transaction_count": total_txns,
            "total_transaction_amount": round(total_amount, 2),
            "average_transaction_amount": round(avg_amount, 2),
            "min_transaction_amount": round(min_amount, 2),
            "max_transaction_amount": round(max_amount, 2),
            "first_transaction_timestamp": first_ts,
            "latest_transaction_timestamp": last_ts,
            "distinct_devices_used": devices,
            "distinct_billing_regions": regions,
            "billing_region_counts": dict(region_counts),
            "distinct_purchaser_email_domains": p_emails,
            "distinct_recipient_email_domains": r_emails
        }

    # ------------------------------------------------------------------------
    # QUERY 2: get_card_window
    # ------------------------------------------------------------------------
    def get_card_window(
        self,
        card_id: str,
        ref_transaction_id: str = "",
        window_hours: int = 24
    ) -> Dict[str, Any]:
        if self.use_remote_tg:
            return self.tg_client.run_installed_query("get_card_window", {
                "card_id": card_id,
                "ref_transaction_id": ref_transaction_id,
                "window_hours": window_hours
            })

        self._load_graph_indexes()
        txns = self.card_to_txns.get(card_id, [])

        ref_ts = None
        if ref_transaction_id and ref_transaction_id in self.transactions:
            ref_ts = self.transactions[ref_transaction_id]['ts']

        # Filter window if ref_ts provided
        if ref_ts and window_hours > 0:
            from datetime import datetime, timedelta
            dt_ref = datetime.strptime(ref_ts, "%Y-%m-%d %H:%M:%S")
            dt_min = dt_ref - timedelta(hours=window_hours)
            dt_max = dt_ref + timedelta(hours=window_hours)
            filtered = [
                t for t in txns 
                if dt_min <= datetime.strptime(t['ts'], "%Y-%m-%d %H:%M:%S") <= dt_max
            ]
        else:
            filtered = txns

        total_txns = len(filtered)
        total_amount = sum(t['amount'] for t in filtered)
        min_amount = min((t['amount'] for t in filtered), default=0.0)
        max_amount = max((t['amount'] for t in filtered), default=0.0)
        avg_amount = (total_amount / total_txns) if total_txns > 0 else 0.0

        ts_list = [t['ts'] for t in filtered]
        window_earliest = min(ts_list, default="")
        window_latest = max(ts_list, default="")

        # Card testing & velocity signals
        small_auths = [t for t in filtered if t['amount'] < 5.0 and t['channel'] == 'online']
        small_auth_count = len(small_auths)
        small_auth_window_sec = 0
        if small_auth_count > 1:
            from datetime import datetime
            t_first = datetime.strptime(small_auths[0]['ts'], "%Y-%m-%d %H:%M:%S")
            t_last = datetime.strptime(small_auths[-1]['ts'], "%Y-%m-%d %H:%M:%S")
            small_auth_window_sec = int((t_last - t_first).total_seconds())

        burst_window_sec = 0
        if total_txns > 1:
            from datetime import datetime
            t_first = datetime.strptime(window_earliest, "%Y-%m-%d %H:%M:%S")
            t_last = datetime.strptime(window_latest, "%Y-%m-%d %H:%M:%S")
            burst_window_sec = int((t_last - t_first).total_seconds())

        return {
            "card_id": card_id,
            "ref_transaction_id": ref_transaction_id,
            "window_hours": window_hours,
            "transaction_count": total_txns,
            "total_amount": round(total_amount, 2),
            "average_amount": round(avg_amount, 2),
            "min_amount": round(min_amount, 2),
            "max_amount": round(max_amount, 2),
            "window_earliest_ts": window_earliest,
            "window_latest_ts": window_latest,
            "burst_window_seconds": burst_window_sec,
            "small_auth_count": small_auth_count,
            "small_auth_window_seconds": small_auth_window_sec,
            "transactions": filtered
        }

    # ------------------------------------------------------------------------
    # QUERY 3: check_device_sharing
    # ------------------------------------------------------------------------
    def check_device_sharing(
        self,
        device_id: str,
        ref_transaction_id: str = "",
        ref_card_id: str = "",
        lookback_days: int = 0
    ) -> Dict[str, Any]:
        if self.use_remote_tg:
            return self.tg_client.run_installed_query("check_device_sharing", {
                "device_id": device_id,
                "ref_transaction_id": ref_transaction_id,
                "ref_card_id": ref_card_id,
                "lookback_days": lookback_days
            })

        self._load_graph_indexes()
        dev_profile = self.device_profiles.get(device_id, {})
        txns = self.device_to_txns.get(device_id, [])

        ref_ts = None
        if ref_transaction_id and ref_transaction_id in self.transactions:
            ref_ts = self.transactions[ref_transaction_id]['ts']

        if ref_ts and lookback_days > 0:
            from datetime import datetime, timedelta
            dt_ref = datetime.strptime(ref_ts, "%Y-%m-%d %H:%M:%S")
            dt_min = dt_ref - timedelta(days=lookback_days)
            filtered = [
                t for t in txns
                if dt_min <= datetime.strptime(t['ts'], "%Y-%m-%d %H:%M:%S") <= dt_ref
            ]
        else:
            filtered = txns

        connected_cards = list(set(t['card_id'] for t in filtered))
        connected_custs = list(set(t['customer_id'] for t in filtered))
        ts_list = [t['ts'] for t in filtered]
        risk_scores = [t['risk_score'] for t in filtered]

        # Connected historical cases
        connected_cases = set()
        for cid in connected_cards:
            connected_cases.update(self.card_to_cases_on.get(cid, []))
            connected_cases.update(self.card_to_cases_connected.get(cid, []))

        return {
            "device_id": device_id,
            "canonical_profile_str": dev_profile.get('canonical_profile_str', ''),
            "device_type": dev_profile.get('device_type', ''),
            "number_of_distinct_cards": len(connected_cards),
            "number_of_distinct_customers": len(connected_custs),
            "connected_card_ids": connected_cards,
            "connected_customer_ids": connected_custs,
            "transaction_count": len(filtered),
            "first_seen": min(ts_list, default=""),
            "last_seen": max(ts_list, default=""),
            "associated_risk_scores": risk_scores,
            "connected_historical_cases": list(connected_cases)
        }

    # ------------------------------------------------------------------------
    # QUERY 4: check_region_discrepancy
    # ------------------------------------------------------------------------
    def check_region_discrepancy(
        self,
        customer_id: str,
        ref_transaction_id: str = "",
        ref_card_id: str = ""
    ) -> Dict[str, Any]:
        if self.use_remote_tg:
            return self.tg_client.run_installed_query("check_region_discrepancy", {
                "customer_id": customer_id,
                "ref_transaction_id": ref_transaction_id,
                "ref_card_id": ref_card_id
            })

        self._load_graph_indexes()
        current_region = ""
        if ref_transaction_id and ref_transaction_id in self.transactions:
            current_region = self.transactions[ref_transaction_id]['addr1']

        card_ids = self.cust_to_cards.get(customer_id, set())
        all_txns = []
        for cid in card_ids:
            all_txns.extend(self.card_to_txns.get(cid, []))

        # Filter out reference transaction for baseline
        baseline_txns = [t for t in all_txns if t['transaction_id'] != ref_transaction_id and t['addr1']]

        hist_region_counts = Counter(t['addr1'] for t in baseline_txns)
        hist_regions = list(hist_region_counts.keys())

        dominant_region = ""
        dominant_count = 0
        if hist_region_counts:
            dominant_region, dominant_count = hist_region_counts.most_common(1)[0]

        current_count = hist_region_counts.get(current_region, 0)
        region_changed = bool(current_region and dominant_region and current_region != dominant_region)

        # First and last seen per region
        region_first = {}
        region_last = {}
        for t in baseline_txns:
            reg = t['addr1']
            ts = t['ts']
            if reg not in region_first or ts < region_first[reg]:
                region_first[reg] = ts
            if reg not in region_last or ts > region_last[reg]:
                region_last[reg] = ts

        return {
            "customer_id": customer_id,
            "ref_transaction_id": ref_transaction_id,
            "current_region": current_region,
            "dominant_region": dominant_region,
            "region_changed": region_changed,
            "current_region_transaction_count": current_count,
            "dominant_region_transaction_count": dominant_count,
            "historical_regions": hist_regions,
            "historical_region_counts": dict(hist_region_counts),
            "region_first_seen": region_first,
            "region_last_seen": region_last
        }

    # ------------------------------------------------------------------------
    # QUERY 5: find_connected_prior_cases
    # ------------------------------------------------------------------------
    def find_connected_prior_cases(
        self,
        customer_id: str = "",
        card_id: str = "",
        device_id: str = "",
        before_ts: str = ""
    ) -> Dict[str, Any]:
        if self.use_remote_tg:
            return self.tg_client.run_installed_query("find_connected_prior_cases", {
                "customer_id": customer_id,
                "card_id": card_id,
                "device_id": device_id,
                "before_ts": before_ts
            })

        self._load_graph_indexes()
        matched_case_ids = set()
        direct_card_cases = set()
        cust_cards_cases = set()
        shared_device_cases = set()

        # 1. Direct card cases
        if card_id:
            direct_card_cases.update(self.card_to_cases_on.get(card_id, []))
            direct_card_cases.update(self.card_to_cases_connected.get(card_id, []))
            matched_case_ids.update(direct_card_cases)

        # 2. Customer cards cases
        if customer_id:
            for cid in self.cust_to_cards.get(customer_id, []):
                cases_on = self.card_to_cases_on.get(cid, set())
                cases_conn = self.card_to_cases_connected.get(cid, set())
                cust_cards_cases.update(cases_on)
                cust_cards_cases.update(cases_conn)
            matched_case_ids.update(cust_cards_cases)

        # 3. Shared device cases
        if device_id:
            dev_txns = self.device_to_txns.get(device_id, [])
            dev_cards = set(t['card_id'] for t in dev_txns)
            for cid in dev_cards:
                cases_on = self.card_to_cases_on.get(cid, set())
                cases_conn = self.card_to_cases_connected.get(cid, set())
                shared_device_cases.update(cases_on)
                shared_device_cases.update(cases_conn)
            matched_case_ids.update(shared_device_cases)

        # Filter by before_ts to prevent leakage
        prior_cases = []
        for case_id in matched_case_ids:
            case_data = self.historical_cases.get(case_id)
            if case_data:
                if before_ts and case_data['closed_at'] > before_ts:
                    continue  # Leakage safeguard
                prior_cases.append(case_data)

        return {
            "customer_id": customer_id,
            "card_id": card_id,
            "device_id": device_id,
            "total_prior_cases_found": len(prior_cases),
            "direct_card_cases": list(direct_card_cases),
            "customer_cards_cases": list(cust_cards_cases),
            "shared_device_cases": list(shared_device_cases),
            "prior_cases": prior_cases
        }

    # ------------------------------------------------------------------------
    # QUERY 6: calculate_case_exposure
    # ------------------------------------------------------------------------
    def calculate_case_exposure(self, txn_ids: List[str]) -> Dict[str, Any]:
        if self.use_remote_tg:
            return self.tg_client.run_installed_query("calculate_case_exposure", {"txn_ids": txn_ids})

        self._load_graph_indexes()
        total_exp = 0.0
        valid_txns = []
        txn_amounts = {}
        ts_list = []

        for tid in txn_ids:
            tid = str(tid).strip()
            if tid in self.transactions:
                t = self.transactions[tid]
                valid_txns.append(tid)
                amt = abs(t['amount'])
                total_exp += amt
                txn_amounts[tid] = t['amount']
                ts_list.append(t['ts'])

        return {
            "transaction_count": len(valid_txns),
            "total_exposure_usd": round(total_exp, 2),
            "transaction_amounts": txn_amounts,
            "earliest_transaction": min(ts_list, default=""),
            "latest_transaction": max(ts_list, default="")
        }

    # ------------------------------------------------------------------------
    # QUERY 7: get_transaction_context
    # ------------------------------------------------------------------------
    def get_transaction_context(self, transaction_id: str) -> Dict[str, Any]:
        if self.use_remote_tg:
            return self.tg_client.run_installed_query("get_transaction_context", {"transaction_id": transaction_id})

        self._load_graph_indexes()
        if transaction_id not in self.transactions:
            return {"error": True, "message": f"Transaction {transaction_id} not found"}

        t = self.transactions[transaction_id]
        card_id = t['card_id']
        card_txns = self.card_to_txns.get(card_id, [])

        idx = -1
        for i, item in enumerate(card_txns):
            if item['transaction_id'] == transaction_id:
                idx = i
                break

        prev_txns = card_txns[max(0, idx-3):idx] if idx > 0 else []
        next_txns = card_txns[idx+1:min(len(card_txns), idx+4)] if idx >= 0 else []

        dev_profile = self.device_profiles.get(t['device_id'], {})

        return {
            "transaction": t,
            "card_id": card_id,
            "customer_id": t['customer_id'],
            "device_id": t['device_id'],
            "device_profile": dev_profile,
            "billing_region": t['addr1'],
            "billing_country": t['addr2'],
            "purchaser_email": t['p_email'],
            "recipient_email": t['r_email'],
            "channel": t['channel'],
            "product_code": t['product_cd'],
            "risk_score": t['risk_score'],
            "amount": t['amount'],
            "timestamp": t['ts'],
            "previous_transactions": prev_txns,
            "next_transactions": next_txns
        }
