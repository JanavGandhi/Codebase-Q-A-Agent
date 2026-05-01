from src.ingestion.chunker import chunk_repository
from src.ingestion.embedder import embed_and_store, get_chroma_collection

print("Step 1: Chunking repository...")
chunks = chunk_repository("repos/requests")

print("\nStep 2: Embedding and storing chunks...")
embed_and_store(chunks)

print("\nStep 3: Verifying ChromaDB...")
collection = get_chroma_collection()
print(f"  Total chunks in DB: {collection.count()}")

# Peek at one stored item
result = collection.peek(limit=1)
print(f"\n  Sample stored chunk:")
print(f"  ID:       {result['ids'][0]}")
print(f"  Name:     {result['metadatas'][0]['name']}")
print(f"  File:     {result['metadatas'][0]['filepath']}")
print(f"  Preview:  {result['documents'][0][:150]}...")