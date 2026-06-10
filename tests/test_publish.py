"""Tests for notebase-publish."""

import tempfile
from pathlib import Path

from notebase_publish.vault import Vault, Note, parse_note
from notebase_publish.renderer import Renderer
from notebase_publish.search import build_search_index, build_tag_index, build_graph_data


def test_parse_note():
    """Test parsing a note with frontmatter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        note_path = Path(tmpdir) / "test.md"
        content = """---
title: "Test Note"
tags: ["test", "example"]
aliases: ["tn"]
created: "2024-01-01T12:00:00"
modified: "2024-01-01T12:00:00"
---

# Test Note

This is a test note with #inline tag.
"""
        note_path.write_text(content)
        note = parse_note(note_path)

        assert note.title == "Test Note"
        assert "test" in note.tags
        assert "example" in note.tags
        assert "tn" in note.aliases
        assert "inline" in note.tags
        assert "This is a test note" in note.content


def test_vault_loading():
    """Test loading a vault with multiple notes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(Path(tmpdir))
        
        # Create test notes
        note1 = Path(tmpdir) / "note1.md"
        note1.write_text("""---
title: "Note One"
tags: ["project/alpha", "research"]
---
# Note One

See [[Note Two]] for more.
""")
        
        note2 = Path(tmpdir) / "note2.md"
        note2.write_text("""---
title: "Note Two"
tags: ["project/alpha", "learning"]
---
# Note Two

Backlink from [[Note One]].
""")

        notes = vault.load_notes()
        assert len(notes) == 2
        
        # Check wiki-links parsed
        n1 = notes.get("note-one")
        n2 = notes.get("note-two")
        assert n1 is not None
        assert n2 is not None
        assert "note-two" in n1.wiki_links
        assert "note-one" in n2.wiki_links
        
        # Check tag indexing
        tag_counts = vault.get_all_tags()
        assert tag_counts.get("project/alpha") == 2
        assert tag_counts.get("research") == 1
        assert tag_counts.get("learning") == 1
        
        # Check project index
        project_notes = vault.get_notes_by_project("alpha")
        assert len(project_notes) == 2


def test_renderer_wikilink_resolution():
    """Test wiki-link resolution in renderer."""
    from notebase_publish.renderer import Renderer
    
    renderer = Renderer(Path("/tmp"))
    
    # Build slug map
    slug_map = {
        "note one": "note-one",
        "note two": "note-two",
        "alias": "note-one",
    }
    
    # Test basic link
    html = renderer.resolve_wikilinks("<p>See [[Note One]] for more</p>", slug_map)
    assert 'href="/note/note-one.html"' in html
    assert '>Note One<' in html
    
    # Test aliased link
    html = renderer.resolve_wikilinks("<p>See [[Note One|alias]] for more</p>", slug_map)
    assert '>alias<' in html
    
    # Test unknown link
    html = renderer.resolve_wikilinks("<p>See [[Unknown]] for more</p>", slug_map)
    assert 'class="wikilink missing"' in html
    assert '>Unknown<' in html


def test_search_index_generation():
    """Test search index JSON generation."""
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        
        notes = {
            "note-one": Note(
                path=Path("note-one.md"),
                title="Note One",
                slug="note-one",
                content="This is about transformer architecture",
                html="<p>This is about transformer architecture</p>",
                tags=["ai", "research"],
                created=None,
                modified=None,
            ),
            "note-two": Note(
                path=Path("note-two.md"),
                title="Note Two", 
                slug="note-two",
                content="Investing in semiconductor stocks",
                html="<p>Investing in semiconductor stocks</p>",
                tags=["investing", "finance"],
                created=None,
                modified=None,
            ),
        }
        
        search_path = build_search_index(notes, out_dir)
        assert search_path.exists()
        
        with open(search_path) as f:
            index = json.load(f)
        
        assert len(index) == 2
        assert index[0]["title"] == "Note One"
        assert "ai" in index[0]["tags"]
        assert "transformer" in index[0]["content"]


def test_tag_index_generation():
    """Test tag cloud JSON generation."""
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        
        notes = {
            "note-one": Note(
                path=Path("note-one.md"),
                title="Note One",
                slug="note-one",
                content="Content",
                html="<p>Content</p>",
                tags=["ai", "research"],
                created=None,
                modified=None,
            ),
            "note-two": Note(
                path=Path("note-two.md"),
                title="Note Two",
                slug="note-two",
                content="Content",
                html="<p>Content</p>",
                tags=["ai", "investing"],
                created=None,
                modified=None,
            ),
        }
        
        tag_path = build_tag_index(notes, out_dir)
        assert tag_path.exists()
        
        with open(tag_path) as f:
            tags = json.load(f)
        
        # ai should have count 2
        ai_tag = next(t for t in tags if t["name"] == "ai")
        assert ai_tag["count"] == 2
        assert ai_tag["url"].endswith("tags/ai.html")


def test_graph_data_generation():
    """Test graph data JSON generation."""
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        
        notes = {
            "note-one": Note(
                path=Path("note-one.md"),
                title="Note One",
                slug="note-one",
                content="Links to [[Note Two]]",
                html="<p>Links to Note Two</p>",
                tags=["ai"],
                created=None,
                modified=None,
                wiki_links=["note-two"],
            ),
            "note-two": Note(
                path=Path("note-two.md"),
                title="Note Two",
                slug="note-two",
                content="",
                html="<p></p>",
                tags=["research"],
                created=None,
                modified=None,
                wiki_links=[],
            ),
        }
        
        graph_path = build_graph_data(notes, out_dir)
        assert graph_path.exists()
        
        with open(graph_path) as f:
            graph = json.load(f)
        
        assert len(graph["nodes"]) == 2
        assert graph["nodes"][0]["id"] == "note-one"
        assert len(graph["edges"]) == 1
        assert graph["edges"][0]["from"] == "note-one"
        assert graph["edges"][0]["to"] == "note-two"


def test_slug_generation():
    """Test slugify function."""
    from notebase_publish.vault import slugify
    
    assert slugify("Hello World") == "hello-world"
    assert slugify("Test_Note") == "test_note"
    assert slugify("  Spaces  ") == "spaces"
    assert slugify("Special!@#Chars") == "specialchars"
    assert slugify("中文標題") == "中文標題"  # Unicode preserved


def test_frontmatter_parsing():
    """Test YAML frontmatter parsing."""
    content = """---
title: "Test Note"
tags: ["tag1", "tag2"]
aliases: ["alias1"]
created: "2024-01-01T12:00:00"
---

# Test Note

Content here.
"""
    fm, body = parse_frontmatter(content)
    
    assert fm["title"] == "Test Note"
    assert fm["tags"] == ["tag1", "tag2"]
    assert fm["aliases"] == ["alias1"]
    assert "Content here" in body


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])