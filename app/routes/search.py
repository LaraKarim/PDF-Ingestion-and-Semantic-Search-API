from fastapi import APIRouter
from pydantic import BaseModel
from app.services.embedder import generate_embeddings
from app.models.vector_db import search_top_k

router = APIRouter()

class SearchQuery(BaseModel):
    query: str

@router.post("/")
async def search(query: SearchQuery):
    query_vector = generate_embeddings([query.query])
    results = search_top_k(query_vector, k=5)
    return {"results": results}
