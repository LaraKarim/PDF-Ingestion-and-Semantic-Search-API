from numpy import dot
from numpy.linalg import norm
from app.core.config import TOP_K


db_store = []

def save_embeddings(doc_name, chunks_with_ids, embeddings):
    for i, chunk in enumerate(chunks_with_ids):
        db_store.append({   #attach metadata to it
            "document": doc_name,
            "chunk_id": chunk["chunk_id"],
            "content": chunk["text"],
            "vector": embeddings[i]
        })

def search_top_k(query_vector, k=TOP_K):
    """
    Return top-k chunks based on cosine similarity.
    """
    results = []
    for entry in db_store:
        score = dot(query_vector, entry["vector"]) / (norm(query_vector) * norm(entry["vector"]))
        results.append({**entry, "score": float(score)})

    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    top_k = [{"document": r["document"], "score": r["score"], "content": r["content"]} for r in results[:k]]
    return top_k
