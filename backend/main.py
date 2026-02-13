"""
InsightsAI Backend - FastAPI Application

This is the main entry point for the backend API. FastAPI handles:
1. Receiving HTTP requests from the React frontend
2. Processing CSV data with pandas
3. Calling the Anthropic Claude API for natural language queries
4. Returning JSON responses

KEY CONCEPT - REST API Design:
- GET  /api/data          → Retrieve current dataset summary & stats
- GET  /api/data/raw      → Retrieve raw data rows (paginated)
- POST /api/upload        → Upload a new CSV file
- POST /api/query         → Ask a natural language question about the data
- GET  /api/sample        → Load the built-in sample dataset
- GET  /api/charts/{type} → Get pre-computed chart data

Each endpoint returns JSON that the React frontend consumes.
"""

import os
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="InsightsAI API",
    description="Sales & Marketing Analytics API powered by Claude",
    version="1.0.0",
)

# CORS (Cross-Origin Resource Sharing):
# The React dev server runs on port 5173, but our API runs on port 8000.
# Browsers block requests between different origins by default (security feature).
# CORS middleware tells the browser "it's okay, allow requests from these origins."
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory data store
# In production you'd use a database, but for a portfolio project storing the
# current dataset in memory keeps things simple.
# ---------------------------------------------------------------------------
current_df: pd.DataFrame | None = None

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_data" / "sales_data.csv"
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Pydantic models – these define the shape of request/response JSON.
# FastAPI automatically validates incoming data against these schemas.
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    question: str


class DataSummary(BaseModel):
    row_count: int
    column_count: int
    columns: list[str]
    numeric_columns: list[str]
    date_range: dict | None
    summary_stats: dict


class UploadResponse(BaseModel):
    message: str
    filename: str
    rows: int
    columns: int


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def compute_summary(df: pd.DataFrame) -> dict:
    """Compute summary statistics for the current dataset."""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Try to detect a date column for range info
    date_range = None
    for col in df.columns:
        if "date" in col.lower() or "month" in col.lower():
            try:
                dates = pd.to_datetime(df[col])
                date_range = {
                    "column": col,
                    "min": str(dates.min().date()),
                    "max": str(dates.max().date()),
                }
            except (ValueError, TypeError):
                pass
            break

    stats = {}
    for col in numeric_cols:
        stats[col] = {
            "mean": round(float(df[col].mean()), 2),
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
            "sum": round(float(df[col].sum()), 2),
        }

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "date_range": date_range,
        "summary_stats": stats,
    }


def get_chart_data_revenue_trend(df: pd.DataFrame) -> list[dict]:
    """Monthly revenue trend aggregated across all segments."""
    if "month" not in df.columns and "date" not in [c.lower() for c in df.columns]:
        return []

    date_col = next(
        (c for c in df.columns if c.lower() in ("month", "date")), None
    )
    if date_col is None:
        return []

    grouped = df.groupby(date_col).agg(
        revenue=("revenue", "sum"),
        customers=("customers", "sum"),
    ).reset_index()
    grouped = grouped.sort_values(date_col)
    grouped.rename(columns={date_col: "month"}, inplace=True)
    return grouped.to_dict(orient="records")


def get_chart_data_by_category(df: pd.DataFrame) -> list[dict]:
    """Revenue broken down by product category."""
    cat_col = next(
        (c for c in df.columns if "category" in c.lower() or "product" in c.lower()),
        None,
    )
    if cat_col is None or "revenue" not in df.columns:
        return []

    grouped = df.groupby(cat_col)["revenue"].sum().reset_index()
    grouped.columns = ["category", "revenue"]
    return grouped.to_dict(orient="records")


def get_chart_data_by_region(df: pd.DataFrame) -> list[dict]:
    """Revenue broken down by region."""
    region_col = next(
        (c for c in df.columns if "region" in c.lower()), None
    )
    if region_col is None or "revenue" not in df.columns:
        return []

    grouped = df.groupby(region_col)["revenue"].sum().reset_index()
    grouped.columns = ["region", "revenue"]
    return grouped.to_dict(orient="records")


def get_chart_data_campaign_performance(df: pd.DataFrame) -> list[dict]:
    """Marketing spend vs revenue by campaign."""
    campaign_col = next(
        (c for c in df.columns if "campaign" in c.lower()), None
    )
    if campaign_col is None:
        return []

    agg_cols = {}
    if "revenue" in df.columns:
        agg_cols["revenue"] = ("revenue", "sum")
    if "marketing_spend" in df.columns:
        agg_cols["marketing_spend"] = ("marketing_spend", "sum")
    if "leads_generated" in df.columns:
        agg_cols["leads_generated"] = ("leads_generated", "sum")

    if not agg_cols:
        return []

    grouped = df.groupby(campaign_col).agg(**agg_cols).reset_index()
    grouped.rename(columns={campaign_col: "campaign"}, inplace=True)
    return grouped.to_dict(orient="records")


def get_chart_data_conversion_funnel(df: pd.DataFrame) -> list[dict]:
    """Aggregated conversion funnel data."""
    metrics = {}
    if "leads_generated" in df.columns:
        metrics["Leads"] = int(df["leads_generated"].sum())
    if "deals_closed" in df.columns:
        metrics["Deals Closed"] = int(df["deals_closed"].sum())
    if "customers" in df.columns:
        metrics["Customers"] = int(df["customers"].sum())

    return [{"stage": k, "value": v} for k, v in metrics.items()]


def get_chart_data_marketing_roi(df: pd.DataFrame) -> list[dict]:
    """Monthly marketing ROI (revenue / spend)."""
    date_col = next(
        (c for c in df.columns if c.lower() in ("month", "date")), None
    )
    if date_col is None or "revenue" not in df.columns or "marketing_spend" not in df.columns:
        return []

    grouped = df.groupby(date_col).agg(
        revenue=("revenue", "sum"),
        marketing_spend=("marketing_spend", "sum"),
    ).reset_index()
    grouped = grouped.sort_values(date_col)
    grouped["roi"] = round(grouped["revenue"] / grouped["marketing_spend"], 2)
    grouped.rename(columns={date_col: "month"}, inplace=True)
    return grouped[["month", "revenue", "marketing_spend", "roi"]].to_dict(orient="records")


CHART_HANDLERS = {
    "revenue-trend": get_chart_data_revenue_trend,
    "by-category": get_chart_data_by_category,
    "by-region": get_chart_data_by_region,
    "campaign-performance": get_chart_data_campaign_performance,
    "conversion-funnel": get_chart_data_conversion_funnel,
    "marketing-roi": get_chart_data_marketing_roi,
}


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/sample")
def load_sample_data():
    """Load the built-in sample sales dataset."""
    global current_df
    current_df = pd.read_csv(SAMPLE_DATA_PATH)
    summary = compute_summary(current_df)
    return {"message": "Sample data loaded successfully", **summary}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file to analyze.

    HOW THIS WORKS:
    1. React sends a POST request with the file as FormData
    2. FastAPI receives it as an UploadFile object
    3. We validate the file type and size
    4. Parse it with pandas and store in memory
    """
    global current_df

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    try:
        from io import BytesIO
        current_df = pd.read_csv(BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    if current_df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Save a copy for reference
    save_path = UPLOAD_DIR / file.filename
    save_path.write_bytes(contents)

    return UploadResponse(
        message="File uploaded successfully",
        filename=file.filename,
        rows=len(current_df),
        columns=len(current_df.columns),
    )


@app.get("/api/data")
def get_data_summary():
    """Return summary statistics for the current dataset."""
    if current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded. Upload a CSV or load sample data first.")
    return compute_summary(current_df)


@app.get("/api/data/raw")
def get_raw_data(page: int = 1, page_size: int = 50):
    """Return paginated raw data rows."""
    if current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")

    start = (page - 1) * page_size
    end = start + page_size
    subset = current_df.iloc[start:end]

    return {
        "data": subset.to_dict(orient="records"),
        "total_rows": len(current_df),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(current_df) + page_size - 1) // page_size,
    }


@app.get("/api/charts/{chart_type}")
def get_chart_data(chart_type: str):
    """
    Return pre-computed chart data.

    Available chart types:
    - revenue-trend: Monthly revenue over time
    - by-category: Revenue by product category
    - by-region: Revenue by region
    - campaign-performance: Campaign spend vs revenue
    - conversion-funnel: Leads → Deals → Customers
    - marketing-roi: Monthly ROI (revenue / marketing spend)
    """
    if current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")

    handler = CHART_HANDLERS.get(chart_type)
    if handler is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown chart type '{chart_type}'. Available: {list(CHART_HANDLERS.keys())}",
        )

    return {"chart_type": chart_type, "data": handler(current_df)}


@app.post("/api/query", response_model=QueryResponse)
async def query_data(request: QueryRequest):
    """
    Natural language query endpoint.

    HOW THIS WORKS:
    1. User types a question like "What was the best performing month?"
    2. We send the question + a summary of the data to Claude
    3. Claude analyzes the data and returns an answer
    4. We send that answer back to the frontend

    This is the core AI feature — it turns raw data into conversational insights.
    """
    if current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Build a data context string for Claude.
    # We include column info, summary stats, and a sample of rows so Claude
    # understands the dataset without needing to see all of it.
    data_context = f"""Dataset Overview:
- Rows: {len(current_df)}, Columns: {len(current_df.columns)}
- Columns: {', '.join(current_df.columns.tolist())}

Summary Statistics:
{current_df.describe().to_string()}

First 10 rows:
{current_df.head(10).to_string()}

Last 5 rows:
{current_df.tail(5).to_string()}
"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a data analytics assistant for a sales & marketing analytics platform called InsightsAI.
You have access to the following dataset:

{data_context}

Answer this question about the data concisely and insightfully. Include specific numbers when relevant.
If the data doesn't contain enough information to answer, say so

Question: {request.question}""",
                }
            ],
        )
        answer = message.content[0].text
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid Anthropic API key")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI query failed: {e}")

    return QueryResponse(answer=answer, question=request.question)


@app.get("/")
def root():
    return {"message": "InsightsAI API is running. Visit /docs for API documentation."}
