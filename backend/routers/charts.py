"""
routers/charts.py - Chart Data Routes

PATH PARAMETERS:
  /api/charts/{chart_type} — the curly-brace syntax tells FastAPI to
  capture that segment of the URL as a function argument.

  FastAPI also validates it: if you declare chart_type: str, any string
  is accepted. You could use an Enum to restrict it at the framework level,
  but we do the check manually here to return a descriptive error message.

THIN ROUTER PRINCIPLE:
  This entire router is ~30 lines. All the real logic (pandas aggregations,
  column detection) lives in data_service.py. The router only:
    1. Checks that data is loaded
    2. Looks up the right handler function
    3. Returns the result
  That's it. When something breaks, you know immediately whether it's
  an HTTP issue (here) or a data issue (data_service.py).
"""

from fastapi import APIRouter, HTTPException

from models.schemas import ChartResponse
from services import data_service

router = APIRouter()


@router.get("/charts/{chart_type}", response_model=ChartResponse)
def get_chart_data(chart_type: str):
    """
    Return pre-computed chart data for the given chart type.

    Available chart types:
    - revenue-trend        Monthly revenue over time
    - by-category          Revenue by product category
    - by-region            Revenue by region
    - campaign-performance Campaign spend vs revenue
    - conversion-funnel    Leads → Deals → Customers
    - marketing-roi        Monthly ROI (revenue / marketing spend)
    """
    try:
        df = data_service.get_current_df()
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))

    handler = data_service.CHART_HANDLERS.get(chart_type)
    if handler is None:
        available = list(data_service.CHART_HANDLERS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown chart type '{chart_type}'. Available: {available}",
        )

    return ChartResponse(chart_type=chart_type, data=handler(df))
