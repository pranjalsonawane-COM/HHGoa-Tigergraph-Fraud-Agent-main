"""
Comprehensive Validation Script for Phase 1 Preprocessing.
Executes Checks A through H and generates a full validation audit.
"""
import os
import csv
import sys
from collections import Counter, defaultdict

PROCESSED_DIR = "d:/HHGOA-Fraud-Agent/data/processed"
RAW_DIR = "d:/HHGOA-Fraud-Agent"

def run_validation():
    print("=========================================================")
    print("   TIGERGRAPH FRAUD INVESTIGATION — PIPELINE VALIDATION   ")
    print("=========================================================\n")

    results = {}

    # Check A: TransactionID Uniqueness & Consistency
    print("[Check A] Validating TransactionID Uniqueness & Consistency...")
    txn_ids = set()
    dup_txns = 0
    total_txns = 0
    with open(os.path.join(PROCESSED_DIR, "transactions.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_txns += 1
            tid = row['transaction_id']
            if tid in txn_ids:
                dup_txns += 1
            txn_ids.add(tid)
    results['check_a'] = {
        'total_txns': total_txns,
        'unique_txns': len(txn_ids),
        'duplicates': dup_txns,
        'passed': (dup_txns == 0 and total_txns == 590742)
    }
    print(f"  Total Transactions: {total_txns}, Unique: {len(txn_ids)}, Duplicates: {dup_txns} -> {'PASS' if results['check_a']['passed'] else 'FAIL'}")

    # Check B: Benchmark Transaction Existence & Match
    print("\n[Check B] Validating 20 Benchmark Cases Resolution...")
    benchmark_cases = []
    with open(os.path.join(RAW_DIR, "case_pack.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            benchmark_cases.append(row)
            
    txn_lookup = {}
    with open(os.path.join(PROCESSED_DIR, "transactions.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row['transaction_id']
            if tid in [b['flagged_txn_id'] for b in benchmark_cases]:
                txn_lookup[tid] = row

    b_matches = 0
    b_mismatches = 0
    case_details = []
    for b in benchmark_cases:
        cid = b['case_id']
        tid = b['flagged_txn_id']
        exp_cust = b['customer_id']
        exp_card = b['card_id']
        
        if tid in txn_lookup:
            t = txn_lookup[tid]
            gen_cust = t['customer_id']
            gen_card = t['card_id']
            match = (gen_cust == exp_cust and gen_card == exp_card)
            if match:
                b_matches += 1
            else:
                b_mismatches += 1
            case_details.append({
                'case_id': cid, 'txn_id': tid, 'exp_cust': exp_cust, 'gen_cust': gen_cust,
                'exp_card': exp_card, 'gen_card': gen_card, 'matched': match
            })
        else:
            b_mismatches += 1
            case_details.append({
                'case_id': cid, 'txn_id': tid, 'exp_cust': exp_cust, 'gen_cust': 'MISSING',
                'exp_card': exp_card, 'gen_card': 'MISSING', 'matched': False
            })

    results['check_b'] = {
        'total_cases': len(benchmark_cases),
        'matched': b_matches,
        'mismatches': b_mismatches,
        'passed': (b_matches == 20 and b_mismatches == 0),
        'details': case_details
    }
    print(f"  Benchmark Cases: {len(benchmark_cases)}, Matched: {b_matches}, Mismatches: {b_mismatches} -> {'PASS' if results['check_b']['passed'] else 'FAIL'}")

    # Check C: Customer ID Consistency
    print("\n[Check C] Validating Customer Entity Consistency...")
    cust_ids = set()
    with open(os.path.join(PROCESSED_DIR, "customers.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cust_ids.add(row['customer_id'])
    results['check_c'] = {
        'total_customers': len(cust_ids),
        'passed': (len(cust_ids) == 13553)
    }
    print(f"  Total Unique Customers: {len(cust_ids)} -> {'PASS' if results['check_c']['passed'] else 'FAIL'}")

    # Check D: Card ID Mapping & Cardinality
    print("\n[Check D] Validating Card Entity Consistency...")
    card_ids = set()
    with open(os.path.join(PROCESSED_DIR, "cards.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            card_ids.add(row['card_id'])
    results['check_d'] = {
        'total_cards': len(card_ids),
        'passed': (len(card_ids) >= 13553)
    }
    print(f"  Total Unique Cards: {len(card_ids)} -> {'PASS' if results['check_d']['passed'] else 'FAIL'}")

    # Check E: Identity-to-Transaction Joins
    print("\n[Check E] Validating Identity Joins & Channel Consistency...")
    id_txns = set()
    with open(os.path.join(RAW_DIR, "identity.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_txns.add(row['TransactionID'])

    online_txns_with_device = 0
    in_person_txns_with_device = 0
    with open(os.path.join(PROCESSED_DIR, "transactions.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row['transaction_id']
            dev_id = row['device_id']
            chan = row['channel']
            if dev_id:
                if chan == 'online':
                    online_txns_with_device += 1
                else:
                    in_person_txns_with_device += 1

    results['check_e'] = {
        'raw_identity_records': len(id_txns),
        'online_txns_with_device': online_txns_with_device,
        'in_person_txns_with_device': in_person_txns_with_device,
        'passed': (online_txns_with_device == len(id_txns) and in_person_txns_with_device == 0)
    }
    print(f"  Identity Records: {len(id_txns)}, Online Joined: {online_txns_with_device}, In-Person Joined: {in_person_txns_with_device} -> {'PASS' if results['check_e']['passed'] else 'FAIL'}")

    # Check F: DeviceProfile Generation
    print("\n[Check F] Validating DeviceProfile Entity Generation...")
    dev_ids = set()
    with open(os.path.join(PROCESSED_DIR, "device_profiles.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dev_ids.add(row['device_id'])
    results['check_f'] = {
        'total_device_profiles': len(dev_ids),
        'passed': (len(dev_ids) > 9000)
    }
    print(f"  Canonical Device Profiles: {len(dev_ids)} -> {'PASS' if results['check_f']['passed'] else 'FAIL'}")

    # Check G: Historical Case Transaction References
    print("\n[Check G] Validating Historical Case Transactions Integrity...")
    hist_txns = 0
    missing_hist_txns = 0
    with open(os.path.join(RAW_DIR, "closed_cases_history.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for tid in row['txn_ids'].split('|'):
                tid = tid.strip()
                if tid:
                    hist_txns += 1
                    if tid not in txn_ids:
                        missing_hist_txns += 1

    results['check_g'] = {
        'total_hist_case_txns': hist_txns,
        'missing_hist_txns': missing_hist_txns,
        'passed': (missing_hist_txns == 0 and hist_txns == 14955)
    }
    print(f"  Historical Case Txns Checked: {hist_txns}, Missing: {missing_hist_txns} -> {'PASS' if results['check_g']['passed'] else 'FAIL'}")

    # Check H: Temporal Partition & Leakage Isolation
    print("\n[Check H] Validating Temporal Boundary & Leakage Isolation...")
    # Check max date of historical cases vs min date of benchmark cases
    max_hist_date = "0000"
    with open(os.path.join(PROCESSED_DIR, "historical_cases.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['closed_at'] > max_hist_date:
                max_hist_date = row['closed_at']

    min_bench_date = "9999"
    with open(os.path.join(PROCESSED_DIR, "benchmark_cases.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['opened_at'] < min_bench_date:
                min_bench_date = row['opened_at']

    leakage_passed = (max_hist_date < min_bench_date)
    results['check_h'] = {
        'max_historical_closed_at': max_hist_date,
        'min_benchmark_opened_at': min_bench_date,
        'passed': leakage_passed
    }
    print(f"  Max Historical Closed Date: {max_hist_date}, Min Benchmark Opened Date: {min_bench_date} -> {'PASS' if leakage_passed else 'FAIL'}")

    print("\n=========================================================")
    all_passed = all(r['passed'] for r in results.values())
    print(f"   OVERALL PIPELINE VALIDATION: {'ALL CHECKS PASSED (100%)' if all_passed else 'SOME CHECKS FAILED'}")
    print("=========================================================\n")
    return results

if __name__ == '__main__':
    run_validation()
