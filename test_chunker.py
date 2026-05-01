# test_chunker.py
from src.retrieval.agent import ask

question = "How does session cookie handling work?"
print(f"Question: {question}\n")
print("=" * 60)

result = ask(question)

print(f"\nAnswer:\n{result['answer']}")

print(f"\n{'=' * 60}")
print("Sources used:")
for chunk in result["sources"]:
    print(f"  - {chunk['name']} ({chunk['filepath']} lines {chunk['start']}–{chunk['end']}) [similarity: {chunk['similarity']}]")