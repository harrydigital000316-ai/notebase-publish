"""notebase-publish - AI's public cognitive exoskeleton."""

__version__ = "0.1.0"

__all__ = [
    "Vault",
    "Note",
    "parse_note",
    "slugify",
    "parse_frontmatter",
    "extract_wiki_links",
    "extract_inline_tags",
]

from .vault import (
    Vault,
    Note,
    parse_note,
    slugify,
    parse_frontmatter,
    extract_wiki_links,
    extract_inline_tags,
)