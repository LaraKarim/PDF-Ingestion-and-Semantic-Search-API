from sentence_transformers import SentenceTransformer
from app.core.config import EMBEDDING_MODEL

# Load model once
model = SentenceTransformer(EMBEDDING_MODEL)

def generate_embeddings(text_chunks):
    """
    Generate embeddings for a list of text chunks.
    """
    embeddings = model.encode(text_chunks, show_progress_bar=False, convert_to_numpy=True)
    return embeddings
