from fastapi import APIRouter, HTTPException
from app.schema.schema import SearchQuery, SearchResponse
from app.services.embedding import generate_embeddings
from app.db.vector_db import search_top_k
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SearchResponse)
async def search(query: SearchQuery):
    # Check if the query is empty or only whitespace
    if not query.query or not query.query.strip():
        logger.warning("Received empty search query")
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    logger.info(f"Received search query: {query.query}")

    # Generate query embedding
    query_vector = generate_embeddings([query.query])[0]

    # Retrieve top-k similar chunks
    results = search_top_k(query_vector)
    logger.info(f"Returning {len(results)} results")
    return {"results": results}
