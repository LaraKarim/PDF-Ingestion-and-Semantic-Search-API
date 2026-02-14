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
    try:
        # handle UploadFile vs normal file
        stream = file_obj.file if hasattr(file_obj, "file") else file_obj

        all_text = ""

        with pdfplumber.open(stream) as pdf:
            if not pdf.pages:
                raise HTTPException(status_code=400, detail="PDF has no pages.")

            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"

        if not all_text.strip():
            raise HTTPException(status_code=400, detail="PDF contains no readable text.")

        chunks = chunk_text(all_text)

        return [
            {"chunk_id": i, "text": c}
            for i, c in enumerate(chunks)
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")


async def process_pdf(file_obj):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _process_pdf_sync, file_obj)
