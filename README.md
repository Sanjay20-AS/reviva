# Reviva

**AI agent for payment degradation → root cause → recovery.**
Built for the Razorpay AI Buildathon — Track 03: AI Revenue Recovery.

## Problem

Revenue loss rarely happens in one clean step. A payment degrades, times out,
or gets declined for reasons that aren't always obvious. Reviva detects
degrading payments, diagnoses the likely root cause (issuer decline, network
timeout, expired instrument, insufficient funds, acquirer-side outage, or
fraud/risk hold), and executes a bounded, compliant recovery action —
with a full audit trail and honest, measured results rather than
cherry-picked wins.

## Results (150-event synthetic batch)

- **Recovery rate:** 48.7%
- **Amount recovered:** ₹9.8L of ₹19.2L at risk
- **Diagnosis accuracy:** ~93% against ground truth
- Every unresolved case is reported honestly in the dashboard's exceptions
  list — not filtered out to inflate the headline numbers.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full data flow diagram
and design rationale.

## Tech stack

- **Frontend:** React + Vite + Tailwind CSS, recharts for visualizations,
  lucide-react for icons
- **Backend:** Python + FastAPI
- **LLM:** Gemini API (`gemini-3.6-flash`) — used only for ambiguous/
  low-confidence diagnosis cases, not the full batch
- **Data:** synthetic, generated via `backend/data/generate_payment_events.py`

## Repo structure

```
reviva/
├── frontend/                # React + Vite + Tailwind dashboard
│   └── src/
│       ├── components/       # Sidebar, MetricsPanel, Charts, EventStream, AuditLog
│       └── App.jsx
├── backend/
│   ├── data/                 # synthetic event generator + sample dataset
│   ├── engine/                # diagnosis, clustering, LLM layer, actions, executor
│   ├── routes/                 # FastAPI endpoints
│   ├── audit/                   # audit_log.jsonl (generated at runtime)
│   └── main.py                  # FastAPI app entrypoint
├── README.md
└── ARCHITECTURE.md
```

## Running it locally

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
cp .env.example .env         # add your GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Then open the frontend URL (typically `http://localhost:5173`).

## Regenerating the dataset

```bash
cd backend/data
python3 generate_payment_events.py --n 150 --seed 42 --out events.json
```

## License

MIT