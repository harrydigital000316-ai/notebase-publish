"""Vault operations for notebase-publish."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass
class Note:
    """Represents a parsed note from the vault."""

    path: Path
    title: str
    slug: str
    content: str
    html: str
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    created: datetime | None = None
    modified: datetime | None = None
    frontmatter: dict[str, Any] = field(default_factory=dict)
    wiki_links: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "slug": self.slug,
            "tags": self.tags,
            "aliases": self.aliases,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
            "html": self.html,
            "content": self.content,
            "frontmatter": self.frontmatter,
            "wiki_links": self.wiki_links,
        }


def slugify(title: str) -> str:
    """Convert title to URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from note content."""
    if not content.startswith("---"):
        return {}, content

    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return frontmatter, body
    except yaml.YAMLError:
        return {}, content


def extract_wiki_links(content: str) -> list[str]:
    """Extract wiki-links [[Note Title]] or [[Note Title|Display]] from content."""
    pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
    return re.findall(pattern, content)


def extract_inline_tags(content: str) -> list[str]:
    """Extract inline #tags from content."""
    pattern = r"(?<!\w)#([\w\-/]+)"
    return list(set(re.findall(pattern, content)))


def parse_note(path: Path, md: MarkdownIt) -> Note:
    """Parse a single note file."""
    content = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    title = frontmatter.get("title", path.stem)
    slug = frontmatter.get("slug", slugify(title))
    tags = frontmatter.get("tags", [])
    aliases = frontmatter.get("aliases", [])

    # Extract inline tags from content
    inline_tags = extract_inline_tags(body)
    tags.extend(inline_tags)
    tags = list(set(tags))

    # Parse dates
    created = frontmatter.get("created")
    modified = frontmatter.get("modified")
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    if isinstance(modified, str):
        modified = datetime.fromisoformat(modified)

    # Extract wiki-links
    wiki_links = extract_wiki_links(body)

    # Render markdown to HTML
    html = md.render(body)

    return Note(
        path=path,
        title=title,
        slug=slug,
        content=body,
        html=html,
        tags=tags,
        aliases=aliases,
        created=created,
        modified=modified,
        frontmatter=frontmatter,
        wiki_links=wiki_links,
    )


class Vault:
    """Represents a notebase vault and provides note iteration."""

    def __init__(self, path: Path):
        self.path = path.expanduser().resolve()
        self._notes: dict[str, Note] | None = None
        self._md = MarkdownIt("commonmark", {"html": True}).enable("table")

    def iter_note_paths(self) -> list[Path]:
        """Get all note file paths, excluding .notebase/ and templates/."""
        note_paths = []
        for ext in (".md", ".markdown"):
            for p in self.path.rglob(f"*{ext}"):
                rel = p.relative_to(self.path)
                # Skip .notebase/ and templates/ directories
                if not any(part.startswith(".") for part in rel.parts) and "templates" not in rel.parts:
                    note_paths.append(p)
        return sorted(note_paths)

    def load_notes(self) -> dict[str, Note]:
        """Load and parse all notes in the vault."""
        if self._notes is not None:
            return self._notes

        notes = {}
        for path in self.iter_note_paths():
            try:
                note = parse_note(path, self._md)
                notes[note.slug] = note
            except Exception as e:
                print(f"Warning: Failed to parse {path}: {e}")

        self._notes = notes
        return notes

    def get_note(self, slug: str) -> Note | None:
        """Get a note by slug."""
        return self.load_notes().get(slug)

    def get_note_by_title(self, title: str) -> Note | None:
        """Get a note by title (case-insensitive) or alias."""
        notes = self.load_notes()
        title_lower = title.lower()
        for note in notes.values():
            if note.title.lower() == title_lower:
                return note
            if title_lower in [a.lower() for a in note.aliases]:
                return note
        return None

    def get_all_tags(self) -> dict[str, int]:
        """Get all tags with their note counts."""
        tag_counts: dict[str, int] = {}
        for note in self.load_notes().values():
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return dict(sorted(tag_counts.items(), key=lambda x: -x[1]))

    def get_daily_notes(self) -> list[Note]:
        """Get daily notes sorted by date."""
        daily = []
        for note in self.load_notes().values():
            if note.path.parts[-1].startswith("daily-") or note.path.parent.name == "daily-notes":
                daily.append(note)
            elif note.created and "daily" in [t.lower() for t in note.tags]:
                daily.append(note)
        return sorted(daily, key=lambda n: n.created or datetime.min, reverse=True)

    def get_notes_by_tag(self, tag: str) -> list[Note]:
        """Get all notes with a specific tag."""
        return [n for n in self.load_notes().values() if tag in n.tags]

    def get_notes_by_project(self, project: str) -> list[Note]:
        """Get all notes for a project (tagged #project/<name>)."""
        tag = f"project/{project}"
        return self.get_notes_by_tag(tag)