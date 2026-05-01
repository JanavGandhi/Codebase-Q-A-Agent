from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from src.ingestion.chunker import CodeChunk

EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # 90MB, runs locally, great for code
CHROMA_PATH     = "chroma_db"           # folder ChromaDB will create on disk
COLLECTION_NAME = "codebase"


def get_chroma_collection():
    """Return (or create) the persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}   # use cosine similarity, not euclidean
    )
    return collection


def embed_and_store(chunks: list[CodeChunk]) -> None:
    """
    Embed every chunk and persist to ChromaDB.
    Safe to re-run — skips chunks that are already stored.
    """
    print(f"  Loading embedding model: {EMBEDDING_MODEL}")
    model      = SentenceTransformer(EMBEDDING_MODEL)
    collection = get_chroma_collection()

    # Check how many are already stored so we don't duplicate
    existing   = collection.count()
    if existing > 0:
        print(f"  Collection already has {existing} chunks — skipping re-embed.")
        print("  (Delete the chroma_db/ folder to force a fresh embed.)")
        return

    print(f"  Embedding {len(chunks)} chunks — this takes ~30s the first time...")

    texts     = [chunk.text     for chunk in chunks]
    ids       = [f"chunk_{i}"   for i in range(len(chunks))]
    metadatas = [
        {
            "name":     chunk.name,
            "type":     chunk.type,
            "filepath": chunk.filepath,
            "start":    chunk.start,
            "end":      chunk.end,
        }
        for chunk in chunks
    ]

    # Embed all texts in one batch (fast)
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids        = ids,
        documents  = texts,
        embeddings = embeddings,
        metadatas  = metadatas,
    )

    print(f"  Stored {collection.count()} chunks in ChromaDB at ./{CHROMA_PATH}/")