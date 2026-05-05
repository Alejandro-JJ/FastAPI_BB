from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from pathlib import Path
import shutil
from tasks import celery_app, run_segmentation_task
import uuid
import json

app = FastAPI(title="Test API Alejandro")


#@app.get("/")
#def root():
#    return{"Hello": "World!"}

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
async def upload_file(file: UploadFile = File(...)):
    # save uploaded file to uploads folder
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Once file has been uploaded, generate unique JobID
    job_id = str(uuid.uuid4())

    # Store in memory (replace with DB later)
    uploaded_files[job_id] = {
        "path": str(file_path),
        "filename": file.filename
    }

    # Send task to celery, automatically after upload
    task = celery_app.send_task(
        "tasks.run_segmentation_task", # ADDED TASKS
        args = [str(file_path), {"threshold":0.5, "min_size": 100}], # the dict of arguments
        task_id = job_id
    )
    
    return {
        "filename": file.filename,
        "size": file.size, 
        #"message": f"File {file.filename} uploaded to {file_path}"
        "status": "processing",
        "message" : f"Job {job_id} started. Check status at /job/{job_id}"
    }

"""
RUN TAB
"""
@app.post("/run")
async def run_segmentation(
    file_id: str = Body(..., embed=True),
    params: dict = Body(..., embed=True)
):
    # Check if file exists
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = uploaded_files[file_id]["path"]

    # Generate job ID
    job_id = str(uuid.uuid4())

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
async def get_job_status(job_id: str):
    # Get task result from celery
    task = celery_app.AsyncResult(job_id)

    if task.ready():
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
