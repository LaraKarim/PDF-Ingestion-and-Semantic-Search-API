from fastapi import APIRouter, UploadFile, File
from app.services.pdf_processor import process_pdf
from app.services.embedder import generate_embeddings
from app.models.vector_db import save_embeddings

router = APIRouter()

@router.post("/")
async def ingest(input: UploadFile = File(...)):
    text_chunks = process_pdf(input)
    embeddings = generate_embeddings(text_chunks)
    save_embeddings(input.filename, text_chunks, embeddings)
    return {"message": f"Successfully ingested {input.filename}", "files": [input.filename]}
