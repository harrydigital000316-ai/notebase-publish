"""HTML renderer for notebase-publish."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .vault import Note, Vault


class Renderer:
    """Renders vault notes to static HTML using Jinja2 templates."""

    WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

    def __init__(self, out_dir: Path, verbose: bool = False):
        self.out_dir = Path(out_dir).resolve()
        self.verbose = verbose

        # Output directories
        self.notes_dir = self.out_dir / "note"
        self.tags_dir = self.out_dir / "tags"
        self.daily_dir = self.out_dir / "daily"
        self.static_dir = self.out_dir / "static"

        for d in (self.notes_dir, self.tags_dir, self.daily_dir, self.static_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Add custom filters
        self.env.filters["tojson"] = json.dumps

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"  {msg}")

    def resolve_wikilinks(self, html: str, slug_map: dict[str, str]) -> str:
        """Convert [[Note Title]] or [[Note Title|Display]] to HTML links."""

        def replace(match: re.Match) -> str:
            link_text = match.group(1)
            # Handle [[Title|Display]] format
            if "|" in link_text:
                target, display = link_text.split("|", 1)
            else:
                target = display = link_text

            target = target.strip()
            display = display.strip()
            slug = slug_map.get(target.lower())

            if slug:
                return f'<a href="/note/{slug}.html" class="wikilink">{display}</a>'
            else:
                # Unknown link - style differently
                return f'<span class="wikilink missing" title="Unknown: {target}">{display}</span>'

        return self.WIKILINK_PATTERN.sub(replace, html)

    def render_all(self, notes: dict[str, Note], vault: Vault) -> None:
        """Render all notes and index pages."""
        # Build slug map for wiki-link resolution
        slug_map = {note.title.lower(): note.slug for note in notes.values()}
        for note in notes.values():
            for alias in note.aliases:
                slug_map[alias.lower()] = note.slug

        # Build tag index
        tag_to_notes: dict[str, list[Note]] = {}
        for note in notes.values():
            for tag in note.tags:
                tag_to_notes.setdefault(tag, []).append(note)

        # Build daily notes list
        daily_notes = vault.get_daily_notes()

        # Build project index
        project_notes: dict[str, list[Note]] = {}
        for tag, tagged_notes in tag_to_notes.items():
            if tag.startswith("project/"):
                project_notes[tag] = tagged_notes

        # Render individual notes
        self._log(f"Rendering {len(notes)} notes...")
        for note in notes.values():
            self._render_note(note, notes, slug_map, tag_to_notes)

        # Render index pages
        self._log("Rendering index pages...")
        self._render_index(notes, tag_to_notes, daily_notes, project_notes)
        self._render_tag_pages(tag_to_notes, notes)
        self._render_daily_pages(daily_notes, notes)
        self._render_graph_page(notes, notes, tag_to_notes)
        self._render_search_page()

        # Copy static assets
        self._copy_static_assets()

        self._log(f"Site rendered to {self.out_dir}")

    def _render_note(
        self,
        note: Note,
        all_notes: dict[str, Note],
        slug_map: dict[str, str],
        tag_to_notes: dict[str, list[Note]],
    ) -> None:
        """Render a single note page."""
        # Resolve wiki-links in HTML
        html = self.resolve_wikilinks(note.html, slug_map)

        # Backlinks
        backlinks = []
        for other in all_notes.values():
            if note.slug in other.wiki_links:
                backlinks.append(other)

        template = self.env.get_template("note.html")
        rendered = template.render(
            note=note,
            html=html,
            backlinks=backlinks,
            tag_to_notes=tag_to_notes,
            all_notes=all_notes,
        )

        out_path = self.notes_dir / f"{note.slug}.html"
        out_path.write_text(rendered, encoding="utf-8")

    def _render_index(
        self,
        notes: dict[str, Note],
        tag_to_notes: dict[str, list[Note]],
        daily_notes: list[Note],
        project_notes: dict[str, list[Note]],
    ) -> None:
        """Render homepage."""
        template = self.env.get_template("index.html")
        
        def sort_key(n: Note):
            return n.created or datetime.min
        
        rendered = template.render(
            notes=sorted(notes.values(), key=sort_key, reverse=True)[:20],
            tag_cloud=sorted(tag_to_notes.items(), key=lambda x: -len(x[1]))[:30],
            daily_notes=daily_notes[:10],
            project_pages=sorted(project_notes.keys()),
            total_notes=len(notes),
            total_tags=len(tag_to_notes),
        )
        (self.out_dir / "index.html").write_text(rendered, encoding="utf-8")

    def _render_tag_pages(
        self,
        tag_to_notes: dict[str, list[Note]],
        all_notes: dict[str, Note],
    ) -> None:
        """Render tag index pages."""
        template = self.env.get_template("tag.html")
        
        def sort_key(n: Note):
            return n.created or datetime.min
        
        for tag, tagged_notes in tag_to_notes.items():
            rendered = template.render(
                tag=tag,
                notes=sorted(tagged_notes, key=sort_key, reverse=True),
                related_tags=[t for t in tag_to_notes if t != tag][:10],
            )
            safe_tag = tag.replace("/", "_").replace(" ", "-")
            (self.tags_dir / f"{safe_tag}.html").write_text(rendered, encoding="utf-8")

    def _render_daily_pages(
        self,
        daily_notes: list[Note],
        all_notes: dict[str, Note],
    ) -> None:
        """Render daily notes index."""
        template = self.env.get_template("daily.html")
        rendered = template.render(
            daily_notes=daily_notes,
        )
        (self.daily_dir / "index.html").write_text(rendered, encoding="utf-8")

    def _render_graph_page(
        self,
        notes: dict[str, Note],
        all_notes: dict[str, Note],
        tag_to_notes: dict[str, list[Note]],
    ) -> None:
        """Render interactive knowledge graph page."""
        template = self.env.get_template("graph.html")
        # Build graph data
        nodes = []
        edges = []
        tag_colors = {}
        import hashlib

        for i, tag in enumerate(sorted(set().union(*[set(n.tags) for n in notes.values()]))):
            # Generate consistent color per tag
            h = int(hashlib.md5(tag.encode()).hexdigest()[:6], 16)
            tag_colors[tag] = f"#{h:06x}"

        for note in notes.values():
            primary_tag = note.tags[0] if note.tags else "untagged"
            nodes.append({
                "id": note.slug,
                "label": note.title,
                "title": note.title,
                "group": note.tags[0] if note.tags else "untagged",
                "color": tag_colors.get(note.tags[0], "#888") if note.tags else "#888",
                "url": f"/note/{note.slug}.html",
            })

        for note in notes.values():
            for link in note.wiki_links:
                target = all_notes.get(link.lower().replace(" ", "-"))
                if target:
                    edges.append({"from": note.slug, "to": target.slug})

        graph_data = {"nodes": nodes, "edges": edges}

        template = self.env.get_template("graph.html")
        rendered = template.render(
            graph_json=json.dumps(graph_data),
            tag_colors=json.dumps(tag_colors),
        )
        (self.out_dir / "graph.html").write_text(rendered, encoding="utf-8")

    def _render_search_page(self) -> None:
        """Render search page."""
        template = self.env.get_template("search.html")
        rendered = template.render()
        (self.out_dir / "search.html").write_text(rendered, encoding="utf-8")

    def _copy_static_assets(self) -> None:
        """Copy static assets to output."""
        source_static = Path(__file__).parent / "static"
        if source_static.exists():
            for item in source_static.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(source_static)
                    dest = self.static_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)