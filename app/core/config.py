import os
# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Text chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Vector DB
TOP_K = 3
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME = "pdf_documents"