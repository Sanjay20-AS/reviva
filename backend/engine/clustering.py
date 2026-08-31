"""
Clustering Engine — Layer 2 (cross-event acquirer-outage detection)
----------------------------------------------------------------------
A single degraded payment routed through a given acquirer_bank can look
identical to a plain issuer_decline or acquirer-code event. What actually
distinguishes an acquirer-side OUTAGE is the pattern across many events:
multiple distinct customers, same acquirer_bank, failing within a short
time window.

This module runs AFTER Layer 1 (diagnosis.py) and can UPGRADE or OVERRIDE
a Layer 1 prediction to "acquirer_outage" (with high confidence) when a
real cluster is found — this is the one diagnosis that fundamentally
requires batch-level reasoning, not just single-event rules.
"""

from datetime import datetime, timedelta
from collections import defaultdict

CLUSTER_WINDOW_MINUTES = 15
CLUSTER_MIN_SIZE = 4          # minimum distinct events to call it a cluster
CLUSTER_MIN_DISTINCT_CUSTOMERS = 3


def _parse_ts(evt):
    return datetime.fromisoformat(evt["timestamp"])


def find_acquirer_clusters(events):
    """
    Groups events by acquirer_bank, then within each bank looks for
    time-windows containing enough distinct-customer failures to call
    it an outage rather than coincidental individual declines.

    Returns a dict: {event_id: cluster_info} for every event that is
    part of a detected cluster. cluster_info includes the bank, window,
    and cluster size, for use in the reasoning/audit trail.
    """
    by_bank = defaultdict(list)
    for evt in events:
        by_bank[evt["acquirer_bank"]].append(evt)

    clustered_event_ids = {}

    for bank, bank_events in by_bank.items():
        bank_events = sorted(bank_events, key=_parse_ts)

        # Sliding window: for each event, look at all events within
        # CLUSTER_WINDOW_MINUTES after it (same bank).
        for i, anchor in enumerate(bank_events):
            window_end = _parse_ts(anchor) + timedelta(minutes=CLUSTER_WINDOW_MINUTES)
            window_events = [anchor]
            for other in bank_events[i + 1:]:
                if _parse_ts(other) <= window_end:
                    window_events.append(other)
                else:
                    break

            distinct_customers = {e["customer_id"] for e in window_events}

            if (
                len(window_events) >= CLUSTER_MIN_SIZE
                and len(distinct_customers) >= CLUSTER_MIN_DISTINCT_CUSTOMERS
            ):
                window_start_ts = _parse_ts(anchor)
                for e in window_events:
                    # Keep the largest cluster an event appears in, in case
                    # of overlapping windows
                    existing = clustered_event_ids.get(e["event_id"])
                    if existing is None or len(window_events) > existing["cluster_size"]:
                        clustered_event_ids[e["event_id"]] = {
                            "acquirer_bank": bank,
                            "cluster_size": len(window_events),
                            "distinct_customers": len(distinct_customers),
                            "window_start": window_start_ts.isoformat(),
                            "window_minutes": CLUSTER_WINDOW_MINUTES,
                        }

    return clustered_event_ids


def apply_clustering(events, layer1_results):
    """
    layer1_results: list of (event, diagnosis) tuples from diagnose_batch().

    Returns a new list of (event, diagnosis) tuples where any event found
    to be part of a real acquirer-outage cluster has its diagnosis upgraded
    to acquirer_outage / high confidence, with reasoning explaining the
    cluster evidence. Events not in a cluster are returned unchanged.
    """
    clusters = find_acquirer_clusters(events)
    updated_results = []

    for evt, diagnosis in layer1_results:
        cluster_info = clusters.get(evt["event_id"])
        if cluster_info:
            updated_results.append((evt, {
                "predicted_cause": "acquirer_outage",
                "confidence": "high",
                "reasoning": (
                    f"Cross-event clustering found {cluster_info['cluster_size']} "
                    f"failed events across {cluster_info['distinct_customers']} "
                    f"distinct customers, all routed through "
                    f"{cluster_info['acquirer_bank']}, within a "
                    f"{cluster_info['window_minutes']}-minute window starting "
                    f"{cluster_info['window_start']}. This pattern is "
                    f"inconsistent with isolated individual declines and "
                    f"indicates an acquirer-side outage. "
                    f"(Layer 1 alone predicted: {diagnosis['predicted_cause']}, "
                    f"confidence={diagnosis['confidence']})"
                ),
            }))
        else:
            updated_results.append((evt, diagnosis))

    return updated_results
