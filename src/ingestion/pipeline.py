# src/ingestion/pipeline.py
from src.ingestion.chunker import chunk_repository
from src.ingestion.embedder import embed_and_store


def build_index(repo_path: str) -> None:
    """
    Full ingestion pipeline: chunk a repo and store embeddings in ChromaDB.
    Safe to re-run — skips embedding if index already exists.
    """
    print(f"\n Building index for: {repo_path}")
    print("-" * 40)

    print("[1/2] Chunking repository...")
    chunks = chunk_repository(repo_path)

    print("\n[2/2] Embedding and storing chunks...")
    embed_and_store(chunks)

    print("\n Index ready.\n")