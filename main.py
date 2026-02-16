import logging
from fastapi import FastAPI
from app.routes import ingest, search  

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("Including routers...")

app = FastAPI(title="PDF Ingestor & Semantic Search API")

app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(search.router, prefix="/search", tags=["Search"])
