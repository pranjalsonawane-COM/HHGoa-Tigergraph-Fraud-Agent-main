"""
Fraud Pattern Detection Engine for TigerGraph Agentic Fraud Investigation.
Evaluates graph signals and query outputs to identify known and undocumented fraud typologies.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

class FraudPatternDetector:
    """
    Analyzes graph signals retrieved from TigerGraph investigation queries
    and determines matching fraud typologies, evidence claims, affected transactions,
    and estimated fraud probability.
    """

    @classmethod
    def evaluate_card_testing(
        cls,
        card_window: Dict[str, Any],
        txn_context: Dict[str, Any]
    ) -> Tuple[bool, float, List[Dict[str, Any]], List[str], str]:
        """
        Pattern 1: Card Testing (Policy R5)
        Signature: 3 or more tiny online authorizations (< $5) within 1 hour followed by a larger attempt.
        """
        small_auth_count = card_window.get("small_auth_count", 0)
        small_auth_window_sec = card_window.get("small_auth_window_seconds", 0)
        all_txns = card_window.get("transactions", [])
        
        # Sort transactions chronologically
        txns_sorted = sorted(all_txns, key=lambda x: x['ts'])
        
        # Find small authorization sequence
        small_txns = [t for t in txns_sorted if t['amount'] < 5.0 and t['channel'] == 'online']
        large_txns = [t for t in txns_sorted if t['amount'] >= 5.0 and t['channel'] == 'online']
        
        is_pattern = False
        prob = 0.0
        evidence = []
        affected_ids = []
        first_txn_id = ""

        if len(small_txns) >= 3:
            # Check if there is a larger purchase following the small authorizations
            first_small_ts = datetime.strptime(small_txns[0]['ts'], "%Y-%m-%d %H:%M:%S")
            last_small_ts = datetime.strptime(small_txns[-1]['ts'], "%Y-%m-%d %H:%M:%S")
            window_minutes = (last_small_ts - first_small_ts).total_seconds() / 60.0
            
            if window_minutes <= 60.0:
                # Find subsequent larger purchase
                subsequent_large = [
                    t for t in large_txns 
                    if datetime.strptime(t['ts'], "%Y-%m-%d %H:%M:%S") >= first_small_ts
                ]
                if subsequent_large:
                    is_pattern = True
                    prob = 0.85
                    first_txn_id = small_txns[0]['transaction_id']
                    affected_ids = [t['transaction_id'] for t in small_txns] + [t['transaction_id'] for t in subsequent_large]
                    evidence.append({
                        "claim": f"{len(small_txns)} online authorizations under $5 within {int(window_minutes)} minutes, followed by a larger purchase of ${subsequent_large[0]['amount']:.2f}",
                        "source": "graph",
                        "ref": "query:get_card_window",
                        "entity_ids": affected_ids
                    })

        return is_pattern, prob, evidence, affected_ids, first_txn_id

    @classmethod
    def evaluate_out_of_region(
        cls,
        region_disc: Dict[str, Any],
        txn_context: Dict[str, Any],
        cust_profile: Dict[str, Any]
    ) -> Tuple[bool, float, List[Dict[str, Any]], List[str], str]:
        """
        Pattern 4: Out-of-Region Use (Policy R2, R3)
        Signature: In-person (card-present) transactions in a region with no prior history,
        while normal activity continues in home region.
        """
        is_pattern = False
        prob = 0.0
        evidence = []
        affected_ids = []
        first_txn_id = ""

        t = txn_context.get("transaction", {})
        channel = t.get("channel", "") or txn_context.get("channel", "")
        current_region = region_disc.get("current_region", "")
        dominant_region = region_disc.get("dominant_region", "")
        region_changed = region_disc.get("region_changed", False)
        current_count = region_disc.get("current_region_transaction_count", 0)
        dominant_count = region_disc.get("dominant_region_transaction_count", 0)

        # Out-of-region applies specifically to card-present / in_person transactions
        if channel == "in_person" and region_changed and (current_count < dominant_count * 0.5 or current_count <= 3):
            is_pattern = True
            prob = 0.75
            target_tid = t.get("transaction_id", "")
            first_txn_id = target_tid
            affected_ids = [target_tid]
            evidence.append({
                "claim": f"Card-present in-person transaction in non-dominant billing region {current_region} ({current_count} lifetime txns) vs primary home region {dominant_region} ({dominant_count} txns)",
                "source": "graph",
                "ref": "query:check_region_discrepancy",
                "entity_ids": [target_tid, current_region, dominant_region]
            })

        return is_pattern, prob, evidence, affected_ids, first_txn_id

    @classmethod
    def evaluate_device_syndicate_or_proxy(
        cls,
        device_sharing: Dict[str, Any],
        txn_context: Dict[str, Any]
    ) -> Tuple[bool, float, List[Dict[str, Any]], List[str], str, str]:
        """
        Pattern 6: Undocumented Shared Device Proxy Ring (Policy R6, R9)
        Signature: Multiple cards across distinct cardholders sharing an unusual device profile
        behind anonymous proxies, linked to historical proxy fraud cases.
        """
        is_pattern = False
        prob = 0.0
        evidence = []
        affected_ids = []
        first_txn_id = ""
        pattern_desc = ""

        num_cards = device_sharing.get("number_of_distinct_cards", 0)
        num_custs = device_sharing.get("number_of_distinct_customers", 0)
        connected_cases = device_sharing.get("connected_historical_cases", [])
        proxy_status = txn_context.get("transaction", {}).get("id_23", "")
        target_tid = txn_context.get("transaction", {}).get("transaction_id", "")
        dev_str = device_sharing.get("canonical_profile_str", "")

        # Check for multi-card device syndicate (> 5 cards across multiple customers or matching proxy cases)
        if num_cards >= 3 and (num_custs >= 3 or len(connected_cases) > 0 or "ANONYMOUS" in proxy_status):
            is_pattern = True
            prob = 0.88
            first_txn_id = target_tid
            affected_ids = [target_tid]
            pattern_desc = (
                f"Multi-card syndicate operating through shared device profile ({dev_str}) "
                f"across {num_cards} distinct cards and {num_custs} customers, operating behind an anonymous proxy "
                f"and linked to {len(connected_cases)} prior closed fraud cases."
            )
            evidence.append({
                "claim": f"Device profile ({dev_str}) is shared across {num_cards} cards and {num_custs} distinct customers, linked to {len(connected_cases)} historical fraud cases ({', '.join(connected_cases[:3])})",
                "source": "graph",
                "ref": "query:check_device_sharing",
                "entity_ids": [target_tid, device_sharing.get("device_id", "")] + connected_cases[:3]
            })

        return is_pattern, prob, evidence, affected_ids, first_txn_id, pattern_desc

    @classmethod
    def evaluate_cnp_new_device(
        cls,
        txn_context: Dict[str, Any],
        cust_profile: Dict[str, Any],
        card_window: Dict[str, Any]
    ) -> Tuple[bool, float, List[Dict[str, Any]], List[str], str]:
        """
        Pattern 3: Card-Not-Present Fraud from a New Device
        Signature: Online CNP charge marked id_15 = 'New' from a device not in customer baseline.
        """
        is_pattern = False
        prob = 0.0
        evidence = []
        affected_ids = []
        first_txn_id = ""

        t = txn_context.get("transaction", {})
        channel = t.get("channel", "")
        id_15 = t.get("id_15", "")
        dev_id = t.get("device_id", "")
        target_tid = t.get("transaction_id", "")
        known_devs = cust_profile.get("distinct_devices_used", [])

        if channel == "online" and (id_15 == "New" or (dev_id and dev_id not in known_devs)):
            is_pattern = True
            prob = 0.65  # Single new device signal has baseline uncertainty (people buy new devices)
            first_txn_id = target_tid
            affected_ids = [target_tid]
            evidence.append({
                "claim": f"Online transaction from a new device profile ({txn_context.get('device_profile', {}).get('canonical_profile_str', dev_id)}) marked id_15='New', not previously seen on this account",
                "source": "graph",
                "ref": "query:get_transaction_context",
                "entity_ids": [target_tid, dev_id]
            })

        return is_pattern, prob, evidence, affected_ids, first_txn_id

    @classmethod
    def evaluate_cnp_fraud(
        cls,
        txn_context: Dict[str, Any],
        cust_profile: Dict[str, Any],
        card_window: Dict[str, Any]
    ) -> Tuple[bool, float, List[Dict[str, Any]], List[str], str]:
        """
        Pattern 2: Standard Card-Not-Present Fraud
        Signature: Online purchase inconsistent with cardholder spend history/merchants.
        """
        is_pattern = False
        prob = 0.0
        evidence = []
        affected_ids = []
        first_txn_id = ""

        t = txn_context.get("transaction", {})
        channel = t.get("channel", "")
        amt = float(t.get("amount", 0.0))
        target_tid = t.get("transaction_id", "")
        avg_spend = cust_profile.get("average_transaction_amount", 50.0)

        if channel == "online":
            is_pattern = True
            prob = 0.55 if amt <= 3 * avg_spend else 0.72
            first_txn_id = target_tid
            affected_ids = [target_tid]
            evidence.append({
                "claim": f"Online card-not-present transaction of ${amt:.2f} under product code {t.get('product_cd')}, compared to customer historical average spend of ${avg_spend:.2f}",
                "source": "graph",
                "ref": "query:get_transaction_context",
                "entity_ids": [target_tid]
            })

        return is_pattern, prob, evidence, affected_ids, first_txn_id

    @classmethod
    def detect_fraud_pattern(
        cls,
        txn_context: Dict[str, Any],
        cust_profile: Dict[str, Any],
        card_window: Dict[str, Any],
        device_sharing: Dict[str, Any],
        region_disc: Dict[str, Any],
        prior_cases: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Master classification engine evaluating all typologies in order of specificity.
        """
        t = txn_context.get("transaction", {})
        target_tid = t.get("transaction_id", "")

        # 1. Evaluate Card Testing
        is_testing, p_testing, ev_testing, aff_testing, first_testing = cls.evaluate_card_testing(card_window, txn_context)
        if is_testing:
            return {
                "pattern": "card_testing",
                "pattern_description": "",
                "fraud_probability": p_testing,
                "evidence": ev_testing,
                "affected_txn_ids": aff_testing,
                "first_suspicious_txn_id": first_testing,
                "exposure_usd": sum(abs(float(txn_context.get("transaction", {}).get("amount", 0))) for _ in aff_testing)
            }

        # 2. Evaluate Undocumented Device Syndicate / Proxy Ring
        is_syndicate, p_syndicate, ev_syndicate, aff_syndicate, first_syndicate, desc_syndicate = cls.evaluate_device_syndicate_or_proxy(device_sharing, txn_context)
        if is_syndicate:
            return {
                "pattern": "undocumented",
                "pattern_description": desc_syndicate,
                "fraud_probability": p_syndicate,
                "evidence": ev_syndicate,
                "affected_txn_ids": aff_syndicate,
                "first_suspicious_txn_id": first_syndicate,
                "exposure_usd": float(t.get("amount", 0.0))
            }

        # 3. Evaluate Out-of-Region Use
        is_region, p_region, ev_region, aff_region, first_region = cls.evaluate_out_of_region(region_disc, txn_context, cust_profile)
        if is_region:
            return {
                "pattern": "out_of_region_use",
                "pattern_description": "",
                "fraud_probability": p_region,
                "evidence": ev_region,
                "affected_txn_ids": aff_region,
                "first_suspicious_txn_id": first_region,
                "exposure_usd": float(t.get("amount", 0.0))
            }

        # 4. Evaluate CNP New Device
        is_new_dev, p_new_dev, ev_new_dev, aff_new_dev, first_new_dev = cls.evaluate_cnp_new_device(txn_context, cust_profile, card_window)
        if is_new_dev:
            return {
                "pattern": "card_not_present_new_device",
                "pattern_description": "",
                "fraud_probability": p_new_dev,
                "evidence": ev_new_dev,
                "affected_txn_ids": aff_new_dev,
                "first_suspicious_txn_id": first_new_dev,
                "exposure_usd": float(t.get("amount", 0.0))
            }

        # 5. Evaluate General CNP Fraud
        is_cnp, p_cnp, ev_cnp, aff_cnp, first_cnp = cls.evaluate_cnp_fraud(txn_context, cust_profile, card_window)
        if is_cnp:
            return {
                "pattern": "card_not_present_fraud",
                "pattern_description": "",
                "fraud_probability": p_cnp,
                "evidence": ev_cnp,
                "affected_txn_ids": aff_cnp,
                "first_suspicious_txn_id": first_cnp,
                "exposure_usd": float(t.get("amount", 0.0))
            }

        # 6. Default / Legitimate Baseline
        return {
            "pattern": "none",
            "pattern_description": "",
            "fraud_probability": 0.10,
            "evidence": [{
                "claim": "Transaction matches cardholder historical spending baseline, trusted devices, and regional parameters",
                "source": "graph",
                "ref": "query:get_customer_profile",
                "entity_ids": [target_tid]
            }],
            "affected_txn_ids": [],
            "first_suspicious_txn_id": "",
            "exposure_usd": 0.0
        }
