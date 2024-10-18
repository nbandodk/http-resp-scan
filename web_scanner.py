import os
import tempfile
import uuid
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import asyncio
import aiofiles
import time
import logging
from scan_enhanced import read_file, findit
from pydantic import ValidationError
from contextlib import asynccontextmanager

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    background_tasks = BackgroundTasks()
    background_tasks.add_task(cleanup_old_scans)
    yield
    # Shutdown
    # Add any cleanup code here if needed

app = FastAPI(lifespan=lifespan)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ScanResult(BaseModel):
    domain: str
    found_terms: List[str]

class ScanStatus(BaseModel):
    total: int
    completed: int
    results: List[dict]
    output_file: str

scan_status = {}

async def run_scan(scan_id: str, input_file: str, output_file: str, search_terms: List[str], port: Optional[int], append: Optional[str]):
    try:
        domains = read_file(input_file)
        total_domains = len(domains)
        scan_status[scan_id] = ScanStatus(total=total_domains, completed=0, results=[], output_file=output_file)

        for domain in domains:
            results = await findit(output_file, search_terms, port, append, domain)
            scan_status[scan_id].completed += 1
            if results:
                scan_status[scan_id].results.extend(results)
            
            # Update progress every 5 domains or when all domains are processed
            if scan_status[scan_id].completed % 5 == 0 or scan_status[scan_id].completed == total_domains:
                await asyncio.sleep(0)  # Allow other coroutines to run

        logger.info(f"Scan {scan_id} completed successfully")
    except Exception as e:
        logger.error(f"Error during scan {scan_id}: {str(e)}")
        raise

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.post("/scan")
async def scan(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    search_terms: str = Form(...), 
    port: Optional[str] = Form(None),
    append: Optional[str] = Form(None)
):
    try:
        logger.info(f"Received scan request. File: {file.filename}, Search terms: {search_terms}, Port: {port}, Append: {append}")

        if not file.filename:
            raise ValueError("No file uploaded")

        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_input:
            content = await file.read()
            if not content:
                raise ValueError("The uploaded file is empty")
            temp_input.write(content)
            input_file = temp_input.name

        output_file = tempfile.mktemp()

        # Parse search terms
        search_terms_list = [term.strip() for term in search_terms.split(',') if term.strip()]
        if not search_terms_list:
            raise ValueError("No valid search terms provided")

        # Parse port
        port_int = None
        if port:
            try:
                port_int = int(port)
            except ValueError:
                raise ValueError(f"Invalid port number: {port}")

        scan_id = str(uuid.uuid4())  # Generate a unique ID for each scan
        output_file = f"results_{scan_id}.txt"

        # Run the scan in the background
        background_tasks.add_task(run_scan, scan_id, input_file, output_file, search_terms_list, port_int, append)

        return JSONResponse(content={"message": "Scan started", "scan_id": scan_id}, status_code=202)

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=422)
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(content={"error": f"An unexpected error occurred: {str(e)}"}, status_code=500)

@app.get("/results/{scan_id}")
async def get_results(scan_id: str):
    if scan_id not in scan_status:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    status = scan_status[scan_id]
    return {
        "total": status.total,
        "completed": status.completed,
        "results": status.results[:10],  # Return only the first 10 results to avoid large payloads
        "is_complete": status.completed == status.total
    }

@app.get("/download/{scan_id}")
async def download_results(scan_id: str):
    if scan_id not in scan_status:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    output_file = scan_status[scan_id].output_file
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Results file not found")
    
    return FileResponse(output_file, filename=f"scan_results_{scan_id}.txt")

async def cleanup_old_scans():
    while True:
        current_time = time.time()
        for filename in os.listdir():
            if filename.startswith("results_") and filename.endswith(".txt"):
                file_path = os.path.join(os.getcwd(), filename)
                if current_time - os.path.getmtime(file_path) > 3600:  # 1 hour
                    os.remove(file_path)
        await asyncio.sleep(3600)  # Run every hour

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
