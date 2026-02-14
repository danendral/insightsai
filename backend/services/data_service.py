"""
services/data_service.py - Data Processing Business Logic

WHAT IS A SERVICE LAYER?
  A service contains your *business logic* — the "what does this app actually
  do" code — completely separate from HTTP concerns (status codes, headers,
  request parsing). This separation matters because:

  1. TESTABILITY: You can unit-test compute_summary() by passing a DataFrame
     directly. No HTTP request needed, no FastAPI spinning up.

  2. REUSABILITY: Multiple endpoints can call the same service function.
     Both /api/upload and /api/sample need compute_summary() — they just
     import it, done.

  3. READABILITY: Routers become thin wiring; services become the logic.
     When something breaks, you know exactly which layer to look in.

IN-MEMORY STATE:
  current_df lives here as a module-level variable. This is still the simple
  in-memory approach — Stage 2 (database) will replace this with a proper
  persistence layer. For now, it's isolated in one place instead of being a
  global scattered across main.py.
"""

from io import BytesIO
from pathlib import Path

import pandas as pd

from models.schemas import DataSummary

# ---------------------------------------------------------------------------
# In-memory data store
# ---------------------------------------------------------------------------
# WHY MODULE-LEVEL:
#   Python modules are singletons — imported once, shared everywhere.
#   Any code that does `from services.data_service import current_df` gets
#   the same object. This is fine for a single-process dev server.
#   Stage 2 will replace this with a database session.
# ---------------------------------------------------------------------------
current_df: pd.DataFrame | None = None

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_sample_data(sample_data_path: Path) -> DataSummary:
    """Read the built-in CSV and store it in memory. Returns a summary."""
    global current_df
    current_df = pd.read_csv(sample_data_path)
    return compute_summary(current_df)


def load_csv_bytes(contents: bytes, filename: str, upload_dir: Path) -> dict:
    """
    Parse raw CSV bytes into a DataFrame.

    Returns a dict with keys: message, filename, rows, columns.
    Raises ValueError on invalid input so the router can map it to HTTP 400.

    WHY bytes and not a file path?
      The router receives an UploadFile from FastAPI. Reading it gives bytes.
      Services shouldn't know about HTTP — passing bytes keeps this function
      pure and easily testable (just pass b"col1,col2\\n1,2").
    """
    global current_df

    if len(contents) > MAX_FILE_SIZE:
        raise ValueError("File too large (max 10 MB)")

    try:
        df = pd.read_csv(BytesIO(contents))
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")

    if df.empty:
        raise ValueError("CSV file is empty")

    current_df = df

    # Persist a copy to disk for reference (non-blocking, best-effort)
    upload_dir.mkdir(exist_ok=True)
    (upload_dir / filename).write_bytes(contents)

    return {
        "message": "File uploaded successfully",
        "filename": filename,
        "rows": len(df),
        "columns": len(df.columns),
    }


def get_current_df() -> pd.DataFrame:
    """
    Return the active DataFrame or raise RuntimeError if none is loaded.

    WHY A GETTER FUNCTION?
      Routers import this function, not the variable directly. That makes it
      easy to mock in tests:
          monkeypatch.setattr("services.data_service.current_df", fake_df)
    """
    if current_df is None:
        raise RuntimeError("No data loaded. Upload a CSV or load sample data first.")
    return current_df


# ---------------------------------------------------------------------------
# Summary & stats
# ---------------------------------------------------------------------------

def compute_summary(df: pd.DataFrame) -> DataSummary:
    """
    Compute descriptive statistics for any DataFrame.

    Returns a DataSummary Pydantic model — not a raw dict — so callers
    get type safety and the router gets automatic JSON serialisation.
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    date_range = _detect_date_range(df)

    stats: dict = {}
    for col in numeric_cols:
        stats[col] = {
            "mean": round(float(df[col].mean()), 2),
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
            "sum": round(float(df[col].sum()), 2),
        }

    return DataSummary(
        row_count=len(df),
        column_count=len(df.columns),
        columns=df.columns.tolist(),
        numeric_columns=numeric_cols,
        date_range=date_range,
        summary_stats=stats,
    )


def get_raw_data(page: int, page_size: int) -> dict:
    """Return one page of raw rows from the current DataFrame."""
    df = get_current_df()
    start = (page - 1) * page_size
    end = start + page_size
    subset = df.iloc[start:end]
    total_pages = (len(df) + page_size - 1) // page_size

    return {
        "data": subset.to_dict(orient="records"),
        "total_rows": len(df),
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ---------------------------------------------------------------------------
# Chart data helpers
# ---------------------------------------------------------------------------

def get_chart_data_revenue_trend(df: pd.DataFrame) -> list[dict]:
    """Monthly revenue trend aggregated across all segments."""
    date_col = _find_date_col(df)
    if date_col is None:
        return []

    grouped = (
        df.groupby(date_col)
        .agg(revenue=("revenue", "sum"), customers=("customers", "sum"))
        .reset_index()
        .sort_values(date_col)
        .rename(columns={date_col: "month"})
    )
    return grouped.to_dict(orient="records")


def get_chart_data_by_category(df: pd.DataFrame) -> list[dict]:
    """Revenue broken down by product category."""
    cat_col = next(
        (c for c in df.columns if "category" in c.lower() or "product" in c.lower()), None
    )
    if cat_col is None or "revenue" not in df.columns:
        return []

    grouped = df.groupby(cat_col)["revenue"].sum().reset_index()
    grouped.columns = ["category", "revenue"]
    return grouped.to_dict(orient="records")


def get_chart_data_by_region(df: pd.DataFrame) -> list[dict]:
    """Revenue broken down by region."""
    region_col = next((c for c in df.columns if "region" in c.lower()), None)
    if region_col is None or "revenue" not in df.columns:
        return []

    grouped = df.groupby(region_col)["revenue"].sum().reset_index()
    grouped.columns = ["region", "revenue"]
    return grouped.to_dict(orient="records")


def get_chart_data_campaign_performance(df: pd.DataFrame) -> list[dict]:
    """Marketing spend vs revenue by campaign."""
    campaign_col = next((c for c in df.columns if "campaign" in c.lower()), None)
    if campaign_col is None:
        return []

    agg_cols = {}
    for col in ("revenue", "marketing_spend", "leads_generated"):
        if col in df.columns:
            agg_cols[col] = (col, "sum")

    if not agg_cols:
        return []

    grouped = df.groupby(campaign_col).agg(**agg_cols).reset_index()
    grouped.rename(columns={campaign_col: "campaign"}, inplace=True)
    return grouped.to_dict(orient="records")


def get_chart_data_conversion_funnel(df: pd.DataFrame) -> list[dict]:
    """Aggregated conversion funnel: Leads → Deals → Customers."""
    metrics = {}
    for label, col in [("Leads", "leads_generated"), ("Deals Closed", "deals_closed"), ("Customers", "customers")]:
        if col in df.columns:
            metrics[label] = int(df[col].sum())
    return [{"stage": k, "value": v} for k, v in metrics.items()]


def get_chart_data_marketing_roi(df: pd.DataFrame) -> list[dict]:
    """Monthly marketing ROI (revenue / spend)."""
    date_col = _find_date_col(df)
    if date_col is None or "revenue" not in df.columns or "marketing_spend" not in df.columns:
        return []

    grouped = (
        df.groupby(date_col)
        .agg(revenue=("revenue", "sum"), marketing_spend=("marketing_spend", "sum"))
        .reset_index()
        .sort_values(date_col)
    )
    grouped["roi"] = round(grouped["revenue"] / grouped["marketing_spend"], 2)
    grouped.rename(columns={date_col: "month"}, inplace=True)
    return grouped[["month", "revenue", "marketing_spend", "roi"]].to_dict(orient="records")


# Map chart type strings → handler functions.
# Routers look up the function here; they don't import individual helpers.
CHART_HANDLERS: dict = {
    "revenue-trend": get_chart_data_revenue_trend,
    "by-category": get_chart_data_by_category,
    "by-region": get_chart_data_by_region,
    "campaign-performance": get_chart_data_campaign_performance,
    "conversion-funnel": get_chart_data_conversion_funnel,
    "marketing-roi": get_chart_data_marketing_roi,
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_date_col(df: pd.DataFrame) -> str | None:
    """Return the first column whose name contains 'month' or 'date'."""
    return next((c for c in df.columns if c.lower() in ("month", "date")), None)


def _detect_date_range(df: pd.DataFrame) -> dict | None:
    """Try to detect a date/month column and return its min/max."""
    for col in df.columns:
        if "date" in col.lower() or "month" in col.lower():
            try:
                dates = pd.to_datetime(df[col])
                return {
                    "column": col,
                    "min": str(dates.min().date()),
                    "max": str(dates.max().date()),
                }
            except (ValueError, TypeError):
                pass
            break
    return None
