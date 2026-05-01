# src/retrieval/retriever.py
from sentence_transformers import SentenceTransformer
from src.ingestion.embedder import get_chroma_collection, EMBEDDING_MODEL

TOP_K = 5   # number of chunks to retrieve per query


def retrieve(query: str) -> list[dict]:
    """
    Embed the query and return the top-k most similar code chunks.
    Each result is a dict with keys: text, name, filepath, start, end.
    """
    model      = SentenceTransformer(EMBEDDING_MODEL)
    collection = get_chroma_collection()

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings = [query_embedding],
        n_results        = TOP_K,
        include          = ["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":       doc,
            "name":       meta["name"],
            "type":       meta["type"],
            "filepath":   meta["filepath"],
            "start":      meta["start"],
            "end":        meta["end"],
            "similarity": round(1 - dist, 3),   # cosine distance → similarity score
        })

    return chunks