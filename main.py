# main.py
import argparse
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.ingestion.pipeline import build_index
from src.retrieval.agent import ask, explain_line, explain_file

console = Console()


def run_ingest(args):
    build_index(args.repo_path)


def run_ask(args):
    console.print(f"\n[bold]Question:[/bold] {args.question}\n")
    with console.status("[cyan]Thinking...[/cyan]"):
        result = ask(args.question)
    _print_answer(result["answer"], result["sources"])


def run_explain_line(args):
    console.print(f"\n[bold]Explaining snippet from[/bold] [cyan]{args.filepath}[/cyan]\n")
    with console.status("[cyan]Analysing...[/cyan]"):
        result = explain_line(args.snippet, args.filepath)
    _print_answer(result["answer"], result["sources"])


def run_explain_file(args):
    console.print(f"\n[bold]Explaining file:[/bold] [cyan]{args.filepath}[/cyan]\n")
    with console.status("[cyan]Reading file chunks...[/cyan]"):
        result = explain_file(args.filepath)
    _print_answer(result["answer"], result.get("sources", []))


def _print_answer(answer: str, sources: list):
    """Shared pretty-printer for all commands."""
    console.print(Panel(
        Markdown(answer),
        title="[bold green]Answer[/bold green]",
        border_style="green"
    ))
    if sources:
        console.print("\n[bold]Sources used:[/bold]")
        for chunk in sources:
            sim = f"[similarity: {chunk['similarity']}]" if "similarity" in chunk else ""
            console.print(
                f"  [cyan]{chunk['name']}[/cyan] "
                f"[dim]{chunk['filepath']} "
                f"lines {chunk['start']}–{chunk['end']} {sim}[/dim]"
            )
    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="Codebase Q&A Agent — ask questions about any Python repo"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: ingest
    p = subparsers.add_parser("ingest", help="Index a repository")
    p.add_argument("repo_path", help="Path to repo e.g. repos/requests or .")
    p.set_defaults(func=run_ingest)

    # Command: ask
    p = subparsers.add_parser("ask", help="Ask a general question about the codebase")
    p.add_argument("question")
    p.set_defaults(func=run_ask)

    # Command: explain-line
    p = subparsers.add_parser("explain-line", help="Explain a specific line or snippet")
    p.add_argument("snippet", help="The exact code snippet to explain")
    p.add_argument("filepath", help="The file it comes from e.g. main.py")
    p.set_defaults(func=run_explain_line)

    # Command: explain-file
    p = subparsers.add_parser("explain-file", help="Explain what an entire file does")
    p.add_argument("filepath", help="Relative path e.g. src/retrieval/agent.py")
    p.set_defaults(func=run_explain_file)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()