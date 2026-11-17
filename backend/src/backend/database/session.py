
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend import config

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{config.DB_USER}:{config.DB_PASSWORD}@"
    f"{config.DB_HOST}:{config.DB_PORT}/"
    f"{config.DB_NAME}"
)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
