"""
LLM-Assisted Diagnosis — Layer 3 (Gemini, ambiguous cases only)
-------------------------------------------------------------------
Layer 1 (rules) and Layer 2 (clustering) resolve the large majority of
events deterministically and cheaply. This layer is called ONLY for
events that come out of Layer 1+2 with confidence == "low" (i.e. no rule
matched cleanly) — using an LLM call for every event would be slow,
expensive, and less auditable than necessary.

Requires GEMINI_API_KEY to be set in the environment (see .env.example).
"""

import os
import json
import google.generativeai as genai

GEMINI_MODEL = "gemini-2.0-flash"

VALID_CAUSES = {
    "issuer_decline",
    "network_timeout",
    "expired_instrument",
    "insufficient_funds",
    "acquirer_outage",
    "fraud_hold",
    "ambiguous",  # LLM may still conclude it's genuinely unresolvable
}

PROMPT_TEMPLATE = """You are a payments risk analyst. Given the signals below for a
single degraded payment event, diagnose the most likely root cause.

Event signals:
- payment_method: {payment_method}
- error_code: {error_code}
- latency_ms: {latency_ms}
- retry_count: {retry_count}
- amount: {amount}
- instrument_details: {instrument_details}

Choose exactly one cause from this fixed list:
issuer_decline, network_timeout, expired_instrument, insufficient_funds,
acquirer_outage, fraud_hold, ambiguous (use "ambiguous" only if truly
unresolvable from these signals).

Respond ONLY with valid JSON, no markdown fences, in this exact shape:
{{"predicted_cause": "<one of the causes above>", "confidence": "high|medium|low", "reasoning": "<one or two sentence explanation citing specific signals>"}}
"""


def _get_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Copy .env.example to .env and add your key."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL)


def diagnose_with_gemini(evt, model=None):
    """
    Calls Gemini for a single ambiguous event. Returns the same shape as
    diagnose_event() in diagnosis.py, plus a "source": "gemini" marker
    for the audit trail. Falls back to a safe "ambiguous"/manual-review
    result if the call fails or returns unparseable output — this layer
    should never crash the pipeline or silently invent a confident-sounding
    answer it can't back up.
    """
    if model is None:
        model = _get_model()

    prompt = PROMPT_TEMPLATE.format(
        payment_method=evt.get("payment_method"),
        error_code=evt.get("error_code"),
        latency_ms=evt.get("latency_ms"),
        retry_count=evt.get("retry_count"),
        amount=evt.get("amount"),
        instrument_details=json.dumps(evt.get("instrument_details", {})),
    )

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip accidental markdown fences if the model adds them anyway
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)

        cause = parsed.get("predicted_cause")
        if cause not in VALID_CAUSES:
            raise ValueError(f"Gemini returned an unrecognized cause: {cause}")

        return {
            "predicted_cause": cause,
            "confidence": parsed.get("confidence", "low"),
            "reasoning": parsed.get("reasoning", ""),
            "source": "gemini",
        }
    except Exception as exc:
        # Fail safe: never let an LLM error produce a false-confident
        # diagnosis. Route to manual review instead.
        return {
            "predicted_cause": "ambiguous",
            "confidence": "low",
            "reasoning": (
                f"Gemini call failed or returned unparseable output "
                f"({exc}). Routed to manual review as a safe fallback."
            ),
            "source": "gemini_fallback",
        }


def resolve_ambiguous_cases(results):
    """
    results: list of (event, diagnosis) tuples, post Layer 1 + Layer 2.

    For any event still at confidence == "low", calls Gemini and replaces
    its diagnosis. All other events pass through unchanged. Reuses a single
    Gemini model instance across calls for efficiency.
    """
    model = None
    updated = []

    for evt, diagnosis in results:
        if diagnosis.get("confidence") == "low":
            if model is None:
                model = _get_model()
            new_diagnosis = diagnose_with_gemini(evt, model=model)
            updated.append((evt, new_diagnosis))
        else:
            updated.append((evt, diagnosis))

    return updated
