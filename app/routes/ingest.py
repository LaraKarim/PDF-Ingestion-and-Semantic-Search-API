from fastapi import APIRouter, UploadFile, File, HTTPException , Form 
from typing import List, Optional
import os
import logging
import asyncio

from app.services.pdf_processor import process_pdf
from app.services.embedding import generate_embeddings
from app.db.vector_db import save_embeddings

router = APIRouter()
logger = logging.getLogger(__name__)

# Limit number of concurrent PDF processing tasks
semaphore = asyncio.Semaphore(5)
SEM_TIMEOUT = 10


async def handle_file(name: str, file_obj):
    """
    Handle processing, embedding, and saving for a single PDF file.
    Returns a tuple: (success: bool, filename: str, error: str|None)
    """
    if not name.lower().endswith(".pdf"):
        error = f"{name} is not a PDF"
        logger.warning(error)
        return False, name, error

    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=SEM_TIMEOUT)   #acquire semaphore and wait if all taken for a certain time
    except asyncio.TimeoutError:
        error = f"{name}: Server busy, try again later"
        logger.error(error)
        return False, name, error

    try:
        # Step 1: Process PDF
        chunks = await process_pdf(file_obj)  #avoid event loop block
        if not chunks:
            error = f"{name}: PDF has no readable text"
            logger.error(error)
            return False, name, error

        texts = [c["text"] for c in chunks]

        # Step 2: Generate embeddings
        embeddings = await asyncio.to_thread(generate_embeddings, texts)  #do embeddings using thread pool

        # Step 3: Save embeddings
        await asyncio.to_thread(save_embeddings, name, chunks, embeddings)

        logger.info(f"Ingested {name}")
        return True, name, None

    except Exception as e:
        error = f"{name}: {str(e)}"
        logger.error(error)
        return False, name, error

    finally:
        semaphore.release()

@router.post("/ingest")
async def ingest(
    # Instead of UploadFile, accept the input as a plain string
    input: str = Form(...)
):
    """
    Accept one field 'input' (string).
    It can be:
      - a single PDF path
      - multiple PDF paths separated by commas
      - a directory path containing PDFs
    """

    tasks = []

    # Normalize input
    input_value = input.strip()

    # Check if string contains multiple comma‑separated paths
    paths = [p.strip() for p in input_value.split(",") if p.strip()]

    # If only one path and it's a directory
    if len(paths) == 1 and os.path.isdir(paths[0]):
        dir_path = paths[0]
        for name in os.listdir(dir_path):
            if name.lower().endswith(".pdf"):
                full = os.path.join(dir_path, name)
                tasks.append(handle_file(name, open(full, "rb")))

        if not tasks:
            raise HTTPException(status_code=400, detail="No PDFs found in directory")

    else:
        # Treat each given path as a PDF path
        for path in paths:
            # Validate extension
            if not path.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"Not a PDF: {path}")

            if not os.path.exists(path):
                raise HTTPException(status_code=400, detail=f"File not found: {path}")

            # Open file and schedule processing
            tasks.append(handle_file(os.path.basename(path), open(path, "rb")))

    # If nothing to do
    if not tasks:
        raise HTTPException(status_code=400, detail="No valid PDF input provided")

    # Run tasks concurrently
    results = await asyncio.gather(*tasks)

    processed_files = []
    errors = []

    for success, filename, error in results:
        if success:
            processed_files.append(filename)
        else:
            errors.append(error)

    if not processed_files:
        raise HTTPException(
            status_code=400,
            detail={"message": "No PDFs were ingested successfully", "errors": errors}
        )

    return {
        "message": f"Successfully ingested {len(processed_files)} PDF documents.",
        "files": processed_files,
        "errors": errors
    }