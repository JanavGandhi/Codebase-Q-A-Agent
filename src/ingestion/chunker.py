import ast
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """A single, semantically meaningful unit of code."""
    text:     str
    name:     str       # function/class name  e.g. "SessionRedirectMixin"
    type:     str       # "FunctionDef" | "AsyncFunctionDef" | "ClassDef"
    filepath: str       # relative path inside the repo
    start:    int       # 1-indexed line number where this chunk begins
    end:      int       # 1-indexed line number where it ends


MAX_CHUNK_LINES = 80   # classes larger than this get skipped — their methods are captured individually

SKIP_DIRS = {".venv", "chroma_db", "repos", "__pycache__", ".git", "node_modules"}


def _extract_from_file(filepath: Path, repo_root: Path) -> list[CodeChunk]:
    """Parse one .py file and return a list of CodeChunks."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree   = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []   # skip unparseable files silently

    lines    = source.splitlines()
    chunks   = []
    rel_path = str(filepath.relative_to(repo_root))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        start = node.lineno - 1     # convert to 0-indexed for slicing
        end   = node.end_lineno     # already correct for slicing

        # If a class is huge, skip it — its individual methods will be captured below
        if isinstance(node, ast.ClassDef) and (end - start) > MAX_CHUNK_LINES:
            continue

        chunk_text = "\n".join(lines[start:end])

        chunks.append(CodeChunk(
            text     = chunk_text,
            name     = node.name,
            type     = type(node).__name__,
            filepath = rel_path,
            start    = node.lineno,
            end      = node.end_lineno,
        ))

    return chunks


def chunk_repository(repo_path: str) -> list[CodeChunk]:
    """Walk an entire repo directory and extract all code chunks."""
    repo_root  = Path(repo_path)
    all_chunks: list[CodeChunk] = []

    py_files = list(repo_root.rglob("*.py"))
    print(f"  Found {len(py_files)} Python files")

    for filepath in py_files:
        # Skip unwanted directories
        if any(part in SKIP_DIRS for part in filepath.parts):
            continue
        # Skip test files
        if filepath.name.startswith("test_"):
            continue
        all_chunks.extend(_extract_from_file(filepath, repo_root))

    print(f"  Extracted {len(all_chunks)} code chunks")
    return all_chunks