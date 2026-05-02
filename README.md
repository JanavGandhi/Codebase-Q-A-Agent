# Codebase Q&A Agent

> An AI-powered agent that reads, understands, and answers questions about any Python codebase — built from scratch using RAG (Retrieval-Augmented Generation), without relying on LangChain or any AI framework.



---

## What it does

Point this agent at any Python repository and ask it natural language questions. It reads the actual source code — not a summary, not training data — and answers with precision, citing the exact file and line number the answer came from.

```bash
# Index any Python repo
python main.py ingest repos/requests

# Ask a question
python main.py ask "How does session cookie handling work?"

# Explain a specific line
python main.py explain-line "ingest_parser = subparsers.add_parser('ingest')" "main.py"

# Explain an entire file
python main.py explain-file "src/retrieval/agent.py"
```

Or use the browser-based chat UI:

```bash
python app.py
# → open http://localhost:5000
```

---

## Demo

| Mode | What it does |
|---|---|
| **Ask anything** | General Q&A about the indexed codebase |
| **Explain file** | Full breakdown of a file — summary, functions, architecture role |
| **Explain snippet** | Paste any line or block and get a deep explanation with context |

---

## Architecture

The project is split into two phases:

### Build phase (runs once)

```
GitHub repo → AST chunker → sentence-transformers → ChromaDB
```

1. Every `.py` file in the repo is parsed using Python's built-in `ast` module
2. Functions and classes are extracted as individual chunks (not fixed-size splits)
3. Each chunk is embedded locally using `sentence-transformers/all-MiniLM-L6-v2`
4. Vectors and metadata are persisted to ChromaDB on disk

### Query phase (runs per question)

```
User question → embed → ChromaDB similarity search → top-k chunks → Groq (Llama 3.1) → answer
```

1. The question is embedded using the same model
2. ChromaDB returns the 5 most semantically similar code chunks
3. Chunks are assembled into a structured prompt
4. Groq (Llama 3.1) generates a sourced answer

---

## Project structure

```
codebase-qa/
├── app.py                    # Flask web UI backend
├── main.py                   # CLI entry point
├── requirements.txt
├── .env                      # API keys (never committed)
├── .env.example              # Template for contributors
├── templates/
│   └── index.html            # Chat UI (file selector + 3 modes)
└── src/
    ├── ingestion/
    │   ├── chunker.py        # AST-based code chunker
    │   ├── embedder.py       # Embeds chunks, persists to ChromaDB
    │   └── pipeline.py       # Orchestrates chunker + embedder
    └── retrieval/
        ├── retriever.py      # Semantic search against ChromaDB
        └── agent.py          # Prompt builder + Groq API caller
```

---

## Tech stack

| Component | Tool | Why |
|---|---|---|
| LLM | Groq + Llama 3.1 | Free tier, fast inference |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Runs fully locally, no API key |
| Vector store | ChromaDB | Zero config, persists to disk |
| Web UI | Flask + vanilla JS | Lightweight, no frontend build step |
| Code parsing | Python `ast` (built-in) | Structural chunking — no dependencies |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/JanavGandhi/Codebase-Q-A-Agent.git
cd Codebase-Q-A-Agent

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Get a free Groq API key

Sign up at [console.groq.com](https://console.groq.com) — no credit card required.

```bash
cp .env.example .env
# Add your key: GROQ_API_KEY=gsk_...
```

### 3. Index a repository

```bash
# Clone the repo you want to query
git clone --depth=1 https://github.com/psf/requests.git repos/requests

# Build the index (runs once, ~30 seconds)
python main.py ingest repos/requests
```

### 4. Start asking questions

**CLI:**
```bash
python main.py ask "How does redirect handling work?"
python main.py explain-file "src/retrieval/agent.py"
python main.py explain-line "collection.query(query_embeddings=[query_embedding])" "src/retrieval/retriever.py"
```

**Web UI:**
```bash
python app.py
# Open http://localhost:5000
```

---

## Design decisions

**Why no LangChain?**
LangChain abstracts away the retrieval loop behind several layers of configuration. Building the pipeline from scratch means every step is explicit and debuggable — and means I can explain exactly what happens between a user's question and the agent's answer.

**Why AST-based chunking over fixed-size splitting?**
Fixed-size chunking cuts at arbitrary character boundaries, which often splits a function signature from its body. AST parsing cuts at natural semantic boundaries — each chunk is exactly one function or class. This produces cleaner embeddings and significantly better retrieval relevance.

**Why `all-MiniLM-L6-v2` for embeddings?**
It runs entirely locally (no API cost, no network dependency), loads in under 2 seconds, and produces strong semantic representations for code. It's a deliberate tradeoff: slightly lower accuracy than OpenAI's `text-embedding-3-small`, but zero marginal cost per query.

**Why ChromaDB over FAISS or Pinecone?**
ChromaDB persists to disk out of the box with no configuration. FAISS requires manual serialisation. Pinecone requires a paid account for production use. For a local development tool, ChromaDB is the right tradeoff.

**Why cosine similarity over euclidean distance?**
Embedding vectors vary in magnitude depending on text length. Cosine similarity normalises for magnitude and measures directional similarity — which is what we actually want when comparing semantic meaning.

---

## Limitations

- Only indexes `.py` files — JavaScript, TypeScript, and other languages are not supported yet
- Very large files (>80 lines per function) are chunked at the method level, which may lose some class-level context
- The agent answers based only on retrieved chunks — if the relevant code isn't in the top-5 results, the answer will be incomplete
- ChromaDB is local only — no shared index across machines

---

## Possible extensions

- [ ] Support for JavaScript / TypeScript codebases
- [ ] Re-ranking retrieved chunks with a cross-encoder for higher precision
- [ ] Conversation memory so follow-up questions retain context
- [ ] GitHub URL input — paste a repo URL and index it directly from the UI
- [ ] Export Q&A sessions as markdown documentation

---

## License

MIT