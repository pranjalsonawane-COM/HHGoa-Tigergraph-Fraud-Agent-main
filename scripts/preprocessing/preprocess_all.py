"""
End-to-end Preprocessing Pipeline for TigerGraph Agentic Fraud Investigation.
Converts raw datasets into normalized, graph-ready CSV files in data/processed/.
"""
import os
import csv
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Set

# Ensure workspace root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.preprocessing.card_mapper import CardMapper
from scripts.preprocessing.device_mapper import DeviceMapper

RAW_DIR = "d:/HHGOA-Fraud-Agent"
PROCESSED_DIR = os.path.join(RAW_DIR, "data", "processed")

def ensure_dirs():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(os.path.join(RAW_DIR, "data", "raw"), exist_ok=True)

def run_pipeline():
    ensure_dirs()
    print("=== STARTING PREPROCESSING PIPELINE ===")

    # 1. Initialize and fit CardMapper
    print("\n[1/6] Fitting Deterministic CardMapper...")
    card_mapper = CardMapper()
    card_mapper.fit(
        closed_cases_path=os.path.join(RAW_DIR, "closed_cases_history.csv"),
        case_pack_path=os.path.join(RAW_DIR, "case_pack.csv"),
        transactions_path=os.path.join(RAW_DIR, "transactions.csv")
    )
    print(f"  CardMapper fitted successfully. Mapped {len(card_mapper.sig_to_card)} unique signatures.")

    # 2. Ingest identity.csv and build DeviceProfiles
    print("\n[2/6] Processing identity.csv & building DeviceProfiles...")
    identity_map: Dict[str, dict] = {}
    device_profiles_dict: Dict[str, dict] = {}

    with open(os.path.join(RAW_DIR, "identity.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row['TransactionID'].strip()
            canonical_str, dev_id, attrs = DeviceMapper.create_device_profile(
                device_info=row['DeviceInfo'],
                id_30_os=row['id_30'],
                id_31_browser=row['id_31'],
                id_33_screen=row['id_33'],
                device_type=row['DeviceType']
            )
            device_profiles_dict[dev_id] = attrs
            identity_map[tid] = {
                'device_id': dev_id,
                'canonical_profile_str': canonical_str,
                'id_15': (row['id_15'] or '').strip(),
                'id_23': (row['id_23'] or '').strip()
            }
    print(f"  Processed {len(identity_map)} identity records into {len(device_profiles_dict)} canonical DeviceProfiles.")

    # 3. Stream transactions.csv and construct normalized entities & edges
    print("\n[3/6] Streaming & Normalizing transactions.csv...")
    
    customers_data = defaultdict(lambda: {'cards': set(), 'regions': Counter(), 'first_seen': '9999', 'total_txns': 0})
    cards_data = {}
    billing_regions = Counter()
    email_domains = Counter()
    
    # Files to open for writing
    txns_out_path = os.path.join(PROCESSED_DIR, "transactions.csv")
    edges_made_path = os.path.join(PROCESSED_DIR, "edges_made.csv")
    edges_from_device_path = os.path.join(PROCESSED_DIR, "edges_from_device.csv")
    edges_billed_in_path = os.path.join(PROCESSED_DIR, "edges_billed_in.csv")
    edges_email_path = os.path.join(PROCESSED_DIR, "edges_email.csv")
    edges_next_path = os.path.join(PROCESSED_DIR, "edges_next.csv")
    
    card_txns_chrono = defaultdict(list) # card_id -> list of (ts, tid)
    
    total_txns = 0
    with open(os.path.join(RAW_DIR, "transactions.csv"), mode='r', encoding='utf-8') as fin, \
         open(txns_out_path, mode='w', encoding='utf-8', newline='') as f_txns, \
         open(edges_made_path, mode='w', encoding='utf-8', newline='') as f_made, \
         open(edges_from_device_path, mode='w', encoding='utf-8', newline='') as f_dev, \
         open(edges_billed_in_path, mode='w', encoding='utf-8', newline='') as f_billed, \
         open(edges_email_path, mode='w', encoding='utf-8', newline='') as f_email:
        
        reader = csv.DictReader(fin)
        
        # Setup writers
        w_txns = csv.writer(f_txns)
        w_txns.writerow([
            'transaction_id', 'card_id', 'customer_id', 'amount', 'ts', 'channel',
            'product_cd', 'risk_score', 'addr1', 'addr2', 'p_email', 'r_email',
            'device_id', 'id_15', 'id_23'
        ])
        
        w_made = csv.writer(f_made)
        w_made.writerow(['from_card', 'to_transaction'])
        
        w_dev = csv.writer(f_dev)
        w_dev.writerow(['from_transaction', 'to_device', 'id_15'])
        
        w_billed = csv.writer(f_billed)
        w_billed.writerow(['from_transaction', 'to_region'])
        
        w_email = csv.writer(f_email)
        w_email.writerow(['from_transaction', 'to_domain', 'role'])
        
        for row in reader:
            total_txns += 1
            tid = row['TransactionID'].strip()
            cid = row['customer_id'].strip()
            amt = float(row['TransactionAmt'])
            ts = row['ts'].strip()
            channel = row['channel'].strip()
            prod = row['ProductCD'].strip()
            risk = float(row['risk_score']) if row['risk_score'] else 0.0
            addr1 = row['addr1'].strip()
            addr2 = row['addr2'].strip()
            p_email = row['P_emaildomain'].strip()
            r_email = row['R_emaildomain'].strip()
            
            c1, c2, c3, c4, c5, c6 = (
                row['card1'].strip(), row['card2'].strip(), row['card3'].strip(),
                row['card4'].strip(), row['card5'].strip(), row['card6'].strip()
            )
            
            card_id = card_mapper.get_card_id(cid, c1, c2, c3, c4, c5, c6)
            
            # Identity linkage
            dev_id = ""
            id_15 = ""
            id_23 = ""
            if tid in identity_map:
                id_info = identity_map[tid]
                dev_id = id_info['device_id']
                id_15 = id_info['id_15']
                id_23 = id_info['id_23']
                w_dev.writerow([tid, dev_id, id_15])
                
            # Write normalized transaction row
            w_txns.writerow([
                tid, card_id, cid, amt, ts, channel, prod, risk,
                addr1, addr2, p_email, r_email, dev_id, id_15, id_23
            ])
            
            # Edges
            w_made.writerow([card_id, tid])
            if addr1:
                w_billed.writerow([tid, addr1])
                billing_regions[addr1] += 1
                if channel == 'in_person':
                    customers_data[cid]['regions'][addr1] += 1
            if p_email:
                w_email.writerow([tid, p_email, 'purchaser'])
                email_domains[p_email] += 1
            if r_email:
                w_email.writerow([tid, r_email, 'recipient'])
                email_domains[r_email] += 1
                
            # Aggregates
            customers_data[cid]['cards'].add(card_id)
            customers_data[cid]['total_txns'] += 1
            if ts < customers_data[cid]['first_seen']:
                customers_data[cid]['first_seen'] = ts
                
            if card_id not in cards_data:
                cards_data[card_id] = {
                    'card_id': card_id,
                    'customer_id': cid,
                    'card_network': c4,
                    'card_type': c6,
                    'card1': c1, 'card2': c2, 'card3': c3, 'card4': c4, 'card5': c5, 'card6': c6
                }
                
            card_txns_chrono[card_id].append((ts, tid))

    print(f"  Processed {total_txns} transactions across {len(cards_data)} cards and {len(customers_data)} customers.")

    # 4. Generate NEXT temporal edges
    print("\n[4/6] Generating NEXT temporal transaction edges...")
    next_edges_count = 0
    with open(edges_next_path, mode='w', encoding='utf-8', newline='') as f_next:
        w_next = csv.writer(f_next)
        w_next.writerow(['from_transaction', 'to_transaction', 'delta_seconds'])
        
        for card_id, txns_list in card_txns_chrono.items():
            # Sort by timestamp
            txns_list.sort(key=lambda x: (x[0], x[1]))
            for i in range(len(txns_list) - 1):
                t1_ts, t1_id = txns_list[i]
                t2_ts, t2_id = txns_list[i+1]
                # Write edge
                w_next.writerow([t1_id, t2_id, 0])
                next_edges_count += 1
    print(f"  Generated {next_edges_count} NEXT edges.")

    # 5. Write entity CSVs (customers, cards, device_profiles, billing_regions, email_domains, edges_owns)
    print("\n[5/6] Writing Entity and Relationship files...")
    
    # Customers
    with open(os.path.join(PROCESSED_DIR, "customers.csv"), mode='w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['customer_id', 'total_cards', 'first_seen', 'home_region', 'total_txns'])
        for cid, data in customers_data.items():
            home_reg = data['regions'].most_common(1)[0][0] if data['regions'] else ""
            w.writerow([cid, len(data['cards']), data['first_seen'], home_reg, data['total_txns']])
            
    # Cards
    with open(os.path.join(PROCESSED_DIR, "cards.csv"), mode='w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['card_id', 'customer_id', 'card_network', 'card_type', 'card1', 'card2', 'card3', 'card4', 'card5', 'card6'])
        for card_id, cdata in cards_data.items():
            w.writerow([
                cdata['card_id'], cdata['customer_id'], cdata['card_network'], cdata['card_type'],
                cdata['card1'], cdata['card2'], cdata['card3'], cdata['card4'], cdata['card5'], cdata['card6']
            ])

    # Edges OWNS
    with open(os.path.join(PROCESSED_DIR, "edges_owns.csv"), mode='w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['from_customer', 'to_card'])
        for card_id, cdata in cards_data.items():
            w.writerow([cdata['customer_id'], card_id])

    # Device Profiles
    with open(os.path.join(PROCESSED_DIR, "device_profiles.csv"), mode='w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['device_id', 'canonical_profile_str', 'device_info', 'os', 'browser', 'screen', 'device_type'])
        for dev_id, ddata in device_profiles_dict.items():
            w.writerow([
                dev_id, ddata['canonical_profile_str'], ddata['device_info'],
                ddata['os'], ddata['browser'], ddata['screen'], ddata['device_type']
            ])

    # Billing Regions
    with open(os.path.join(PROCESSED_DIR, "billing_regions.csv"), mode='w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['region_id', 'total_transactions'])
        for reg_id, cnt in billing_regions.items():
            w.writerow([reg_id, cnt])

    # Email Domains
    with open(os.path.join(PROCESSED_DIR, "email_domains.csv"), mode='w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['domain_name', 'total_transactions'])
        for dom, cnt in email_domains.items():
            w.writerow([dom, cnt])

    # 6. Process Historical & Benchmark Cases
    print("\n[6/6] Processing Historical Case Memory & Benchmark Pack...")
    
    # Historical Cases
    edges_case_involves_path = os.path.join(PROCESSED_DIR, "edges_case_involves.csv")
    edges_case_card_path = os.path.join(PROCESSED_DIR, "edges_case_card.csv")
    
    with open(os.path.join(RAW_DIR, "closed_cases_history.csv"), mode='r', encoding='utf-8') as fin, \
         open(os.path.join(PROCESSED_DIR, "historical_cases.csv"), mode='w', encoding='utf-8', newline='') as f_cases, \
         open(edges_case_involves_path, mode='w', encoding='utf-8', newline='') as f_cinv, \
         open(edges_case_card_path, mode='w', encoding='utf-8', newline='') as f_ccard:
        
        reader = csv.DictReader(fin)
        w_cases = csv.writer(f_cases)
        w_cases.writerow([
            'case_id', 'customer_id', 'card_id', 'opened_at', 'closed_at', 'outcome',
            'pattern', 'exposure_usd', 'report_filed', 'actions_taken', 'analyst_notes', 'txn_ids', 'connected_card_ids'
        ])
        
        w_cinv = csv.writer(f_cinv)
        w_cinv.writerow(['from_case', 'to_transaction', 'is_first_fraud'])
        
        w_ccard = csv.writer(f_ccard)
        w_ccard.writerow(['from_case', 'to_card', 'rel_type'])
        
        for row in reader:
            cid = row['case_id']
            cust = row['customer_id']
            card = row['card_id']
            first_txn = row['first_fraud_txn_id'].strip()
            
            w_cases.writerow([
                cid, cust, card, row['opened_at'], row['closed_at'], row['outcome'],
                row['pattern'], row['exposure_usd'], row['report_filed'], row['actions_taken'],
                row['analyst_notes'], row['txn_ids'], row['connected_card_ids']
            ])
            
            w_ccard.writerow([cid, card, 'on_card'])
            if row['connected_card_ids']:
                for ccard in row['connected_card_ids'].split('|'):
                    if ccard.strip():
                        w_ccard.writerow([cid, ccard.strip(), 'connected_to'])
                        
            for tid in row['txn_ids'].split('|'):
                tid = tid.strip()
                if tid:
                    w_cinv.writerow([cid, tid, 1 if tid == first_txn else 0])

    # Benchmark Cases
    with open(os.path.join(RAW_DIR, "case_pack.csv"), mode='r', encoding='utf-8') as fin, \
         open(os.path.join(PROCESSED_DIR, "benchmark_cases.csv"), mode='w', encoding='utf-8', newline='') as fout:
        reader = csv.DictReader(fin)
        w = csv.writer(fout)
        w.writerow(['case_id', 'opened_at', 'trigger_type', 'trigger_text', 'flagged_txn_id', 'card_id', 'customer_id', 'risk_score'])
        for row in reader:
            w.writerow([
                row['case_id'], row['opened_at'], row['trigger_type'], row['trigger_text'],
                row['flagged_txn_id'], row['card_id'], row['customer_id'], row['risk_score']
            ])

    print("\n=== PREPROCESSING COMPLETED SUCCESSFULLY ===")

if __name__ == '__main__':
    run_pipeline()
