# database.py
# This file sets up the connection to the SQLite database using SQLAlchemy.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL. 
# "sqlite:///./database.db" creates a file named database.db in the current directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"

# Create the engine. 
# connect_args={"check_same_thread": False} is required for SQLite in FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create the session factory. 
# This is used to create database sessions for each request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the Base class. 
# All database models will inherit from this class.
Base = declarative_base()

# Dependency function to get a database session.
# This is used in FastAPI endpoints to access the database.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
