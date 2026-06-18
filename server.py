"""
KiahBao.AI FastAPI Server — Backend bridge for the Next.js frontend.
Exposes the full 4-tier pipeline (Ingest → Route → LLM → Verify) via REST.
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal
import uvicorn

from app import KiahBaoApp
from verification.math_validator import BuyerProfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
# Request / Response Schemas
# ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Incoming query from the web frontend."""
    prompt: str = Field(..., description="User's natural language / Singlish question")
    # Buyer profile
    youngest_buyer_age: int = Field(30, ge=21, le=99)
    flat_remaining_lease: int = Field(70, ge=1, le=99)
    average_monthly_income: float = Field(5000.0, ge=0)
    is_family: bool = Field(True)
    proximity_km: float = Field(5.0, ge=0)
    living_with_parents: bool = Field(False)
    # Citizenship
    citizenship_status: Literal["SC", "PR"] = Field("SC", description="SC = Singapore Citizen | PR = Permanent Resident")
    partner_citizenship: Literal["SC", "PR", "none"] = Field("none", description="Citizenship of spouse/partner")
    has_parents_in_sg: bool = Field(True, description="Whether buyer's parents are Singapore-based")

class QueryResponse(BaseModel):
    """Structured response back to the frontend."""
    query: str
    route: str
    response: str
    profile: dict
    status: str = "success"

class HealthResponse(BaseModel):
    status: str
    model: str
    engine_ready: bool

# ────────────────────────────────────────────────
# App Setup
# ────────────────────────────────────────────────

app = FastAPI(
    title="KiahBao.AI API 🏡 仔包",
    description="Singapore housing knowledge engine — HDB grants, CPF, renovations, resale pricing.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Allow the Next.js dev server (port 3000) and production builds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise the KiahBao orchestrator once at startup
logger.info("Booting KiahBao.AI orchestrator…")
kiahbao = KiahBaoApp()
logger.info("KiahBao.AI orchestrator ready ✓")

# ────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Quick liveness probe for the frontend to confirm backend is up."""
    engine_ready = kiahbao.engine is not None and kiahbao.engine.llm is not None
    return HealthResponse(
        status="ok",
        model="kiahbao-ai (aisingapore/Gemma-SEA-LION-v4-27B-IT)",
        engine_ready=engine_ready,
    )


@app.post("/api/query", response_model=QueryResponse, tags=["Core"])
def query(request: QueryRequest):
    """
    Main inference endpoint.
    Accepts a free-form Singlish / English prompt plus buyer profile data.
    Returns a verified, hallucination-free answer from the 4-tier pipeline.
    """
    try:
        profile = BuyerProfile(
            youngest_buyer_age=request.youngest_buyer_age,
            flat_remaining_lease=request.flat_remaining_lease,
            average_monthly_income=request.average_monthly_income,
            is_family=request.is_family,
            proximity_km=request.proximity_km,
            living_with_parents=request.living_with_parents,
            citizenship_status=request.citizenship_status,
            partner_citizenship=request.partner_citizenship,
            has_parents_in_sg=request.has_parents_in_sg,
        )
        result = kiahbao.query(prompt=request.prompt, profile=profile)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market", tags=["Data"])
def get_market_snapshot():
    """Returns the latest HDB resale price snapshot from data.gov.sg."""
    try:
        df = kiahbao.fetcher.fetch_recent_transactions(limit=10)
        if df.empty:
            return {"status": "no_data", "transactions": []}
        records = df.head(10).to_dict(orient="records")
        avg = df["resale_price"].astype(float).mean()
        return {
            "status": "ok",
            "average_price": round(avg, 2),
            "sample_count": len(records),
            "transactions": records,
        }
    except Exception as e:
        logger.error(f"Market data error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/town/{town_name}", tags=["Data"])
def get_town_prices(town_name: str):
    """
    Returns HDB resale price summary for a specific town.
    Accepts canonical names (e.g. 'Tampines') or aliases (e.g. 'AMK', 'CCK').
    This endpoint is also called by the @ location chat feature.
    """
    try:
        result = kiahbao.fetcher.fetch_by_town(town_name)
        return result
    except Exception as e:
        logger.error(f"Town price error for '{town_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news", tags=["Data"])
def get_latest_news():
    """
    Returns the latest HDB Pulse news articles.
    Reads from the scraped data/processed/latest_news.json cache.
    """
    try:
        from pathlib import Path
        import json
        
        base_dir = Path(__file__).resolve().parent
        news_file = base_dir / "data" / "processed" / "latest_news.json"
        
        if news_file.exists():
            with open(news_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        else:
            from ingestion.scrape_hdb_info import _news_fallback
            articles = _news_fallback()
            return {"fetched_at": "static_fallback", "articles": articles}
    except Exception as e:
        logger.error(f"News endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
