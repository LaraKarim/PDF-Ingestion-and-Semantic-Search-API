import pdfplumber
from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP
import asyncio

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)


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

        chunks = text_splitter.split_text(all_text)

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
