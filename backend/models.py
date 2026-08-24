# models.py
# This file defines the database tables (models) for Users, Files, and Jobs.

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base  # Import Base from database.py
from fastapi_users.db import BaseUserDatabase  # ✅ Use BaseUserDatabase instead

# ============================================
# USER MODEL
# ============================================
class User(BaseUserDatabase, Base):
    """
    User table - stores user accounts
    Inherits from BaseUserDatabase (provides email, password, etc.)
    """
    __tablename__ = "users"  # Table name in database
    
    id = Column(Integer, primary_key=True, index=True)  # Unique ID
    jobs = relationship("Job", back_populates="user")  # Link to jobs
    files = relationship("File", back_populates="user")  # Link to files

# ============================================
# FILE MODEL
# ============================================
class File(Base):
    """
    File table - stores uploaded image information
    """
    __tablename__ = "files"  # Table name in database
    
    id = Column(Integer, primary_key=True, index=True)  # Unique ID
    user_id = Column(Integer, ForeignKey("users.id"))  # Link to user
    filename = Column(String, nullable=False)  # Original filename
    path = Column(String, nullable=False)  # Path to file on disk
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Upload time
    user = relationship("User", back_populates="files")  # Link back to user

# ============================================
# JOB MODEL
# ============================================
class Job(Base):
    """
    Job table - stores segmentation job information
    """
    __tablename__ = "jobs"  # Table name in database
    
    id = Column(String, primary_key=True, index=True)  # Job ID (UUID)
    user_id = Column(Integer, ForeignKey("users.id"))  # Link to user
    file_id = Column(Integer, ForeignKey("files.id"))  # Link to file
    status = Column(String, default="pending")  # Job status (pending/processing/completed)
    result_path = Column(String, nullable=True)  # Path to result file
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Job creation time
    user = relationship("User", back_populates="jobs")  # Link back to user
    file = relationship("File")  # Link to file