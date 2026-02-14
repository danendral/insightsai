"""
routers/data.py - Data & Upload Routes

WHAT IS AN APIRouter?
  Think of it as a mini FastAPI app that handles a slice of your routes.
  main.py registers it with a prefix, so every route here automatically
  becomes /api/<path>.

  Before (main.py):
      @app.get("/api/data")
      @app.post("/api/upload")
      ...

  After (this file):
      @router.get("/data")        →  app mounts as /api/data
      @router.post("/upload")     →  app mounts as /api/upload

WHY SPLIT BY DOMAIN?
  If you later add authentication, you add a single dependency to this
  router and ALL data routes are protected — no touching each endpoint.

DEPENDENCY INJECTION WITH Depends():
  FastAPI's Depends() is a first-class DI system. When you write:
      settings: Settings = Depends(get_settings)
  FastAPI:
    1. Calls get_settings() once per request (or uses cache)
    2. Passes the result as the `settings` argument
    3. Handles errors (e.g., missing env var) before your function runs

  This means your route functions stay pure — they receive ready-to-use
  objects, not raw environment variables.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.config import Settings, get_settings
from models.schemas import DataSummary, RawDataResponse, UploadResponse
from services import data_service

router = APIRouter()


@router.get("/sample", response_model=DataSummary)
def load_sample_data(settings: Settings = Depends(get_settings)):
    """
    Load the built-in sample sales dataset into memory.

    GET vs POST?
      Technically this mutates server state, so POST would be more
      RESTful. GET is kept here to match the original design and because
      it's a read-only sample with no side effects on user data.
    """
    return data_service.load_sample_data(settings.sample_data_path)


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    """
    Upload a CSV file to analyse.

    FLOW:
      1. FastAPI receives multipart/form-data, wraps file in UploadFile
      2. We validate extension here (HTTP concern → stays in router)
      3. Read bytes, pass to service (business concern → goes to service)
      4. Service validates size/content and raises ValueError on failure
      5. We convert ValueError → HTTP 400 here (HTTP concern → router)

    WHY async?
      file.read() is an async operation — it reads from the incoming
      HTTP stream. Using `await` frees the event loop while waiting,
      so other requests can be served concurrently.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()

    try:
        result = data_service.load_csv_bytes(contents, file.filename, settings.upload_dir)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return UploadResponse(**result)


@router.get("/data", response_model=DataSummary)
def get_data_summary():
    """Return summary statistics for the currently loaded dataset."""
    try:
        df = data_service.get_current_df()
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return data_service.compute_summary(df)


@router.get("/data/raw", response_model=RawDataResponse)
def get_raw_data(page: int = 1, page_size: int = 50):
    """
    Return paginated raw rows from the current dataset.

    QUERY PARAMETERS:
      FastAPI reads page and page_size from the URL automatically:
          GET /api/data/raw?page=2&page_size=25
      No extra parsing code needed — FastAPI validates types too.
    """
    try:
        result = data_service.get_raw_data(page=page, page_size=page_size)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RawDataResponse(**result)
