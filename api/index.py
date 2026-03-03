import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_crons import Crons
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.routes.registrations import router as registrations_router
from api.health_checks import check_db, check_smtp
from api.keep_alive import run_keep_alive
from api.rate_limit import limiter
from api.settings import get_settings


settings = get_settings()
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="COM/VERGE Registration API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

crons = Crons(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "COM/VERGE Registration API"}


@app.get("/health/extended")
async def health_extended():
    db = await check_db()
    smtp = await check_smtp()
    status = "healthy" if db.get("ok") and smtp.get("ok") else "degraded"
    return {"status": status, "db": db, "smtp": smtp}


app.include_router(registrations_router, prefix="/api", tags=["registrations"])


@app.get("/api/keep-alive")
async def keep_alive():
    try:
        await run_keep_alive()
    except Exception:
        logging.getLogger(__name__).exception("Keep-alive query failed")
    return {"status": "alive"}


@crons.cron("0 */2 * * *")
async def keep_alive_job():
    await keep_alive()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
