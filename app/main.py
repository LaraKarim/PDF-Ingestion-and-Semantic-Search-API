from fastapi import FastAPI
from app.routes import ingest, search

app = FastAPI(title="PDF Ingestion & Semantic Search API")

app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(search.router, prefix="/search", tags=["Search"])
