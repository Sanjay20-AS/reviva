"""
Diagnosis Engine — Layer 1 (per-event rule classifier)
--------------------------------------------------------
Looks at a single payment event's signals (error_code, latency_ms,
retry_count, instrument_details) and produces a predicted root cause,
a confidence level, and a human-readable reasoning string.

Deliberately does NOT look at `degradation_type` (the ground-truth label) —
that field exists only for scoring accuracy afterward, not as an input.

Low-confidence / ambiguous cases are flagged so the caller can route them
to the Gemini-assisted layer (see llm_diagnosis.py) instead of guessing.
"""

from datetime import datetime


TIMEOUT_CODES = {"GATEWAY_TIMEOUT", "NO_RESPONSE"}
FRAUD_CODES = {"RISK_HOLD_61", "VELOCITY_LIMIT_EXCEEDED"}
DECLINE_CODES = {"BANK_DECLINE_05", "BANK_DECLINE_51"}
EXPIRED_CODES = {"EXPIRED_CARD", "INVALID_UPI_HANDLE"}
FUNDS_CODES = {"INSUFFICIENT_FUNDS"}
ACQUIRER_CODES = {"ACQUIRER_UNAVAILABLE", "GATEWAY_5XX"}

HIGH_AMOUNT_THRESHOLD = 5000
HIGH_LATENCY_THRESHOLD_MS = 3500


def _instrument_is_expired(evt):
    details = evt.get("instrument_details", {})
    if evt.get("payment_method") == "card":
        expiry = details.get("card_expiry")
        if not expiry:
            return False
        try:
            month, year = expiry.split("/")
            expiry_date = datetime(2000 + int(year), int(month), 28)
            return expiry_date < datetime(2026, 8, 1)
        except (ValueError, AttributeError):
            return False
    elif evt.get("payment_method") == "upi":
        return details.get("valid") is False
    return False


def diagnose_event(evt):
    """
    Returns a dict:
        {
            "predicted_cause": str,
            "confidence": "high" | "medium" | "low",
            "reasoning": str,
        }
    """
    error_code = evt.get("error_code")
    latency = evt.get("latency_ms", 0)
    retry_count = evt.get("retry_count", 0)
    amount = evt.get("amount", 0)

    # 1. Fraud/risk hold — highest priority, never auto-retry
    if error_code in FRAUD_CODES:
        return {
            "predicted_cause": "fraud_hold",
            "confidence": "high",
            "reasoning": (
                f"error_code '{error_code}' matches known fraud/risk-hold "
                f"signatures. Flagging for manual review rather than retry."
            ),
        }

    # 2. Network/gateway timeout — high latency + timeout-style code
    if error_code in TIMEOUT_CODES and latency > HIGH_LATENCY_THRESHOLD_MS:
        return {
            "predicted_cause": "network_timeout",
            "confidence": "high",
            "reasoning": (
                f"error_code '{error_code}' with latency {latency}ms "
                f"(> {HIGH_LATENCY_THRESHOLD_MS}ms threshold) indicates the "
                f"request never completed cleanly, consistent with a "
                f"network/gateway timeout rather than a hard decline."
            ),
        }

    # 3. Expired/invalid instrument — repeated failures + expired instrument
    if error_code in EXPIRED_CODES or _instrument_is_expired(evt):
        return {
            "predicted_cause": "expired_instrument",
            "confidence": "high" if retry_count >= 1 else "medium",
            "reasoning": (
                f"Instrument details indicate an expired/invalid "
                f"{evt.get('payment_method')} "
                f"(retry_count={retry_count}), so retrying without prompting "
                f"the customer to update their payment method would keep failing."
            ),
        }

    # 4. Acquirer-side codes at the single-event level (may be overridden
    #    by Layer 2 clustering if a real outage pattern is detected across
    #    multiple events)
    if error_code in ACQUIRER_CODES:
        return {
            "predicted_cause": "acquirer_outage",
            "confidence": "medium",
            "reasoning": (
                f"error_code '{error_code}' suggests an acquirer-side issue. "
                f"Confidence is medium at the single-event level — this will "
                f"be upgraded to high confidence if Layer 2 clustering finds "
                f"other events sharing this acquirer_bank in the same window."
            ),
        }

    # 5. Decline-style codes — distinguish insufficient_funds vs issuer_decline
    if error_code in DECLINE_CODES or error_code in FUNDS_CODES:
        if error_code in FUNDS_CODES:
            return {
                "predicted_cause": "insufficient_funds",
                "confidence": "high",
                "reasoning": (
                    f"error_code '{error_code}' is an explicit insufficient-funds "
                    f"signal. Recommending a delayed retry rather than an "
                    f"immediate one."
                ),
            }
        # BANK_DECLINE_* codes are issuer declines by construction. Amount
        # alone is too weak a signal to override that (kept only as a note
        # in the reasoning, not as a reclassification trigger) — treating
        # every high-amount decline as insufficient_funds produced too many
        # false reclassifications in testing.
        return {
            "predicted_cause": "issuer_decline",
            "confidence": "high" if amount < HIGH_AMOUNT_THRESHOLD else "medium",
            "reasoning": (
                f"error_code '{error_code}' is an issuer decline code. "
                f"Amount is ₹{amount:.2f}"
                + (
                    f" (above the ₹{HIGH_AMOUNT_THRESHOLD} threshold, so "
                    f"insufficient_funds can't be fully ruled out — flagged "
                    f"medium confidence)."
                    if amount >= HIGH_AMOUNT_THRESHOLD
                    else "."
                )
            ),
        }

    # 6. Nothing matched clearly — ambiguous, route to Gemini-assisted layer
    return {
        "predicted_cause": "ambiguous",
        "confidence": "low",
        "reasoning": (
            f"Signals don't cleanly match a known pattern "
            f"(error_code='{error_code}', latency={latency}ms, "
            f"retry_count={retry_count}). Routing to LLM-assisted diagnosis."
        ),
    }


def diagnose_batch(events):
    """Runs diagnose_event over a full batch, returns list of
    (event, diagnosis) tuples. Does not mutate the original events."""
    results = []
    for evt in events:
        diagnosis = diagnose_event(evt)
        results.append((evt, diagnosis))
    return results
