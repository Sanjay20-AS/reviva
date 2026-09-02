"""
API routes — serves the processed batch (events + diagnoses + actions +
outcomes) and summary metrics to the frontend dashboard.

The full pipeline (diagnosis -> clustering -> Gemini -> actions ->
executor) is run once per process start and cached in memory. For this
buildathon's scope (single demo batch, not a live production service),
re-running on every request isn't necessary — see run_pipeline() below
for where you'd add a refresh/re-run endpoint if needed later.
"""

import os
import json
import sys

from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.diagnosis import diagnose_batch
from engine.clustering import apply_clustering
from engine.actions import map_batch_actions
from engine.executor import execute_batch, write_audit_log, summarize_metrics

try:
    from engine.llm_diagnosis import resolve_ambiguous_cases
    GEMINI_AVAILABLE = bool(os.environ.get("GEMINI_API_KEY"))
except ImportError:
    GEMINI_AVAILABLE = False

router = APIRouter()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "events.json")

_cache = {"audit_entries": None, "metrics": None}


def run_pipeline():
    """Runs the full pipeline once and caches the result. Call
    invalidate_cache() if you want the next request to re-run it."""
    if _cache["audit_entries"] is not None:
        return _cache["audit_entries"], _cache["metrics"]

    with open(DATA_PATH) as f:
        events = json.load(f)

    layer1 = diagnose_batch(events)
    layer2 = apply_clustering(events, layer1)

    if GEMINI_AVAILABLE:
        layer3 = resolve_ambiguous_cases(layer2)
    else:
        # No API key configured -- proceed without Gemini rather than
        # failing the whole pipeline. Low-confidence cases stay as-is
        # and will show up honestly as "ambiguous" in the results.
        layer3 = layer2

    mapped = map_batch_actions(layer3)
    audit_entries = execute_batch(mapped, seed=7)
    write_audit_log(audit_entries)
    metrics = summarize_metrics(audit_entries)

    _cache["audit_entries"] = audit_entries
    _cache["metrics"] = metrics
    return audit_entries, metrics


def invalidate_cache():
    _cache["audit_entries"] = None
    _cache["metrics"] = None


@router.get("/api/events")
def get_events():
    """Returns the full processed batch: every event with its diagnosis,
    action, and outcome -- what the dashboard's event stream renders."""
    audit_entries, _ = run_pipeline()
    return {"events": audit_entries, "gemini_used": GEMINI_AVAILABLE}


@router.get("/api/events/{event_id}")
def get_event(event_id: str):
    audit_entries, _ = run_pipeline()
    for entry in audit_entries:
        if entry["event_id"] == event_id:
            return entry
    raise HTTPException(status_code=404, detail="Event not found")


@router.get("/api/metrics")
def get_metrics():
    """Returns the headline metrics: recovery rate, amount recovered,
    diagnosis accuracy, and the honest exception list."""
    _, metrics = run_pipeline()
    return metrics


@router.get("/api/audit-log")
def get_audit_log():
    """Returns the raw audit trail entries -- same data as /api/events,
    exposed separately since the frontend's AuditLog view may want to
    treat it as a distinct, append-only log view rather than the live
    event stream."""
    audit_entries, _ = run_pipeline()
    return {"audit_log": audit_entries}


@router.post("/api/rerun")
def rerun_pipeline():
    """Forces a fresh pipeline run (e.g. after regenerating events.json
    with a different seed). Useful for demoing a different batch live."""
    invalidate_cache()
    audit_entries, metrics = run_pipeline()
    return {"status": "ok", "total_events": len(audit_entries), "metrics": metrics}
