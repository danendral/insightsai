"""
main.py - Application Entry Point

WHAT THIS FILE SHOULD DO (and nothing more):
  1. Create the FastAPI app instance
  2. Add middleware (CORS, auth, logging — things that wrap every request)
  3. Register routers
  4. Optionally add startup/shutdown lifecycle hooks

WHAT THIS FILE SHOULD NOT DO:
  - Define Pydantic models       →  models/schemas.py
  - Implement business logic     →  services/
  - Define route handlers        →  routers/
  - Read environment variables   →  core/config.py

BEFORE vs AFTER:
  Before refactor: main.py was 423 lines doing everything.
  After refactor:  main.py is ~60 lines of pure wiring.

  This is the Single Responsibility Principle in practice.
  Every file has one reason to change:
    - main.py changes when you add/remove a router or middleware
    - routers/*.py change when you add/remove endpoints
    - services/*.py change when business logic changes
    - models/schemas.py changes when your API contract changes
    - core/config.py changes when you add config values

APP LIFESPAN (startup/shutdown):
  The @asynccontextmanager pattern is FastAPI's modern way to run code
  at startup and shutdown (replaces the old @app.on_event decorators).
  We use it here to ensure the upload directory exists before the first
  request arrives, without putting setup code in a route handler.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from routers import charts, data, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup (before `yield`) and once at shutdown (after `yield`).

    Startup is the right place to:
      - Create directories
      - Warm up database connections (Stage 2)
      - Load ML models into memory
      - Validate external service connectivity
    """
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown logic goes here (e.g., close DB connections in Stage 2)


app = FastAPI(
    title="InsightsAI API",
    description="Sales & Marketing Analytics API powered by Claude",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
# CORS must be registered BEFORE routers so it wraps every route.
# The React dev server runs on 5173; the API runs on 8000.
# Browsers block cross-origin requests by default — this lifts that restriction
# for our known frontend origin only.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
# prefix="/api" means every route in data.router and query.router
# automatically gets the /api prefix — no need to write it in each router.
# tags=[...] groups endpoints in the /docs Swagger UI.
# ---------------------------------------------------------------------------
app.include_router(data.router, prefix="/api", tags=["Data"])
app.include_router(charts.router, prefix="/api", tags=["Charts"])
app.include_router(query.router, prefix="/api", tags=["Query"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    """Basic health check — confirms the API is running."""
    return {"message": "InsightsAI API is running. Visit /docs for API documentation."}
