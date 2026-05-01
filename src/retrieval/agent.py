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
    """
    Full RAG pipeline: retrieve relevant chunks, build prompt, call Groq.
    Returns a dict with the answer and the source chunks used.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Step 1 — retrieve
    print("  Retrieving relevant chunks...")
    chunks = retrieve(question)

    # Step 2 — build prompt
    context = build_context(chunks)
    user_message = f"""Here are the most relevant code chunks from the codebase:

{context}

Question: {question}"""

    # Step 3 — call Groq
    print("  Calling Groq (Llama 3.1)...")
    response = client.chat.completions.create(
        model    = GROQ_MODEL,
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,   # low temperature = factual, consistent answers
    )

    answer = response.choices[0].message.content

    return {
        "question": question,
        "answer":   answer,
        "sources":  chunks,
    }