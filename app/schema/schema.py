#To validate requests and responses 

from pydantic import BaseModel
from typing import List

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    document: str
    score: float
    content: str

class SearchResponse(BaseModel):
    results: List[SearchResult]
