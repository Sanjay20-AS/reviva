# Architecture

## Data flow

```
events.json (synthetic stream)
        │
        ▼
Diagnosis Layer 1 — rule-based, per-event
  (issuer_decline / network_timeout / expired_instrument /
   insufficient_funds / fraud_hold / ambiguous)
        │
        ▼
Clustering Layer 2 — cross-event acquirer-outage detection
  (overrides Layer 1 where a cluster is found: same acquirer_bank,
   tight time window, multiple distinct customers)
        │
        ▼
Gemini call — ONLY for low-confidence / ambiguous cases from Layer 1
  (reasons over the event's signals, returns cause + explanation)
        │
        ▼
Action Mapper — cause → bounded recovery action + stopping rule
        │
        ▼
Executor — simulates the recovery action (retry / notify / escalate),
  respects max-attempt and cooldown rules
        │
        ├──► Audit Log (audit/audit_log.jsonl) — every decision,
        │     signals considered, action taken, outcome
        ▼
FastAPI REST endpoints
        │
        ▼
React + Vite + Tailwind dashboard
  — event stream, per-case reasoning cards, recovery metrics,
    audit log view, honest exception list
```

## Diagnosis rules (Layer 1)

| Signal | Cause |
|---|---|
| latency_ms > 3500 AND timeout-style error code | network_timeout |
| retry_count ≥ 1 AND instrument expired/invalid | expired_instrument |
| error_code in fraud/risk codes | fraud_hold |
| decline-style error_code + high amount + low latency | insufficient_funds (medium confidence) |
| decline-style error_code, other signals | issuer_decline |
| conflicting/weak signals | ambiguous → routed to Gemini |

## Recovery action mapping

| Cause | Action | Stopping rule |
|---|---|---|
| network_timeout | retry immediately, same route | max 2 retries |
| issuer_decline | retry after cooldown (~6h) | max 2 retries |
| insufficient_funds | delay retry (~3 days) | max 1 retry |
| expired_instrument | notify customer, no auto-retry | 0 retries |
| acquirer_outage | retry via alternate route | max 1 retry, then escalate |
| fraud_hold | escalate to manual review | 0 retries |
| ambiguous | escalate to manual review | 0 retries |

## Why this design

- **Two-layer diagnosis** separates fast/explainable rule-based classification
  (handles the majority of clear-cut cases) from cross-event reasoning
  (acquirer-outage clustering), which cannot be detected from a single event
  in isolation.
- **LLM used selectively**, not universally — Gemini is only called for
  ambiguous cases, keeping the system fast, cheap, and auditable for the
  ~90% of clear-cut events while still using AI meaningfully where rules
  alone are insufficient.
- **Every decision is logged** with the signals considered and the reasoning,
  satisfying the track's requirement for an audit trail and honest,
  non-cherry-picked exception reporting.
