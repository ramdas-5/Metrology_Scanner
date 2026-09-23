import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import crud, database
from app.config import settings
from app.routers import auth, scans, dashboard, admin
from app.services import classifier_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown.

    Startup is deliberately fault tolerant: if MongoDB (Atlas) is briefly
    unreachable the API still comes up and reports the problem through
    /api/health and the admin System Health widget, instead of crash-looping
    the whole deployment.
    """
    if database.init_db():
        try:
            crud.ensure_default_admin()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not ensure the bootstrap admin account: %s", exc)
    classifier_service.warmup_async()
    yield
    database.close()


app = FastAPI(
    title="Legal Metrology Compliance API",
    description=(
        "Backend for the Software System to check compliance of Packaged "
        "Commodities under the Legal Metrology (Packaged Commodities) Rules, 2011 "
        "(SIH Problem Statement 26034)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Allow every *.vercel.app origin (production AND the per-branch preview
    # deployments Vercel generates) so the frontend never breaks because a new
    # preview URL was created. Set CORS_ALLOW_VERCEL=false to lock it down.
    allow_origin_regex=r"https://[A-Za-z0-9-]+\.vercel\.app" if settings.CORS_ALLOW_VERCEL else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images / generated reports so the frontend can render them
# directly, e.g. <img src="https://api.example.com/files/uploads/xxx.jpg" />
app.mount("/files/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/files/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")

app.include_router(auth.router)
app.include_router(scans.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Legal Metrology Compliance API"}


@app.get("/api/health")
def health():
    """Render / uptime health probe - also reports the database status."""
    db_ok = database.ping()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "classifier": "enabled" if settings.CLASSIFIER_ENABLED else "disabled",
    }
