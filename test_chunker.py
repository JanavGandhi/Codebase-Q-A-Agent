from src.ingestion.chunker import chunk_repository

print("Running chunker...")
chunks = chunk_repository("repos/requests")

for chunk in chunks[:3]:
    print(f"\n{'='*60}")
    print(f"Name:  {chunk.name}  ({chunk.type})")
    print(f"File:  {chunk.filepath}  [lines {chunk.start}–{chunk.end}]")
    print(f"Preview:\n{chunk.text[:300]}")
    print("...")