from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

# SQLite: check_same_thread=False. Postgres (e.g. Neon): optional sslmode in URL (?sslmode=require)
_connect_args = {}
if "sqlite" in settings.database_url:
    _connect_args["check_same_thread"] = False
# Neon and other serverless Postgres often need sslmode=require; set in DATABASE_URL if required
engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,  # verify connections (helps with Neon/serverless timeouts)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
