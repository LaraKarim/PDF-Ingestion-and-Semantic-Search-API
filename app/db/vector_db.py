import chromadb
import logging
from typing import List, Dict
from app.core.config import (
    TOP_K,
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    CHROMA_HOST,
    CHROMA_PORT,
)

logger = logging.getLogger(__name__) #to tell me which part is talking

# Initialize ChromaDB client (lazy singleton)
_client = None
_collection = None


def _get_client():
    """Initialize and return ChromaDB client: HttpClient if CHROMA_HOST/PORT set, else PersistentClient."""
    global _client
    if _client is None:
        try:
            if CHROMA_HOST and CHROMA_PORT:
                _client = chromadb.HttpClient(host=CHROMA_HOST, port=int(CHROMA_PORT))
                logger.info(f"Initialized ChromaDB HttpClient: {CHROMA_HOST}:{CHROMA_PORT}")
            else:
                _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
                logger.info(f"Initialized ChromaDB PersistentClient with path: {CHROMA_DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise
    return _client


def _get_collection():
    """Initialize and return the ChromaDB collection."""
    global _collection
    if _collection is None:
        try:
            client = _get_client()
           
            _collection = client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                metadata={"description": "PDF document chunks with embeddings"},
                # Default is L2 distance; I converted to similarity score in search_top_k
            )
            logger.info(f"Retrieved/created collection: {CHROMA_COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Failed to get/create collection: {str(e)}")
            raise
    return _collection


def save_embeddings(doc_name: str, chunks_with_ids: List[Dict], embeddings):
    """
    Save embeddings to ChromaDB collection.
    
    Args:
        doc_name: Name of the source PDF document
        chunks_with_ids: List of dicts with 'chunk_id' and 'text' keys
        embeddings: Numpy array of embeddings (one per chunk)
    """
    try:
        collection = _get_collection()
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embedding_list = []
        
        for i, chunk in enumerate(chunks_with_ids):
            # Create unique ID: filename_chunk_index
            chunk_id = f"{doc_name}_{chunk['chunk_id']}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append({
                "source": doc_name,
                "chunk_id": chunk["chunk_id"]
            })
            # Convert numpy array to list for ChromaDB
            embedding_list.append(embeddings[i].tolist())
        
        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embedding_list
        )
        
        logger.info(f"Saved {len(ids)} chunks from {doc_name} to ChromaDB")
        
    except Exception as e:
        logger.error(f"Error saving embeddings to ChromaDB: {str(e)}")
        raise


def search_top_k(query_vector, k: int = TOP_K) -> List[Dict]:
    """
    Search for top-k most similar chunks using ChromaDB query.
    
    Args:
        query_vector: Query embedding vector (numpy array or list)
        k: Number of results to return
        
    Returns:
        List of dicts with 'document', 'score', and 'content' keys
    """
    try:
        collection = _get_collection()
        
        # Convert query vector to list if it's a numpy array
        if hasattr(query_vector, 'tolist'):
            query_vector = query_vector.tolist()
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=k
        )
        
        # Format results to match expected schema
        # Convert ChromaDB distances to similarity scores (higher = more similar)
        formatted_results = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                # ChromaDB returns distances (lower = more similar)
                # Collection uses cosine space: distance = 1 - cosine_similarity
                # So: similarity_score = 1 - distance, clamped to [0, 1]
                distance = float(results['distances'][0][i]) if 'distances' in results and results['distances'] else 0.0
                similarity_score = max(0.0, min(1.0, 1.0 - distance))
                
                formatted_results.append({
                    "document": results['metadatas'][0][i].get("source", "unknown"),
                    "score": similarity_score,
                    "content": results['documents'][0][i]
                })
        
        logger.info(f"Found {len(formatted_results)} results for query")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching ChromaDB: {str(e)}")
        raise