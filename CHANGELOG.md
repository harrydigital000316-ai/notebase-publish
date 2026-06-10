# Changelog

All notable changes to this project will be documented in this format.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows (lint, test, build, deploy)
- GitHub Actions cron workflows for daily automated tasks
- Issue templates (bug report, feature request)
- Pull request template
- Deploy workflow with GitHub Pages integration
- `--host` CLI option for development server (default: 0.0.0.0)
- Proper `.gitignore` handling for gh-pages deploy

### Fixed
- Server file watcher bug (awatch returns strings, not Path objects)
- Deploy script now uses temp repo + credential helper for auth
- Deploy excludes .venv and source files (only deploys _site/)

### Changed
- Default serve host changed from localhost to 0.0.0.0
- Deploy uses orphan gh-pages branch via temp directory

## [0.1.0] - 2026-06-10

### Added
- Initial release: notebase-publish static site generator
- Vault parsing with frontmatter, wiki-links, tags
- Jinja2 templates (base, note, index, tag, daily, graph, search)
- Fuse.js full-text search (client-side)
- Cytoscape.js knowledge graph visualization
- Dark/light theme with CSS custom properties
- Live reload development server with WebSocket
- GitHub Pages deployment via gh-pages branch
- CLI commands: build, serve, deploy, init
- Comprehensive test suite