import time

from fastapi import FastAPI, Request
from sqlalchemy import text

from app.api import auth, comparables, factors, reports, users, valuations
from app.core.config import get_settings
from app.core.database import engine

settings = get_settings()

app = FastAPI(
    title="ReVal 房地产估价系统 API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.middleware("http")
async def no_store_cache(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/api/health", tags=["system"])
def health():
    started = time.perf_counter()
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": db_ok,
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "env": settings.app_env,
    }


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(comparables.router, prefix="/api/comparables", tags=["comparables"])
app.include_router(valuations.router, prefix="/api/valuations", tags=["valuations"])
app.include_router(factors.router, prefix="/api/factors", tags=["factors"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
