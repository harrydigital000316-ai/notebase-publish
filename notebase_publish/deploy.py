"""Deployment utilities for notebase-publish."""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import Optional


def deploy_site(out_dir: Path, target: str, remote: Optional[str] = None, branch: str = "gh-pages") -> None:
    """Deploy built site to target platform."""
    out_dir = Path(out_dir).resolve()
    
    if not out_dir.exists():
        raise ValueError(f"Output directory {out_dir} does not exist. Run build first.")
    
    if target == "github-pages":
        _deploy_github_pages(out_dir, remote, branch)
    elif target == "netlify":
        _deploy_netlify(out_dir)
    elif target == "rsync":
        _deploy_rsync(out_dir, remote)
    else:
        raise ValueError(f"Unknown deploy target: {target}")


def _deploy_github_pages(out_dir: Path, remote: Optional[str], branch: str) -> None:
    """Deploy to GitHub Pages via gh-pages branch."""
    import tempfile
    import os
    
    # Create a temporary git repo for the gh-pages branch
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        repo = tmpdir / "site"
        repo.mkdir(parents=True, exist_ok=True)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", branch], cwd=repo, check=True, capture_output=True)
        
        # Copy site files
        for item in out_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, repo / item.name)
            else:
                shutil.copytree(item, repo / item.name)
        
        # Configure git
        subprocess.run(["git", "config", "user.name", "notebase-publish"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "bot@notebase.ai"], cwd=repo, check=True)
        
        # Add and commit
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Deploy notebase-publish site"], cwd=repo, check=True, capture_output=True)
        
        # Push
        remote_name = remote or "origin"
        subprocess.run(["git", "push", "-f", remote_name, f"{branch}:{branch}"], cwd=repo, check=True)
        
        print(f"Deployed to GitHub Pages branch '{branch}'")


def _deploy_netlify(out_dir: Path) -> None:
    """Deploy to Netlify (requires netlify CLI)."""
    try:
        subprocess.run(["netlify", "deploy", "--prod", "--dir", str(out_dir)], check=True)
        print("Deployed to Netlify")
    except FileNotFoundError:
        raise RuntimeError("netlify CLI not found. Install with: npm install -g netlify-cli")


def _deploy_rsync(out_dir: Path, remote: Optional[str]) -> None:
    """Deploy via rsync to a remote server."""
    if not remote:
        raise ValueError("rsync deploy requires --remote (user@host:/path)")
    
    # Ensure trailing slash on source for rsync
    src = str(out_dir) + "/"
    subprocess.run(["rsync", "-avz", "--delete", src, remote], check=True)
    print(f"Deployed via rsync to {remote}")