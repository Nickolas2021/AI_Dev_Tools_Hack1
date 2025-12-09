import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncAttrs, create_async_engine
from sqlalchemy.orm import DeclarativeBase


SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:password@localhost:5433/office_manager"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass