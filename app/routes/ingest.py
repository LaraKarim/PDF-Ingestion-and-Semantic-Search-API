from fastapi import APIRouter, UploadFile, File, Form, HTTPException
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
semaphore = asyncio.Semaphore(3)
SEM_TIMEOUT = 10


async def handle_file(name: str, file_obj):
    """
    Handle processing, embedding, and saving for a single PDF file.
    """
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"{name} is not a PDF.")

    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=SEM_TIMEOUT)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=429, detail="Server busy, try again later.")

    try:
        # --- Step 1: PDF processing (async already wraps sync) ---
        chunks = await process_pdf(file_obj)
        if not chunks:
            raise HTTPException(status_code=400, detail=f"{name} has no readable text.")

        texts = [c["text"] for c in chunks]

        # --- Step 2: Generate embeddings (CPU-bound) ---
        embeddings = await asyncio.to_thread(generate_embeddings, texts)

        # --- Step 3: Save embeddings (DB/storage, possibly blocking) ---
        await asyncio.to_thread(save_embeddings, name, chunks, embeddings)

        logger.info(f"Ingested {name}")
        return name

    finally:
        semaphore.release()


@router.post("/")
async def ingest(
    input: Optional[List[UploadFile]] = File(None),
    input_path: Optional[str] = Form(None)
):
    if not input and not input_path:
        raise HTTPException(status_code=400, detail="No input provided.")

    tasks = []

    # ---------- files ----------
    if input:
        for f in input:
            # f.file is a SpooledTemporaryFile, safe to pass
            tasks.append(handle_file(f.filename, f.file))

    # ---------- directory ----------
    if input_path:
        if not os.path.isdir(input_path):
            raise HTTPException(status_code=400, detail="Invalid directory path.")

        for name in os.listdir(input_path):
            if name.lower().endswith(".pdf"):
                path = os.path.join(input_path, name)
                # Wrap in async to avoid blocking event loop
                tasks.append(
                    asyncio.to_thread(handle_file, name, open(path, "rb"))
                )

    if not tasks:
        raise HTTPException(status_code=400, detail="No valid PDFs found.")

    # Run all tasks concurrently with proper exception handling
    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed_files = []
    errors = []

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Error ingesting file: {r}")
            errors.append(str(r))
        else:
            processed_files.append(r)

    if not processed_files:
        raise HTTPException(status_code=400, detail="No PDFs were ingested successfully.")

    return {
        "message": f"Successfully ingested {len(processed_files)} PDF documents.",
        "files": processed_files,
        "errors": errors
    }
