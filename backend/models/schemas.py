"""
models/schemas.py - Pydantic Request & Response Schemas

WHY A DEDICATED FILE:
  Pydantic models are the contract between your API and its callers.
  Keeping them in one place means:
  - One import to find all shapes: `from models.schemas import QueryRequest`
  - Easy to version (v1 vs v2 schemas) later
  - Clear separation: schemas describe data, services process it

PYDANTIC v2 QUICK REFERENCE:
  - BaseModel        → define the shape of a JSON body or response
  - Field(...)       → required field (no default)
  - Field(default)   → optional field with a default value
  - model_config     → class-level Pydantic settings (replaces class Config)

FASTAPI INTEGRATION:
  - Request body:  declare as a function parameter type hint
      async def query(request: QueryRequest): ...
  - Response body: declare as response_model=
      @router.post("/query", response_model=QueryResponse)
  FastAPI serialises/deserialises automatically.
"""

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Query endpoints
# --------------------------------------------------------------------------- #

class QueryRequest(BaseModel):
    """Body for POST /api/query"""
    question: str = Field(..., min_length=1, description="Natural language question about the data")


class QueryResponse(BaseModel):
    """Response from POST /api/query"""
    question: str
    answer: str


# --------------------------------------------------------------------------- #
# Data / upload endpoints
# --------------------------------------------------------------------------- #

class UploadResponse(BaseModel):
    """Response from POST /api/upload"""
    message: str
    filename: str
    rows: int
    columns: int


class DataSummary(BaseModel):
    """
    Response from GET /api/data and GET /api/sample.

    summary_stats shape:
        {
          "revenue": {"mean": 1234.5, "min": 100.0, "max": 9999.0, "sum": 44444.0},
          ...
        }
    """
    row_count: int
    column_count: int
    columns: list[str]
    numeric_columns: list[str]
    date_range: dict | None = None
    summary_stats: dict


class RawDataResponse(BaseModel):
    """Response from GET /api/data/raw"""
    data: list[dict]
    total_rows: int
    page: int
    page_size: int
    total_pages: int


# --------------------------------------------------------------------------- #
# Chart endpoints
# --------------------------------------------------------------------------- #

class ChartResponse(BaseModel):
    """Response from GET /api/charts/{chart_type}"""
    chart_type: str
    data: list[dict]
