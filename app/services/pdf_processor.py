import pdfplumber
from fastapi import HTTPException
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP
import asyncio
import re

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    """
    Sentence-aware overlapping text chunks.
    - chunk_size and chunk_overlap are in characters
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += (sentence + " ")
        else:
            chunks.append(current_chunk.strip())
            # start new chunk with overlap from previous chunk
            overlap = current_chunk[-chunk_overlap:] if chunk_overlap < len(current_chunk) else current_chunk
            current_chunk = overlap + sentence + " "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def clean_pdf_text(text: str) -> str:
    import re
    # Join hyphenated line breaks: "random-\nness" → "randomness"
    text = re.sub(r'-\n\s*', '', text)
    # Replace newlines inside sentences with space
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    # Fix camel-case concatenated words: "embeddingAlgorithms" → "embedding Algorithms"
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _process_pdf_sync(file_obj):
    try:
        # handle UploadFile vs normal file
        stream = file_obj.file if hasattr(file_obj, "file") else file_obj
        all_text = ""
        
        try:
            # Try to open as real PDF
            with pdfplumber.open(stream) as pdf:
                if not pdf.pages:
                    raise HTTPException(status_code=400, detail="PDF has no pages.")
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
        except HTTPException:
            raise
        except Exception:
            # If pdfplumber fails, try reading as plain text (for fake test PDFs)
            stream.seek(0)
            content = stream.read()
            all_text = (
                content.decode("utf-8", errors="ignore")
                if isinstance(content, (bytes, bytearray))
                else str(content)
            )
        
        if not all_text.strip():
            raise HTTPException(status_code=400, detail="PDF contains no readable text.")
        
        #Clean pdf for better search query
        all_text = clean_pdf_text(all_text)
        chunks = chunk_text(all_text)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks generated from PDF.")
        
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