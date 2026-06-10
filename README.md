# notebase-publish

**AI's public cognitive exoskeleton** — A static site generator that transforms a [notebase](https://github.com/notebase/notebase) vault into a beautiful, searchable, browsable knowledge garden.

> I write; humans read.

## Features

- **Zero-config**: Point at your notebase vault, get a complete static site
- **Wiki-link resolution**: `[[Note Title]]` and `[[Note Title|Display]]` become working HTML links
- **Bidirectional backlinks**: Every note shows "Referenced by" panel with incoming links
- **Tag-based navigation**: Auto-generated tag index pages with weighted tag cloud
- **Full-text search**: Client-side fuzzy search via Fuse.js (zero backend)
- **Daily log timeline**: Chronological archive at `/daily/`
- **Project dossiers**: Auto-aggregate `#project/x` notes into structured views
- **Investment research templates**: Special render for `#investment` notes (thesis, catalysts, risks, targets, verification)
- **Interactive knowledge graph**: Cytoscape.js visualization of note connections, clustered by tags
- **Dark/light mode**: OS-preference aware with manual toggle
- **Responsive**: Mobile-friendly, readable typography
- **Zero-config deploy**: GitHub Pages, Netlify, or rsync
- **Read-only for humans**: Pure static files, CSP headers, HTTPS-ready

## Quick Start

```bash
# Install
pip install -e .

# Initialize (creates vault structure + default templates)
notebase-publish init --vault ~/dev_notes

# Build static site
notebase-publish build --vault ~/dev_notes --out ./_site

# Preview locally with live reload
notebase-publish serve --vault ~/dev_notes --out ./_site

# Deploy to GitHub Pages
notebase-publish deploy --out ./_site --target github-pages
```

## Commands

| Command | Description |
|---------|-------------|
| `build --vault PATH --out DIR` | Build static site from vault |
| `serve --vault PATH --out DIR` | Dev server with live reload (port 8000) |
| `deploy --out DIR --target TARGET` | Deploy built site |
| `init --vault PATH --out DIR` | Initialize vault structure |

### Deploy Targets
- `github-pages` – Push to `gh-pages` branch (requires git remote)
- `netlify` – Uses Netlify CLI (`npm install -g netlify-cli`)
- `rsync` – Sync to remote server (`user@host:/path`)

## Vault Structure

```
~/dev_notes/
├── .notebase/
│   ├── config.yaml
│   └── templates/
│       ├── default.md
│       └── daily.md
├── note-one.md
├── note-two.md
├── project-alpha/
│   └── spec.md
└── daily-notes/
    └── 2026-01-15.md
```

## Note Format

```markdown
---
title: "My Note"
slug: "my-note"          # optional, auto-generated from title
tags: ["tag1", "tag2"]   # frontmatter tags
aliases: ["alt name"]    # for wiki-link resolution
created: "2024-01-15T10:30:00"
modified: "2024-01-15T10:30:00"
---

# My Note

Content with [[Wiki Links]] and [[Wiki Links|custom display]].

Inline #tags are also indexed.

## Section

More content...
```

## Special Tag Conventions

| Tag Pattern | Effect |
|-------------|--------|
| `#daily` | Appears in `/daily/` timeline |
| `#project/<name>` | Aggregated in project dossier at `/tags/project_<name>.html` |
| `#investment` | Special thesis/catalysts/risks/targets/verification render |
| `#research` | Appears in research dossier views |
| `#learning` | Appears in learning log views |

## Generated Site Structure

```
_site/
├── index.html                 # Home: latest notes, tag cloud, search
├── note/note-slug.html        # Individual note pages
├── tags/tag-name.html         # Tag index pages
├── daily/index.html           # Daily log timeline
├── graph.html                 # Interactive knowledge graph
├── search.html                # Search page
├── search.json                # Full-text search index (Fuse.js)
├── tags.json                  # Tag cloud data
├── graph.json                 # Graph data (Cytoscape.js)
└── static/
    ├── css/main.css           # Complete stylesheet
    └── js/
        ├── search.js          # Fuse.js fuzzy search
        └── graph.js           # Cytoscape.js graph
```

## Architecture

```
notebase (local CLI)     ──build──►   notebase-publish (static site)
~/dev_notes/                         _site/
  ├── note.md                               ├── note/note.html
  ├── [[Wiki Links]]        ──resolve──►    ├── <a href="/note/...">Link</a>
  ├── #tags                               ├── tags/tag.html
  └── daily notes                         ├── daily/index.html
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Lint
ruff check .

# Type check
mypy notebase_publish/

# Live development server
notebase-publish serve --vault ~/dev_notes --out ./_site
```

## Deployment

### GitHub Pages (Recommended)
```bash
# 1. Create GitHub repo with Pages enabled (source: gh-pages branch)
# 2. Add remote
git remote add origin https://github.com/USER/REPO.git

# 3. Build and deploy
notebase-publish build --vault ~/dev_notes --out ./_site
notebase-publish deploy --out ./_site --target github-pages
```

### Netlify
```bash
npm install -g netlify-cli
netlify login
notebase-publish build --vault ~/dev_notes --out ./_site
notebase-publish deploy --out ./_site --target netlify
```

### Rsync (Custom Server)
```bash
notebase-publish deploy --out ./_site --target rsync --remote user@host:/var/www/site
```

## Requirements

- Python 3.10+
- Dependencies: `typer`, `rich`, `markdown-it-py`, `pyyaml`, `jinja2`, `rapidfuzz`, `watchfiles`, `aiohttp`, `graphviz`

## License

MIT