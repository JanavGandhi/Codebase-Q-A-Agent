# src/retrieval/agent.py
import os
from groq import Groq
from dotenv import load_dotenv
from src.retrieval.retriever import retrieve

load_dotenv()

GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are an expert code assistant that answers questions about a Python codebase.

You will be given relevant source code chunks retrieved from the codebase, followed by a user question.

Rules:
- Answer using ONLY the provided source code. Do not guess or use outside knowledge.
- Always mention which file and function your answer comes from.
- If the provided chunks do not contain enough information, say so honestly.
- Be concise but technically precise.
- Format code snippets with markdown code blocks.
"""

EXPLAIN_LINE_PROMPT = """You are an expert Python engineer and teacher.

A user is looking at a specific line or snippet of code and wants to understand it deeply.
You will be given:
1. The exact code snippet they are asking about
2. The file it comes from
3. Surrounding context from the codebase retrieved automatically

Explain clearly:
- What this code does, line by line if needed
- Why it exists and its purpose in the bigger picture
- Any important Python concepts it uses e.g. argparse, dataclasses, decorators

Be educational but precise. Use markdown formatting.
"""

EXPLAIN_FILE_PROMPT = """You are an expert Python engineer.

A user wants to understand what a specific file does in a codebase.
You will be given retrieved code chunks from that file.

Provide:
- A one-paragraph summary of what this file does
- A breakdown of each major function/class and its role
- How this file fits into the overall project architecture

Use markdown formatting with headers.
"""


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a readable context block for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"--- Chunk {i}: {chunk['name']} "
            f"({chunk['filepath']}, lines {chunk['start']}–{chunk['end']}) "
            f"[similarity: {chunk['similarity']}] ---\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(parts)


def ask(question: str) -> dict:
    """General Q&A: retrieve relevant chunks and answer the question."""
    client  = Groq(api_key=os.getenv("GROQ_API_KEY"))
    chunks  = retrieve(question)
    context = build_context(chunks)

    user_message = f"""Here are the most relevant code chunks from the codebase:

{context}

Question: {question}"""

    response = client.chat.completions.create(
        model       = GROQ_MODEL,
        messages    = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,
    )

    return {
        "question": question,
        "answer":   response.choices[0].message.content,
        "sources":  chunks,
    }


def explain_line(snippet: str, filepath: str) -> dict:
    """Explain a specific line or snippet of code in context."""
    client  = Groq(api_key=os.getenv("GROQ_API_KEY"))
    chunks  = retrieve(snippet)
    context = build_context(chunks)

    user_message = f"""The user is asking about this specific code snippet from `{filepath}`:

```python
{snippet}
```

Here is related context retrieved from the codebase:
{context}

Please explain what this code does, why it exists, and any important concepts it uses."""

    response = client.chat.completions.create(
        model       = GROQ_MODEL,
        messages    = [
            {"role": "system", "content": EXPLAIN_LINE_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,
    )

    return {
        "snippet":  snippet,
        "filepath": filepath,
        "answer":   response.choices[0].message.content,
        "sources":  chunks,
    }


def explain_file(filepath: str) -> dict:
    """Explain what an entire file does by retrieving all its chunks."""
    from src.ingestion.embedder import get_chroma_collection

    client     = Groq(api_key=os.getenv("GROQ_API_KEY"))
    collection = get_chroma_collection()

    results = collection.get(
        where   = {"filepath": filepath},
        include = ["documents", "metadatas"]
    )

    if not results["documents"]:
        return {
            "filepath": filepath,
            "answer":   f"No indexed chunks found for `{filepath}`. Make sure you've run `ingest` first.",
            "sources":  []
        }

    chunks = []
    for doc, meta in zip(results["documents"], results["metadatas"]):
        chunks.append({
            "text":     doc,
            "name":     meta["name"],
            "filepath": meta["filepath"],
            "start":    meta["start"],
            "end":      meta["end"],
        })

    context = "\n\n".join(
        f"--- {c['name']} (lines {c['start']}–{c['end']}) ---\n{c['text']}"
        for c in chunks
    )

    user_message = f"""Please explain the file `{filepath}` based on these extracted chunks:

{context}"""

    response = client.chat.completions.create(
        model       = GROQ_MODEL,
        messages    = [
            {"role": "system", "content": EXPLAIN_FILE_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,
    )

    return {
        "filepath": filepath,
        "answer":   response.choices[0].message.content,
        "sources":  chunks,
    }