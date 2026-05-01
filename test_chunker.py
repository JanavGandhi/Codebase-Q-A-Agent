from src.retrieval.retriever import retrieve

query = "how does session cookie handling work?"
print(f"Query: '{query}'\n")

results = retrieve(query)

for i, chunk in enumerate(results, 1):
    print(f"Result {i} — {chunk['name']} ({chunk['filepath']} lines {chunk['start']}–{chunk['end']})")
    print(f"Similarity: {chunk['similarity']}")
    print(f"Preview: {chunk['text'][:200]}")
    print()