import pdfplumber
from fastapi import HTTPException
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP
import asyncio

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    """
    Simple text splitter that splits text into overlapping chunks.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap if chunk_size > chunk_overlap else chunk_size

    return chunks


def _process_pdf_sync(file_obj):
    # Get underlying file object
    stream = file_obj.file if hasattr(file_obj, "file") else file_obj
    
    all_text = ""
    
    try:
        # Try the normal PDF extraction
        with pdfplumber.open(stream) as pdf:
            if not pdf.pages:
                # No pages → treat it as fallback
                raise Exception("PDF has no pages")

            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"

        # If no text extracted from PDF pages, fallback
        if not all_text.strip():
            raise Exception("No readable text in PDF")

    except Exception as e:
        # Fallback: treat content as raw text
        try:
            stream.seek(0)
        except Exception:
            pass

        content = stream.read()
        all_text = (
            content.decode("utf-8", errors="ignore")
            if isinstance(content, (bytes, bytearray))
            else str(content)
        )

        if not all_text.strip():
            # Still no text → meaningful error
            raise HTTPException(status_code=400, detail="Document contains no readable text.")

    # Now that we have text, chunk it
    chunks = chunk_text(all_text)

    return [
        {"chunk_id": i, "text": c}
        for i, c in enumerate(chunks)
    ]

async def process_pdf(file_obj):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _process_pdf_sync, file_obj)