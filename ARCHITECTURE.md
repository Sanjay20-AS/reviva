# Architecture

## Processing pipeline

What happens to a single event, from raw signal to logged outcome.
Most events resolve in Layers 1–2; only genuinely ambiguous cases
reach Gemini.

```mermaid
flowchart TD
    A["150 synthetic events<br/>(events.json)"] --> B["Layer 1 — rule-based diagnosis<br/>issuer_decline, network_timeout,<br/>expired_instrument, insufficient_funds,<br/>fraud_hold, acquirer_outage (medium), ambiguous"]
    B --> C["Layer 2 — clustering<br/>cross-event acquirer-outage check<br/>(same bank, tight window, multiple customers)"]
    C -->|"high / medium confidence<br/>(~145 events)"| E["Action mapper<br/>cause → bounded action + stopping rule"]
    C -->|"still low confidence<br/>(~5 events)"| D["Layer 3 — Gemini<br/>reasons over the same signals,<br/>falls back to ambiguous on any API error"]
    D --> E
    E --> F["Executor<br/>simulates the action"]
    F -->|"auto-retry succeeds"| G1["outcome: recovered"]
    F -->|"auto-retry fails"| G2["outcome: not_recovered"]
    F -->|"non-retry action"| G3["outcome: pending_manual_action"]
    G1 --> H["Audit log (audit_log.jsonl)<br/>signals, diagnosis, reasoning, action,<br/>outcome, ground-truth comparison"]
    G2 --> H
    G3 --> H
    H --> I["Metrics summary<br/>recovery rate, amount recovered,<br/>diagnosis accuracy, full exceptions list<br/>(not_recovered + pending_manual_action, reported honestly)"]
```

## System architecture

How the pieces are actually deployed and talk to each other — separate
from the per-event logic above.

```mermaid
flowchart TD
    FE["React + Vite frontend<br/>Sidebar, MetricsPanel, Charts,<br/>EventStream, AuditLog"]
    BE["FastAPI backend<br/>runs the pipeline once per process start,<br/>caches the result; reads events.json,<br/>writes audit_log.jsonl"]
    LLM["Gemini API (gemini-3.6-flash)<br/>only called for the handful of<br/>low-confidence cases, not the full batch"]

    FE -->|"GET /api/metrics<br/>GET /api/events<br/>GET /api/audit-log<br/>(fetched once on load;<br/>/api/rerun forces a fresh run)"| BE
    BE -->|"HTTPS request per<br/>ambiguous event"| LLM
```

## Diagnosis rules (Layer 1)

| Signal | Cause |
|---|---|
| error_code in fraud/risk codes | fraud_hold (highest priority) |
| timeout-style error code AND latency_ms > 3500 | network_timeout |
| error_code indicates expired/invalid instrument, or instrument's own expiry has passed | expired_instrument |
| error_code in acquirer-side codes | acquirer_outage (medium confidence at single-event level) |
| explicit insufficient-funds error_code | insufficient_funds |
| issuer decline error_code | issuer_decline (confidence downgraded to medium if amount is high, since insufficient_funds can't be fully ruled out from the code alone) |
| nothing matches cleanly | ambiguous → routed to Gemini (Layer 3) |

Layer 1 alone reaches ~94% accuracy against the synthetic ground truth;
the remaining gap is closed by Layer 2 (cluster upgrades) and Layer 3
(Gemini on genuinely ambiguous cases).

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

## Frontend

- **Sidebar** — grouped navigation (Event Stream, Audit Trail, About), dark
  minimal shadcn-inspired visual style
- **MetricsPanel** — headline numbers (recovery rate, amount recovered,
  diagnosis accuracy) plus a status breakdown and the honest exceptions list
- **Charts** — recovery rate by cause (bar), cumulative amount recovered
  over the batch (line), both color-matched to the cause palette used
  throughout the dashboard
- **EventStream** — filterable, cause-coded cards showing each event's
  diagnosis, confidence, reasoning, action, and outcome
- **AuditLog** — expandable table with every decision, its signals, and a
  ground-truth correctness check, for full traceability

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