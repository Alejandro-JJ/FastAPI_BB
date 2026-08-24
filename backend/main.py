from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Depends
from pathlib import Path
import shutil
from tasks import celery_app, run_segmentation_task
import uuid
import json

# ✅ FIXED IMPORTS
from database import get_db, engine, Base
from models import User, File, Job
from auth import fastapi_users
from fastapi_users.router import get_register_router, get_auth_router, get_users_router
from fastapi_users.router.common import ErrorCode, ErrorModel

app = FastAPI(title="Test API Alejandro")

# ✅ CREATE DATABASE TABLES ON STARTUP
Base.metadata.create_all(bind=engine)

# ✅ ADD AUTHENTICATION ROUTERS (FIXED)
app.include_router(get_register_router(fastapi_users, ErrorModel), prefix="/auth", tags=["auth"])
app.include_router(get_auth_router(fastapi_users, ErrorModel), prefix="/auth", tags=["auth"])
app.include_router(get_users_router(fastapi_users, ErrorModel), prefix="/auth", tags=["auth"])

# Create directories for upload and download
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")

UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# In-memory storage for uploaded files (replace with DB later)
uploaded_files = {}  # file_id -> {path: str, filename: str}

"""
UPLOAD TAB
"""
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db = Depends(get_db),
    user = Depends(fastapi_users.current_user(active=True))
):
    # save uploaded file to uploads folder
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ STORE FILE IN DATABASE
    db_file = File(
        filename=file.filename,
        path=str(file_path),
        user_id=user.id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Once file has been uploaded, generate unique JobID
    job_id = str(uuid.uuid4())

    # Send task to celery, automatically after upload
    task = celery_app.send_task(
        "tasks.run_segmentation_task", # ADDED TASKS
        args = [str(file_path), {"threshold":0.5, "min_size": 100}], # the dict of arguments
        task_id = job_id
    )
    
    return {
        "filename": file.filename,
        "size": file.size, 
        "file_id": db_file.id,  # ✅ Return database file_id
        "status": "processing",
        "message" : f"Job {job_id} started. Check status at /job/{job_id}"
    }

"""
RUN TAB
"""
@app.post("/run")
async def run_segmentation(
    file_id: int = Body(...),  # ✅ Changed from str to int
    params: dict = Body(...),
    db = Depends(get_db),
    user = Depends(fastapi_users.current_user(active=True))
):
    # ✅ CHECK FILE EXISTS AND BELONGS TO USER
    db_file = db.query(File).filter(File.id == file_id).first()
    if not db_file or db_file.user_id != user.id:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = db_file.path  # ✅ Get path from database

    # Generate job ID
    job_id = str(uuid.uuid4())

    # ✅ STORE JOB IN DATABASE
    db_job = Job(
        id=job_id,
        user_id=user.id,
        file_id=file_id,
        status="pending"
    )
    db.add(db_job)
    db.commit()

    # Send task to Celery
    task = celery_app.send_task(
        "tasks.run_segmentation_task", # ADDED TASKS
        args=[file_path, params],
        task_id=job_id
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Segmentation started for file {file_id}"
    }


@app.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    db = Depends(get_db),
    user = Depends(fastapi_users.current_user(active=True))
):
    # ✅ CHECK JOB EXISTS AND BELONGS TO USER
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job or db_job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get task result from celery
    task = celery_app.AsyncResult(job_id)

    if task.ready():
        # ✅ UPDATE JOB STATUS IN DATABASE
        db_job.status = "completed"
        db_job.result_path = task.result.get("result_path")
        db.commit()
        return{
            "job_id": job_id,
            "status": "DONE",
            "results": task.result
        }
    else:
        return{
            "job_id": job_id,
            "status": "processing",
        }