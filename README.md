# Reviva

**AI agent for payment degradation → root cause → recovery.**
Built for the Razorpay AI Buildathon — Track 03: AI Revenue Recovery.

## Problem

Revenue loss rarely happens in one clean step. A payment degrades, times out,
or gets declined for reasons that aren't always obvious. Reviva detects
degrading payments, diagnoses the likely root cause (issuer decline, network
timeout, expired instrument, insufficient funds, acquirer-side outage, or
fraud/risk hold), and executes a bounded, compliant recovery action —
with a full audit trail and honest, measured results.

## Status

🚧 Work in progress — built over one week for the buildathon submission.

- [x] Synthetic payment event generator with planted degradation patterns
- [ ] Root-cause diagnosis engine (rule-based + Gemini-assisted)
- [ ] Cross-event acquirer-outage clustering
- [ ] Action mapper + bounded executor with stopping rules
- [ ] Audit trail
- [ ] FastAPI backend
- [ ] React + Vite + Tailwind dashboard
- [ ] Deployment + demo video

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full data flow diagram.

## Tech stack

- **Frontend:** React + Vite + Tailwind CSS
- **Backend:** Python + FastAPI
- **LLM:** Gemini API (used only for ambiguous/low-confidence diagnosis cases)
- **Data:** synthetic, generated via `backend/data/generate_payment_events.py`

## Repo structure

```
reviva/
├── frontend/          # React + Vite + Tailwind dashboard
├── backend/
│   ├── data/           # synthetic event generator + sample dataset
│   ├── engine/          # diagnosis, clustering, action mapping, executor
│   ├── routes/          # FastAPI endpoints
│   └── audit/           # audit_log.jsonl (generated at runtime)
├── README.md
└── ARCHITECTURE.md
```

## Running the data generator

```bash
cd backend/data
python3 generate_payment_events.py --n 150 --seed 42 --out events.json
```

## License

MIT
