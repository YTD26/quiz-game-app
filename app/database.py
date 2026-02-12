"""Database configuratie en sessie management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL uit environment of default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quiz_app.db")

# Create engine met SQLite optimalisaties
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set True voor SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class voor models
Base = declarative_base()


def get_db():
    """Dependency voor database sessies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialiseer database en maak alle tabellen."""
    from app import models  # Import hier om circular imports te voorkomen
    Base.metadata.create_all(bind=engine)
    print("✅ Database tabellen aangemaakt")