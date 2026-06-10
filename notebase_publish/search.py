"""Search index builder for notebase-publish."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .vault import Note, Vault


def build_search_index(notes: dict[str, Note], out_dir: Path) -> Path:
    """Build search.json index for client-side Fuse.js search."""
    index = []

    for note in notes.values():
        # Prepare searchable content
        content_parts = []

        # Title (highest weight)
        content_parts.append(note.title)

        # Tags
        content_parts.extend(note.tags)

        # HTML content (strip tags)
        import re
        text_content = re.sub(r"<[^>]+>", " ", note.html)
        text_content = re.sub(r"\s+", " ", text_content).strip()
        content_parts.append(text_content)

        full_text = " ".join(content_parts)

        index.append({
            "title": note.title,
            "slug": note.slug,
            "url": f"/note/{note.slug}.html",
            "tags": note.tags,
            "created": note.created.isoformat() if note.created else None,
            "content": full_text[:5000],  # Limit content length
            "excerpt": text_content[:300] + ("..." if len(text_content) > 300 else ""),
        })

    # Write search index
    search_json = out_dir / "search.json"
    search_json.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    return search_json


def build_tag_index(notes: dict[str, Note], out_dir: Path) -> Path:
    """Build tag cloud data for navigation."""
    tag_counts = {}
    for note in notes.values():
        for tag in note.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    tags = [
        {"name": tag, "count": count, "url": f"/tags/{tag.replace('/', '_').replace(' ', '-')}.html"}
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])
    ]

    tag_json = out_dir / "tags.json"
    tag_json.write_text(
        json.dumps(tags, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return tag_json


def build_graph_data(notes: dict[str, Note], out_dir: Path) -> Path:
    """Build graph data for Cytoscape.js visualization."""
    import hashlib

    # Assign colors to tags
    all_tags = set()
    for note in notes.values():
        all_tags.update(note.tags)

    tag_colors = {}
    for tag in sorted(all_tags):
        h = int(hashlib.md5(tag.encode()).hexdigest()[:6], 16)
        tag_colors[tag] = f"#{h:06x}"

    nodes = []
    edges = []
    slug_to_title = {n.slug: n.title for n in notes.values()}

    for note in notes.values():
        primary_tag = note.tags[0] if note.tags else "untagged"
        color = tag_colors.get(note.tags[0], "#888") if note.tags else "#888"
        nodes.append({
            "id": note.slug,
            "label": note.title,
            "title": note.title,
            "group": primary_tag,
            "color": color,
            "url": f"/note/{note.slug}.html",
        })

    for note in notes.values():
        for link in note.wiki_links:
            # Try to resolve link to slug
            link_lower = link.lower().replace(" ", "-")
            if link_lower in notes:
                edges.append({
                    "from": note.slug,
                    "to": notes[link_lower].slug,
                })

    graph_data = {"nodes": nodes, "edges": edges}

    graph_json = out_dir / "graph.json"
    graph_json.write_text(
        json.dumps(graph_data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return graph_json