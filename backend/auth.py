# auth.py
# Minimal authentication setup for FastAPI Users

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi_users import FastAPIUsers
from fastapi_users.db import BaseUserDatabase
from models import User
from database import get_db
from sqlalchemy.orm import Session

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependency to get the user database
async def get_user_db(db: Session = Depends(get_db)):
    yield BaseUserDatabase(db, User)

# FastAPI Users instance (minimal setup)
fastapi_users = FastAPIUsers(get_user_db, [oauth2_scheme])