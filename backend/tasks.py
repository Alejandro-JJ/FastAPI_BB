from celery import Celery
import time
import os
from pathlib import Path
from PIL import Image # NEW

# Get the absolute path of the current script
BASE_DIR = Path(__file__).parent  # This is the backend/ folder

# Create celery App -> requires redis running in background through docker in port 6379
celery_app = Celery(
    "tasks", 
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Define a task, here is where the heavy work is done
# Celery will be listening to redis in the background constantly
# and will fetch the next available job

@celery_app.task
def run_segmentation_task(file_path: str, params: dict):
    """
    Just a dummy task, properly implemented later
    """
    print(f"Starting segmentation...")

    # Simulate calculation, wait some time
    time.sleep(5)
    
    # Load the image
    img = Image.open(file_path)
    
    # Convert to grayscale (black and white)
    img_gray = img.convert('L')

    # Use absolute path to ensure file is saved in the correct location
    result_path = BASE_DIR / "results" / f"segmented_{Path(file_path).stem}.jpeg"
    result_path.parent.mkdir(exist_ok=True)

    # Save as a valid JPEG image
    img_gray.save(result_path, "JPEG")
    #with open(result_path, "w") as f:
    #    f.write(f"Segmented mask for {Path(file_path).stem}")
    
    print("Segmentation complete!")
    return {"status": "complete", "result_path": str(result_path)}