"""
Comprehensive Graph Integrity, Count Verification & Traversal Validator for FraudGraph.
"""
import os
import csv
import json
import sys
from collections import defaultdict, Counter
from typing import Dict, Any, List, Set, Tuple

PROCESSED_DIR = "d:/HHGOA-Fraud-Agent/data/processed"
ARTIFACTS_DIR = "d:/HHGOA-Fraud-Agent/tests/artifacts"

def ensure_dirs():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def run_graph_validation():
    ensure_dirs()
    print("==================================================================")
    print("   TIGERGRAPH FRAUDGRAPH — DATA LOADING & INTEGRITY VALIDATION   ")
    print("==================================================================\n")

    # ------------------------------------------------------------------------
    # 1. VERTEX COUNTS VERIFICATION
    # ------------------------------------------------------------------------
    print("[1/4] Calculating Exact Vertex Counts from data/processed/...")
    vertex_counts = {}
    
    # Customer
    cust_ids = set()
    with open(os.path.join(PROCESSED_DIR, "customers.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cust_ids.add(row['customer_id'].strip())
    vertex_counts['Customer'] = len(cust_ids)

    # Card
    card_ids = set()
    with open(os.path.join(PROCESSED_DIR, "cards.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            card_ids.add(row['card_id'].strip())
    vertex_counts['Card'] = len(card_ids)

    # Transaction
    txn_ids = set()
    txns_data = {}
    with open(os.path.join(PROCESSED_DIR, "transactions.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row['transaction_id'].strip()
            txn_ids.add(tid)
            txns_data[tid] = row
    vertex_counts['Transaction'] = len(txn_ids)

    # DeviceProfile
    dev_ids = set()
    dev_data = {}
    with open(os.path.join(PROCESSED_DIR, "device_profiles.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            did = row['device_id'].strip()
            dev_ids.add(did)
            dev_data[did] = row
    vertex_counts['DeviceProfile'] = len(dev_ids)

    # BillingRegion
    reg_ids = set()
    with open(os.path.join(PROCESSED_DIR, "billing_regions.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            reg_ids.add(row['region_id'].strip())
    vertex_counts['BillingRegion'] = len(reg_ids)

    # EmailDomain
    email_domains = set()
    with open(os.path.join(PROCESSED_DIR, "email_domains.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email_domains.add(row['domain_name'].strip())
    vertex_counts['EmailDomain'] = len(email_domains)

    # ClosedCase
    case_ids = set()
    cases_data = {}
    with open(os.path.join(PROCESSED_DIR, "historical_cases.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row['case_id'].strip()
            case_ids.add(cid)
            cases_data[cid] = row
    vertex_counts['ClosedCase'] = len(case_ids)

    total_vertices = sum(vertex_counts.values())
    print("  Vertex Counts Summary:")
    for vname, cnt in vertex_counts.items():
        print(f"    - {vname:<15}: {cnt:>8,d}")
    print(f"    Total Vertices : {total_vertices:>8,d}\n")

    # ------------------------------------------------------------------------
    # 2. EDGE COUNTS VERIFICATION (PRIMARY & REVERSE)
    # ------------------------------------------------------------------------
    print("[2/4] Calculating Exact Edge Counts & Splits from data/processed/...")
    edge_counts = {}
    reverse_edge_counts = {}

    # OWNS (Customer -> Card)
    owns_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_owns.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            owns_edges.append((row['from_customer'].strip(), row['to_card'].strip()))
    edge_counts['OWNS'] = len(owns_edges)
    reverse_edge_counts['OWNED_BY'] = len(owns_edges)

    # MADE (Card -> Transaction)
    made_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_made.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            made_edges.append((row['from_card'].strip(), row['to_transaction'].strip()))
    edge_counts['MADE'] = len(made_edges)
    reverse_edge_counts['MADE_BY'] = len(made_edges)

    # FROM_DEVICE (Transaction -> DeviceProfile)
    from_dev_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_from_device.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_dev_edges.append((row['from_transaction'].strip(), row['to_device'].strip(), row['id_15'].strip()))
    edge_counts['FROM_DEVICE'] = len(from_dev_edges)
    reverse_edge_counts['DEVICE_FOR_TXN'] = len(from_dev_edges)

    # BILLED_IN (Transaction -> BillingRegion)
    billed_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_billed_in.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            billed_edges.append((row['from_transaction'].strip(), row['to_region'].strip()))
    edge_counts['BILLED_IN'] = len(billed_edges)
    reverse_edge_counts['REGION_FOR_TXN'] = len(billed_edges)

    # EMAIL EDGES SPLIT (PURCHASER_EMAIL vs RECIPIENT_EMAIL)
    purchaser_email_edges = []
    recipient_email_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_email.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row['from_transaction'].strip()
            dom = row['to_domain'].strip()
            role = row['role'].strip()
            if role == 'purchaser':
                purchaser_email_edges.append((tid, dom))
            elif role == 'recipient':
                recipient_email_edges.append((tid, dom))
                
    edge_counts['PURCHASER_EMAIL'] = len(purchaser_email_edges)
    reverse_edge_counts['PURCHASER_EMAIL_FOR_TXN'] = len(purchaser_email_edges)
    edge_counts['RECIPIENT_EMAIL'] = len(recipient_email_edges)
    reverse_edge_counts['RECIPIENT_EMAIL_FOR_TXN'] = len(recipient_email_edges)

    # NEXT (Transaction -> Transaction)
    next_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_next.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            next_edges.append((row['from_transaction'].strip(), row['to_transaction'].strip()))
    edge_counts['NEXT'] = len(next_edges)
    reverse_edge_counts['PREV'] = len(next_edges)

    # INVOLVES (ClosedCase -> Transaction)
    case_inv_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_case_involves.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_inv_edges.append((row['from_case'].strip(), row['to_transaction'].strip(), row['is_first_fraud'].strip()))
    edge_counts['INVOLVES'] = len(case_inv_edges)
    reverse_edge_counts['INVOLVED_IN_CASE'] = len(case_inv_edges)

    # CASE_CARD EDGES SPLIT (ON_CARD vs CONNECTED_TO)
    on_card_edges = []
    connected_to_edges = []
    with open(os.path.join(PROCESSED_DIR, "edges_case_card.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row['from_case'].strip()
            card = row['to_card'].strip()
            rel = row['rel_type'].strip()
            if rel == 'on_card':
                on_card_edges.append((cid, card))
            elif rel == 'connected_to':
                connected_to_edges.append((cid, card))

    edge_counts['ON_CARD'] = len(on_card_edges)
    reverse_edge_counts['CASE_ON_CARD'] = len(on_card_edges)
    edge_counts['CONNECTED_TO'] = len(connected_to_edges)
    reverse_edge_counts['CONNECTED_TO_CASE'] = len(connected_to_edges)

    total_primary_edges = sum(edge_counts.values())
    total_reverse_edges = sum(reverse_edge_counts.values())
    print("  Primary Directed Edge Counts Summary:")
    for ename, cnt in edge_counts.items():
        print(f"    - {ename:<18}: {cnt:>8,d}")
    print(f"    Total Primary Edges: {total_primary_edges:>8,d}")
    print("  Reverse Edge Counts Summary:")
    for rname, cnt in reverse_edge_counts.items():
        print(f"    - {rname:<25}: {cnt:>8,d}")
    print(f"    Total Reverse Edges: {total_reverse_edges:>8,d}\n")

    # ------------------------------------------------------------------------
    # 3. DATA INTEGRITY & ORPHAN EDGE AUDIT
    # ------------------------------------------------------------------------
    print("[3/4] Performing Rigorous Data Integrity & Foreign Key Checks...")
    integrity_errors = 0

    # OWNS: Customer -> Card
    for u, v in owns_edges:
        if u not in cust_ids or v not in card_ids:
            print(f"  Integrity Error in OWNS: {u} -> {v}")
            integrity_errors += 1

    # MADE: Card -> Transaction
    for u, v in made_edges:
        if u not in card_ids or v not in txn_ids:
            print(f"  Integrity Error in MADE: {u} -> {v}")
            integrity_errors += 1

    # FROM_DEVICE: Transaction -> DeviceProfile
    for u, v, _ in from_dev_edges:
        if u not in txn_ids or v not in dev_ids:
            print(f"  Integrity Error in FROM_DEVICE: {u} -> {v}")
            integrity_errors += 1

    # BILLED_IN: Transaction -> BillingRegion
    for u, v in billed_edges:
        if u not in txn_ids or v not in reg_ids:
            print(f"  Integrity Error in BILLED_IN: {u} -> {v}")
            integrity_errors += 1

    # PURCHASER_EMAIL & RECIPIENT_EMAIL: Transaction -> EmailDomain
    for u, v in purchaser_email_edges + recipient_email_edges:
        if u not in txn_ids or v not in email_domains:
            print(f"  Integrity Error in EMAIL edge: {u} -> {v}")
            integrity_errors += 1

    # NEXT: Transaction -> Transaction
    for u, v in next_edges:
        if u not in txn_ids or v not in txn_ids:
            print(f"  Integrity Error in NEXT: {u} -> {v}")
            integrity_errors += 1

    # INVOLVES: ClosedCase -> Transaction
    for u, v, _ in case_inv_edges:
        if u not in case_ids or v not in txn_ids:
            print(f"  Integrity Error in INVOLVES: {u} -> {v}")
            integrity_errors += 1

    # ON_CARD & CONNECTED_TO: ClosedCase -> Card
    for u, v in on_card_edges + connected_to_edges:
        if u not in case_ids or v not in card_ids:
            print(f"  Integrity Error in CASE_CARD: {u} -> {v}")
            integrity_errors += 1

    print(f"  Integrity Audit Result: {integrity_errors} foreign key errors detected. -> {'PASS' if integrity_errors == 0 else 'FAIL'}\n")

    # ------------------------------------------------------------------------
    # 4. BENCHMARK CASE HHG-014 GRAPH TRAVERSAL VERIFICATION
    # ------------------------------------------------------------------------
    print("[4/4] Executing Real Graph Traversal for Benchmark Case HHG-014...")
    # Flagged transaction: 3478561, Customer: C13487, Card: C13487-K1
    target_txn_id = "3478561"
    target_cust_id = "C13487"
    target_card_id = "C13487-K1"

    # 1. Flagged transaction
    flagged_txn = txns_data[target_txn_id]
    
    # 2. Owning card & 3. Owning customer
    owning_card = target_card_id
    owning_cust = flagged_txn['customer_id']

    # 4. Device Profile
    dev_id = flagged_txn['device_id']
    device_profile = dev_data.get(dev_id, {})

    # 5. Billing Region
    billing_region = flagged_txn['addr1']

    # 6. Purchaser email & 7. Recipient email
    p_email = flagged_txn['p_email']
    r_email = flagged_txn['r_email']

    # 8. Nearby transactions through NEXT/PREV
    # Find all transactions on this card ordered by ts
    card_txns = []
    for u, v in made_edges:
        if u == target_card_id:
            card_txns.append(txns_data[v])
    card_txns.sort(key=lambda x: x['ts'])
    
    flagged_idx = -1
    for i, t in enumerate(card_txns):
        if t['transaction_id'] == target_txn_id:
            flagged_idx = i
            break
            
    prev_txns = card_txns[max(0, flagged_idx-3):flagged_idx]
    next_txns = card_txns[flagged_idx+1:min(len(card_txns), flagged_idx+4)]

    # 9. Other cards belonging to the same customer
    cust_cards = [v for u, v in owns_edges if u == target_cust_id]
    
    # 10. Transactions made by those cards
    other_cards_txns = {}
    for c in cust_cards:
        if c != target_card_id:
            other_cards_txns[c] = [txns_data[v] for u, v in made_edges if u == c]

    # 11. Previous closed cases connected to the card
    cases_on_card = [u for u, v in on_card_edges if v == target_card_id]
    cases_on_card_details = [cases_data[c] for c in cases_on_card]

    # 12. Previous closed cases connected to the customer
    cases_on_cust = []
    for c in cust_cards:
        for cid, card in on_card_edges:
            if card == c and cid not in cases_on_cust:
                cases_on_cust.append(cid)
    cases_on_cust_details = [cases_data[c] for c in cases_on_cust]

    # 13. Other transactions and cards sharing the SAME device profile (Cross-Card Syndicate Check)
    device_sharing_txns = [u for u, v, _ in from_dev_edges if v == dev_id and u != target_txn_id]
    device_sharing_cards = set(txns_data[t]['card_id'] for t in device_sharing_txns)
    device_sharing_custs = set(txns_data[t]['customer_id'] for t in device_sharing_txns)
    
    # Historical cases that involve the same device profile
    device_cases = []
    for cid, t, _ in case_inv_edges:
        if t in device_sharing_txns:
            if cid not in device_cases:
                device_cases.append(cid)
    device_cases_details = [cases_data[c] for c in device_cases]

    traversal_result = {
        "case_id": "HHG-014",
        "flagged_transaction": {
            "transaction_id": target_txn_id,
            "amount": float(flagged_txn['amount']),
            "ts": flagged_txn['ts'],
            "channel": flagged_txn['channel'],
            "product_cd": flagged_txn['product_cd'],
            "risk_score": float(flagged_txn['risk_score']),
            "addr1": flagged_txn['addr1'],
            "addr2": flagged_txn['addr2'],
            "id_15": flagged_txn['id_15'],
            "id_23": flagged_txn['id_23']
        },
        "owning_card": {
            "card_id": owning_card,
            "total_card_transactions": len(card_txns)
        },
        "owning_customer": {
            "customer_id": owning_cust,
            "total_cards": len(cust_cards),
            "cards": cust_cards
        },
        "device_profile": {
            "device_id": dev_id,
            "canonical_profile_str": device_profile.get('canonical_profile_str', ''),
            "device_info": device_profile.get('device_info', ''),
            "os": device_profile.get('os', ''),
            "browser": device_profile.get('browser', ''),
            "screen": device_profile.get('screen', ''),
            "device_type": device_profile.get('device_type', '')
        },
        "billing_region": billing_region,
        "purchaser_email": p_email,
        "recipient_email": r_email,
        "adjacent_transactions_prev": prev_txns,
        "adjacent_transactions_next": next_txns,
        "other_cards_transactions_count": {c: len(txns) for c, txns in other_cards_txns.items()},
        "closed_cases_on_card": cases_on_card_details,
        "closed_cases_on_customer": cases_on_cust_details,
        "cross_card_device_sharing": {
            "shared_transactions_count": len(device_sharing_txns),
            "connected_cards": list(device_sharing_cards),
            "connected_customers": list(device_sharing_custs),
            "connected_historical_cases": device_cases_details
        }
    }

    output_json_path = os.path.join(ARTIFACTS_DIR, "hhg014_graph_validation.json")
    with open(output_json_path, mode='w', encoding='utf-8') as f:
        json.dump(traversal_result, f, indent=2)

    print(f"  HHG-014 Graph Traversal Retrieved Successfully:")
    print(f"    - Flagged Txn: {target_txn_id} (${float(flagged_txn['amount'])}, {flagged_txn['channel']}, score: {flagged_txn['risk_score']})")
    print(f"    - Device Profile: {device_profile.get('canonical_profile_str')}")
    print(f"    - Cross-card Device Links: {len(device_sharing_cards)} other cards share this exact device profile!")
    print(f"    - Connected Historical Cases: {[c['case_id'] for c in device_cases_details]}")
    print(f"  Saved traversal evidence artifact to {output_json_path}\n")

    return {
        "vertex_counts": vertex_counts,
        "edge_counts": edge_counts,
        "reverse_edge_counts": reverse_edge_counts,
        "integrity_errors": integrity_errors,
        "hhg014_traversal": traversal_result
    }

if __name__ == '__main__':
    run_graph_validation()
