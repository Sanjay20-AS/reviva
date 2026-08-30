"""
Synthetic Payment Degradation Event Generator
-----------------------------------------------
Generates a reproducible batch of payment events with planted "degradation"
patterns for a root-cause diagnosis + recovery agent.

Usage:
    python generate_payment_events.py --n 150 --seed 42 --out events.json
"""

import argparse
import json
import random
from datetime import datetime, timedelta


CARD_NETWORKS = ["Visa", "Mastercard", "RuPay", "Amex"]
BANKS = ["HDFC Bank", "ICICI Bank", "SBI", "Axis Bank", "Kotak Bank", "Yes Bank"]
PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]

# Error codes loosely styled after common gateway/bank decline codes.
# Not claiming to be exact Razorpay codes -- illustrative for the demo.
ERROR_CODES = {
    "issuer_decline": ["BANK_DECLINE_05", "BANK_DECLINE_51"],
    "network_timeout": ["GATEWAY_TIMEOUT", "NO_RESPONSE"],
    "expired_instrument": ["EXPIRED_CARD", "INVALID_UPI_HANDLE"],
    "insufficient_funds": ["INSUFFICIENT_FUNDS"],
    "acquirer_outage": ["ACQUIRER_UNAVAILABLE", "GATEWAY_5XX"],
    "fraud_hold": ["RISK_HOLD_61", "VELOCITY_LIMIT_EXCEEDED"],
}


def random_timestamp(base, spread_hours=72):
    return base + timedelta(minutes=random.randint(0, spread_hours * 60))


def make_instrument(method, expired=False):
    if method == "card":
        network = random.choice(CARD_NETWORKS)
        if expired:
            expiry = (datetime.now() - timedelta(days=random.randint(10, 400))).strftime("%m/%y")
        else:
            expiry = (datetime.now() + timedelta(days=random.randint(30, 900))).strftime("%m/%y")
        return {"card_network": network, "card_expiry": expiry}
    elif method == "upi":
        handle = f"user{random.randint(1000,9999)}@{random.choice(['okhdfcbank','okicici','oksbi','okaxis'])}"
        return {"upi_handle": handle, "valid": not expired}
    elif method == "netbanking":
        return {"bank_name": random.choice(BANKS)}
    else:  # wallet
        return {"wallet_provider": random.choice(["Paytm", "PhonePe Wallet", "AmazonPay"])}


def base_event(event_id, ts, merchant_id="MERCH_001"):
    method = random.choice(PAYMENT_METHODS)
    return {
        "event_id": f"evt_{event_id:05d}",
        "timestamp": ts.isoformat(),
        "merchant_id": merchant_id,
        "customer_id": f"cust_{random.randint(1000,4999)}",
        "amount": round(random.uniform(199, 24999), 2),
        "payment_method": method,
        "instrument_details": make_instrument(method),
        "retry_count": 0,
        "latency_ms": random.randint(200, 900),
        "acquirer_bank": random.choice(BANKS),
        "status": "degraded",
        "error_code": None,
        "degradation_type": None,  # ground truth label, not shown to the diagnosis engine
    }


def apply_issuer_decline(evt):
    evt["degradation_type"] = "issuer_decline"
    evt["error_code"] = random.choice(ERROR_CODES["issuer_decline"])
    evt["latency_ms"] = random.randint(200, 600)
    evt["retry_count"] = 0
    return evt


def apply_network_timeout(evt):
    evt["degradation_type"] = "network_timeout"
    evt["error_code"] = random.choice(ERROR_CODES["network_timeout"])
    evt["latency_ms"] = random.randint(4000, 9000)
    evt["retry_count"] = 0
    return evt


def apply_expired_instrument(evt):
    evt["degradation_type"] = "expired_instrument"
    evt["error_code"] = random.choice(ERROR_CODES["expired_instrument"])
    evt["instrument_details"] = make_instrument(evt["payment_method"], expired=True)
    evt["retry_count"] = random.randint(1, 3)  # fails consistently across retries
    return evt


def apply_insufficient_funds(evt):
    evt["degradation_type"] = "insufficient_funds"
    evt["error_code"] = random.choice(ERROR_CODES["insufficient_funds"])
    evt["retry_count"] = random.randint(0, 2)
    evt["amount"] = round(random.uniform(5000, 24999), 2)  # skews higher amounts
    return evt


def apply_fraud_hold(evt):
    evt["degradation_type"] = "fraud_hold"
    evt["error_code"] = random.choice(ERROR_CODES["fraud_hold"])
    evt["latency_ms"] = random.randint(200, 500)
    return evt


def apply_noise(evt):
    """Ambiguous event with mixed/weak signals - for honest exception reporting."""
    evt["degradation_type"] = "ambiguous"
    evt["error_code"] = random.choice(sum(ERROR_CODES.values(), []))
    evt["latency_ms"] = random.randint(500, 3000)
    evt["retry_count"] = random.randint(0, 1)
    return evt


def generate_acquirer_outage_cluster(start_id, base_ts, bank, cluster_size):
    """Multiple events, same acquirer_bank, tight time window -> requires
    cross-event reasoning to detect, unlike the single-event categories above."""
    window_start = random_timestamp(base_ts, spread_hours=48)
    cluster = []
    for i in range(cluster_size):
        evt = base_event(start_id + i, window_start + timedelta(minutes=random.randint(0, 8)))
        evt["acquirer_bank"] = bank
        evt["degradation_type"] = "acquirer_outage"
        evt["error_code"] = random.choice(ERROR_CODES["acquirer_outage"])
        evt["latency_ms"] = random.randint(1500, 4000)
        cluster.append(evt)
    return cluster


def generate_dataset(n, seed):
    random.seed(seed)
    base_ts = datetime(2026, 8, 1, 9, 0, 0)

    events = []
    event_id = 1

    # Reserve ~15% of n for one or two acquirer-outage clusters
    cluster_budget = max(6, int(n * 0.15))
    n_remaining = n - cluster_budget

    # Single-event categories, roughly evenly weighted, with a noise slice
    weighted_categories = (
        [apply_issuer_decline] * 22
        + [apply_network_timeout] * 18
        + [apply_expired_instrument] * 20
        + [apply_insufficient_funds] * 18
        + [apply_fraud_hold] * 12
        + [apply_noise] * 10
    )

    for _ in range(n_remaining):
        ts = random_timestamp(base_ts)
        evt = base_event(event_id, ts)
        fn = random.choice(weighted_categories)
        evt = fn(evt)
        events.append(evt)
        event_id += 1

    # Add 1-2 acquirer outage clusters
    n_clusters = 1 if cluster_budget < 12 else 2
    per_cluster = cluster_budget // n_clusters
    for c in range(n_clusters):
        bank = random.choice(BANKS)
        cluster = generate_acquirer_outage_cluster(event_id, base_ts, bank, per_cluster)
        events.extend(cluster)
        event_id += per_cluster

    random.shuffle(events)
    # Re-sort by timestamp for a realistic stream order
    events.sort(key=lambda e: e["timestamp"])
    return events


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic payment degradation events.")
    parser.add_argument("--n", type=int, default=150, help="Number of events to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--out", type=str, default="events.json", help="Output JSON file path")
    args = parser.parse_args()

    events = generate_dataset(args.n, args.seed)

    with open(args.out, "w") as f:
        json.dump(events, f, indent=2)

    # Quick summary printed to console
    counts = {}
    for e in events:
        counts[e["degradation_type"]] = counts.get(e["degradation_type"], 0) + 1

    print(f"Generated {len(events)} events -> {args.out}")
    print("Category breakdown:")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
