from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.db_migration import run_migrations
from app.routers import auth, scans, dashboard, admin
from app.services import classifier_service

# Create tables if they don't exist yet (fine for SQLite / small deployments;
# swap for Alembic migrations if you move to Postgres in production).
Base.metadata.create_all(bind=engine)

# Add columns introduced after the DB was first created (SQLite only, no-op
# when everything is already present).
run_migrations(engine)

app = FastAPI(
    title="Legal Metrology Compliance API",
    description=(
        "Backend for the Software System to check compliance of Packaged "
        "Commodities under the Legal Metrology (Packaged Commodities) Rules, 2011 "
        "(SIH Problem Statement 26034)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images / generated reports so the frontend can render them
# directly, e.g. <img src="http://localhost:8000/files/uploads/xxx.jpg" />
app.mount("/files/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/files/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")

app.include_router(auth.router)
app.include_router(scans.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Legal Metrology Compliance API"}


@app.on_event("startup")
def warmup_ml():
    """Load the label classifier in the background so the first scan is fast."""
    classifier_service.warmup_async()


@app.get("/api/health")
def health():
    return {"status": "healthy"}
