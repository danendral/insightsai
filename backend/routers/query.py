"""
routers/query.py - Natural Language Query Route

DEPENDENCY INJECTION IN ACTION:
  This endpoint uses two injected dependencies:
    - settings: Settings = Depends(get_settings)   → API keys, model config
    - (implicitly) data_service.get_current_df()   → the loaded DataFrame

  Notice the route function is clean:
    1. Get data (or 404)
    2. Call AI service (or map errors to HTTP codes)
    3. Return response

  Zero configuration code, zero global variable access.

ERROR MAPPING PATTERN:
  Services raise domain-specific exceptions (RuntimeError, AuthenticationError).
  Routers catch them and convert to appropriate HTTP status codes.
  This is a consistent pattern throughout the codebase:

      Service raises         →  Router returns
      ─────────────────────────────────────────
      RuntimeError           →  HTTP 404 (no data loaded)
      AuthenticationError    →  HTTP 401 (bad API key)
      Exception              →  HTTP 500 (unexpected error)
"""

import anthropic
from fastapi import APIRouter, Depends, HTTPException

from core.config import Settings, get_settings
from models.schemas import QueryRequest, QueryResponse
from services import ai_service, data_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_data(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Answer a natural language question about the loaded dataset using Claude.
    """
    try:
        df = data_service.get_current_df()
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        answer = ai_service.ask_claude(
            question=request.question,
            df=df,
            settings=settings,
        )
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid Anthropic API key")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI query failed: {e}")

    return QueryResponse(question=request.question, answer=answer)
