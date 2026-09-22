from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=(settings.ENVIRONMENT == "development")
    )
    # Test connection creation / driver loading
    engine.connect().close()
except Exception:
    # Local fallback engine for testing/environments without PostgreSQL
    engine = create_engine(
        "sqlite:///./sentinel_dev.db",
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
