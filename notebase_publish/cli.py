"""CLI for notebase-publish."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .vault import Vault
from .renderer import Renderer
from .search import build_search_index, build_tag_index, build_graph_data
from .deploy import deploy_site
from .server import run as run_server

app = typer.Typer(
    name="notebase-publish",
    help="AI's public cognitive exoskeleton — static site generator for notebase vaults.",
    add_completion=False,
)
console = Console()


@app.command()
def build(
    vault_path: Path = typer.Option(..., "--vault", "-v", help="Path to notebase vault", exists=True),
    out_dir: Path = typer.Option(..., "--out", "-o", help="Output directory"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Build static site from vault."""
    if verbose:
        console.print(f"[cyan]Loading vault from {vault_path}...[/cyan]")

    vault = Vault(vault_path)
    notes = vault.load_notes()

    if verbose:
        console.print(f"[green]Loaded {len(notes)} notes[/green]")

    renderer = Renderer(out_dir, verbose=verbose)
    renderer.render_all(notes, vault)
    
    # Build search, tag, and graph indexes
    if verbose:
        console.print("[cyan]Building search index...[/cyan]")
    build_search_index(notes, out_dir)
    
    if verbose:
        console.print("[cyan]Building tag index...[/cyan]")
    build_tag_index(notes, out_dir)
    
    if verbose:
        console.print("[cyan]Building graph data...[/cyan]")
    build_graph_data(notes, out_dir)
    
    if verbose:
        console.print("[green]✓ Build complete[/green]")


@app.command()
def serve(
    vault_path: Path = typer.Option(..., "--vault", "-v", help="Path to notebase vault", exists=True),
    out_dir: Path = typer.Option(..., "--out", "-o", help="Output directory"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve on"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to (0.0.0.0 for external access)"),
    no_build: bool = typer.Option(False, "--no-build", help="Skip initial build"),
):
    """Run development server with live reload."""
    if not no_build:
        console.print("[cyan]Building initial site...[/cyan]")
        vault = Vault(vault_path)
        notes = vault.load_notes()
        renderer = Renderer(out_dir)
        renderer.render_all(notes, vault)
        build_search_index(notes, out_dir)
        build_tag_index(notes, out_dir)
        build_graph_data(notes, out_dir)

    console.print(f"[green]Starting server at http://{host}:{port}[/green]")
    console.print("[cyan]Watching for changes... (Ctrl+C to stop)[/cyan]")
    run_server(vault_path, out_dir, port, host)


@app.command()
def deploy(
    out_dir: Path = typer.Option(..., "--out", "-o", help="Output directory to deploy"),
    target: str = typer.Option("github-pages", "--target", "-t", help="Deploy target: github-pages, netlify, rsync"),
    remote: Optional[str] = typer.Option(None, "--remote", "-r", help="Git remote name (for github-pages)"),
    branch: str = typer.Option("gh-pages", "--branch", "-b", help="Branch to deploy to"),
):
    """Deploy built site to target platform."""
    deploy_site(out_dir, target, remote=remote, branch=branch)


@app.command()
def init(
    vault_path: Path = typer.Option("~/dev_notes", "--vault", "-v", help="Vault path to initialize"),
    out_dir: Path = typer.Option("./_site", "--out", "-o", help="Default output directory"),
):
    """Initialize notebase-publish configuration."""
    # Create vault structure if missing
    vault_path = vault_path.expanduser().resolve()
    vault_path.mkdir(parents=True, exist_ok=True)
    (vault_path / ".notebase").mkdir(exist_ok=True)
    (vault_path / "templates").mkdir(exist_ok=True)

    # Create default templates if missing
    default_template = vault_path / "templates" / "default.md"
    if not default_template.exists():
        default_template.write_text("""---
title: "{{title}}"
tags: []
aliases: []
created: "{{date}}"
modified: "{{date}}"
---

# {{title}}

<!-- Write your note here -->
""", encoding="utf-8")

    daily_template = vault_path / "templates" / "daily.md"
    if not daily_template.exists():
        daily_template.write_text("""---
title: "Daily Note - {{date}}"
tags: ["daily"]
aliases: []
created: "{{date}}"
modified: "{{date}}"
---

# Daily Note - {{date}}

## 📅 Today's Focus
- [ ] 
- [ ] 
- [ ] 

## 📝 Notes


## 🔗 Links


## 💭 Reflections

""", encoding="utf-8")

    console.print(f"[green]✓ Initialized vault at {vault_path}[/green]")
    console.print(f"  Default output: {out_dir}")
    console.print("  Run: notebase-publish build --vault ~/dev_notes --out ./_site")


if __name__ == "__main__":
    app()