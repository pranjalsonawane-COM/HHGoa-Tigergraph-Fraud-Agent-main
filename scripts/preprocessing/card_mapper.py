"""
Deterministic Card Mapper for TigerGraph Agentic Fraud Investigation (HHGOA IEEE-CIS).
Maps each transaction and customer to a canonical card_id (<customer_id>-K<n>).
"""
import csv
from collections import defaultdict
from typing import Dict, Tuple, Optional

class CardMapper:
    def __init__(self):
        self.sig_to_card: Dict[Tuple[str, Tuple[str, ...]], str] = {}
        self.cust_cards: Dict[str, set] = defaultdict(set)
        self.is_fitted = False

    def fit(self, closed_cases_path: str, case_pack_path: str, transactions_path: str):
        """
        Builds the deterministic signature-to-card mapping using labeled cases as ground truth
        and chronological assignment for unlabeled signatures.
        """
        known_txn_to_card = {}
        
        # 1. Ingest closed cases
        with open(closed_cases_history_path := closed_cases_path, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                card = row['card_id'].strip()
                for tid in row['txn_ids'].split('|'):
                    tid = tid.strip()
                    if tid:
                        known_txn_to_card[tid] = card
                        
        # 2. Ingest benchmark case pack
        with open(case_pack_path, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                card = row['card_id'].strip()
                tid = row['flagged_txn_id'].strip()
                if tid:
                    known_txn_to_card[tid] = card

        # 3. Stream transactions to register known signatures & chronological appearance
        cust_sigs_chrono = defaultdict(list)
        with open(transactions_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row['customer_id'].strip()
                tid = row['TransactionID'].strip()
                sig = (
                    row['card1'].strip(),
                    row['card2'].strip(),
                    row['card3'].strip(),
                    row['card4'].strip(),
                    row['card5'].strip(),
                    row['card6'].strip()
                )
                cust_sig_key = (cid, sig)
                
                if cust_sig_key not in self.sig_to_card:
                    if cust_sig_key not in cust_sigs_chrono[cid]:
                        cust_sigs_chrono[cid].append(cust_sig_key)
                        
                if tid in known_txn_to_card:
                    self.sig_to_card[cust_sig_key] = known_txn_to_card[tid]

        # 4. Fill unassigned signatures with deterministic -K<n> suffixes
        for cid, sig_keys in cust_sigs_chrono.items():
            used_k_numbers = set()
            for k in sig_keys:
                if k in self.sig_to_card:
                    suffix = self.sig_to_card[k].split('-')[-1]
                    if suffix.startswith('K') and suffix[1:].isdigit():
                        used_k_numbers.add(int(suffix[1:]))
                        
            curr_k = 1
            for k in sig_keys:
                if k not in self.sig_to_card:
                    while curr_k in used_k_numbers:
                        curr_k += 1
                    self.sig_to_card[k] = f"{cid}-K{curr_k}"
                    used_k_numbers.add(curr_k)
                    
            for k in sig_keys:
                self.cust_cards[cid].add(self.sig_to_card[k])

        self.is_fitted = True

    def get_card_id(self, customer_id: str, card1: str, card2: str, card3: str, card4: str, card5: str, card6: str) -> str:
        if not self.is_fitted:
            raise RuntimeError("CardMapper must be fitted before calling get_card_id")
        sig = (
            card1.strip(),
            card2.strip(),
            card3.strip(),
            card4.strip(),
            card5.strip(),
            card6.strip()
        )
        return self.sig_to_card.get((customer_id.strip(), sig), f"{customer_id.strip()}-K1")
