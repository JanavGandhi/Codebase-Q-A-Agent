# main.py
import argparse
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print as rprint

from src.ingestion.pipeline import build_index
from src.retrieval.agent import ask

console = Console()


def run_ingest(args):
    build_index(args.repo_path)


def run_ask(args):
    console.print(f"\n[bold]Question:[/bold] {args.question}\n")

    with console.status("[cyan]Thinking...[/cyan]"):
        result = ask(args.question)

    # Print the answer as rendered markdown
    console.print(Panel(
        Markdown(result["answer"]),
        title="[bold green]Answer[/bold green]",
        border_style="green"
    ))

    # Print sources
    console.print("\n[bold]Sources used:[/bold]")
    for chunk in result["sources"]:
        console.print(
            f"  [cyan]{chunk['name']}[/cyan] "
            f"[dim]{chunk['filepath']} "
            f"lines {chunk['start']}–{chunk['end']} "
            f"[similarity: {chunk['similarity']}][/dim]"
        )
    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="Codebase Q&A Agent — ask questions about any Python repo"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: ingest
    ingest_parser = subparsers.add_parser("ingest", help="Index a repository")
    ingest_parser.add_argument("repo_path", help="Path to the repo e.g. repos/requests")
    ingest_parser.set_defaults(func=run_ingest)

    # Command: ask
    ask_parser = subparsers.add_parser("ask", help="Ask a question about the codebase")
    ask_parser.add_argument("question", help='e.g. "How does redirect handling work?"')
    ask_parser.set_defaults(func=run_ask)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()