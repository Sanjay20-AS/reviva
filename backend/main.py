"""
Reviva backend — FastAPI app entrypoint.

Run locally with:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes.api import router as api_router

app = FastAPI(title="Reviva API", version="0.1.0")

# Permissive CORS for local dev with the Vite frontend (localhost:5173).
# Tighten this to the deployed frontend origin before shipping.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "reviva-backend"}
