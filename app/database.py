from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Creates the connection engine to PostgreSQL using the URL validated by Pydantic
engine  = create_engine(settings.DATABASE_URL)

# Creates a session factory. Each request will have its own isolated session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our models (tables) will inherit
Base = declarative_base()

