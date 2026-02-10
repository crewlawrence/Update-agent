from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db import engine, Base
from app.api import auth, quickbooks, clients, pending_updates, agent_run
import app.models  # noqa: F401 - ensure all models (including RefreshToken) are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    # shutdown if needed


app = FastAPI(
    title="Client Update Agent",
    description="Multi-tenant AI agent for buyer client updates from QuickBooks",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(quickbooks.router)
app.include_router(clients.router)
app.include_router(pending_updates.router)
app.include_router(agent_run.router)


@app.get("/health")
def health():
    return {"status": "ok"}
