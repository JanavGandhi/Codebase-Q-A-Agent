# app.py
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from src.retrieval.agent import ask, explain_line, explain_file
from src.ingestion.pipeline import build_index

app = Flask(__name__)

REPO_PATH = "repos/requests"   # default repo — can be changed via UI


@app.route("/")
def index():
    """Serve the chat UI."""
    files = _get_indexed_files()
    return render_template("index.html", files=files)


@app.route("/api/chat", methods=["POST"])
def chat():
    """Main chat endpoint — routes to the right agent function."""
    data     = request.json
    mode     = data.get("mode", "ask")        # "ask" | "explain_file" | "explain_line"
    question = data.get("question", "")
    filepath = data.get("filepath", "")
    snippet  = data.get("snippet", "")

    try:
        if mode == "explain_file":
            result = explain_file(_normalise_path(filepath))
        elif mode == "explain_line":
            result = explain_line(snippet, filepath)
        else:
            result = ask(question)

        return jsonify({
            "answer":  result["answer"],
            "sources": result.get("sources", [])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/files")
def list_files():
    """Return all indexed file paths for the file selector."""
    return jsonify({"files": _get_indexed_files()})


def _get_indexed_files() -> list[str]:
    """Fetch unique file paths stored in ChromaDB."""
    try:
        from src.ingestion.embedder import get_chroma_collection
        collection = get_chroma_collection()
        results    = collection.get(include=["metadatas"])
        paths      = sorted(set(m["filepath"] for m in results["metadatas"]))
        return paths
    except Exception:
        return []


def _normalise_path(filepath: str) -> str:
    """Accept both forward and back slashes."""
    return str(Path(filepath))


if __name__ == "__main__":
    app.run(debug=True, port=5000)