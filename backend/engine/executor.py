"""
Executor
---------
Simulates carrying out the recovery action chosen for each event, and
writes a full audit trail: every decision, the signals behind it, the
action taken, and the (simulated) outcome.

Simulation model (deliberately simple and transparent, not black-box):
- auto_retry actions succeed with a cause-specific recovery probability,
  meant to loosely reflect real-world recovery likelihood (e.g. a network
  timeout retry succeeds more often than a fraud hold "recovers").
- notify/escalate actions never auto-resolve here — they're logged as
  "pending_manual_action" since real resolution would depend on a human
  or the customer, which is outside this system's bounded scope.
- This is explicitly a SIMULATION for the buildathon demo, not a claim
  of live payment processing. That's stated in the README/pitch, not
  hidden here.
"""

import json
import random
import os
from datetime import datetime

# Loosely-motivated recovery probabilities per cause, used only for the
# simulated outcome. Kept in one place so they're easy to justify/tune.
RECOVERY_PROBABILITY = {
    "network_timeout": 0.85,
    "issuer_decline": 0.55,
    "insufficient_funds": 0.40,
    "acquirer_outage": 0.70,
}

AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "audit", "audit_log.jsonl"
)


def _simulate_outcome(cause, action_spec, seed_rng):
    if not action_spec["auto_retry"]:
        return {
            "outcome": "pending_manual_action",
            "amount_recovered": 0.0,
        }

    prob = RECOVERY_PROBABILITY.get(cause, 0.5)
    recovered = seed_rng.random() < prob
    return {
        "outcome": "recovered" if recovered else "not_recovered",
        "amount_recovered": None,  # filled in by caller with the event amount
    }


def execute_batch(mapped_results, seed=7):
    """
    mapped_results: list of (event, diagnosis, action_spec) tuples from
    actions.map_batch_actions().

    Returns:
        audit_entries: list of dicts, one per event, ready to write to
                        the audit log and to summarize as metrics.
    """
    rng = random.Random(seed)
    audit_entries = []

    for evt, diagnosis, action_spec in mapped_results:
        sim = _simulate_outcome(diagnosis["predicted_cause"], action_spec, rng)
        amount_recovered = evt["amount"] if sim["outcome"] == "recovered" else 0.0

        entry = {
            "event_id": evt["event_id"],
            "timestamp_processed": datetime.utcnow().isoformat(),
            "original_event_timestamp": evt["timestamp"],
            "customer_id": evt["customer_id"],
            "amount": evt["amount"],
            "signals": {
                "error_code": evt.get("error_code"),
                "latency_ms": evt.get("latency_ms"),
                "retry_count": evt.get("retry_count"),
                "acquirer_bank": evt.get("acquirer_bank"),
                "payment_method": evt.get("payment_method"),
            },
            "diagnosis": {
                "predicted_cause": diagnosis["predicted_cause"],
                "confidence": diagnosis["confidence"],
                "reasoning": diagnosis["reasoning"],
                "source": diagnosis.get("source", "rule_engine"),
            },
            "action": {
                "action": action_spec["action"],
                "description": action_spec["description"],
                "max_attempts": action_spec["max_attempts"],
                "cooldown_minutes": action_spec["cooldown_minutes"],
            },
            "outcome": sim["outcome"],
            "amount_recovered": amount_recovered,
            # Ground truth included ONLY for scoring/demo purposes — a
            # production system wouldn't have this, but it lets the
            # dashboard show honest accuracy alongside recovery metrics.
            "ground_truth_cause": evt.get("degradation_type"),
            "diagnosis_correct": diagnosis["predicted_cause"] == evt.get("degradation_type"),
        }
        audit_entries.append(entry)

    return audit_entries


def write_audit_log(audit_entries, path=AUDIT_LOG_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for entry in audit_entries:
            f.write(json.dumps(entry) + "\n")
    return path


def summarize_metrics(audit_entries):
    """Produces the headline numbers for the dashboard: recovery rate,
    total amount recovered, diagnosis accuracy, and an honest exception
    list (events not recovered), rather than only reporting successes."""
    total = len(audit_entries)
    total_amount_at_risk = sum(e["amount"] for e in audit_entries)
    total_recovered = sum(e["amount_recovered"] for e in audit_entries)
    recovered_count = sum(1 for e in audit_entries if e["outcome"] == "recovered")
    pending_manual = sum(1 for e in audit_entries if e["outcome"] == "pending_manual_action")
    not_recovered = sum(1 for e in audit_entries if e["outcome"] == "not_recovered")
    correct_diagnoses = sum(1 for e in audit_entries if e["diagnosis_correct"])

    exceptions = [
        {
            "event_id": e["event_id"],
            "amount": e["amount"],
            "predicted_cause": e["diagnosis"]["predicted_cause"],
            "outcome": e["outcome"],
        }
        for e in audit_entries
        if e["outcome"] in ("not_recovered", "pending_manual_action")
    ]

    return {
        "total_events": total,
        "total_amount_at_risk": round(total_amount_at_risk, 2),
        "total_amount_recovered": round(total_recovered, 2),
        "recovery_rate_pct": round(100 * recovered_count / total, 1) if total else 0,
        "recovered_count": recovered_count,
        "not_recovered_count": not_recovered,
        "pending_manual_count": pending_manual,
        "diagnosis_accuracy_pct": round(100 * correct_diagnoses / total, 1) if total else 0,
        "exceptions": exceptions,
    }
