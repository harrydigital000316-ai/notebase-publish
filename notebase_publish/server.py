"""Development server with live reload for notebase-publish."""

from __future__ import annotations

import asyncio
import signal
from pathlib import Path
from typing import Optional

from watchfiles import awatch


async def run_server(vault_path: Path, out_dir: Path, port: int = 8000, host: str = "0.0.0.0") -> None:
    """Run the development server with live reload."""
    from .vault import Vault
    from .renderer import Renderer
    from .search import build_search_index, build_tag_index, build_graph_data
    from aiohttp import web

    vault_path = Path(vault_path).resolve()
    out_dir = Path(out_dir).resolve()

    vault = Vault(vault_path)

    async def build_site() -> None:
        """Rebuild the site."""
        notes = vault.load_notes()

        renderer = Renderer(out_dir)
        renderer.render_all(notes, vault)

        build_search_index(notes, out_dir)
        build_tag_index(notes, out_dir)
        build_graph_data(notes, out_dir)

        print(f"Rebuilt site ({len(notes)} notes)")

    # Initial build
    await build_site()

    # Setup HTTP server
    app = web.Application()
    app.router.add_static("/", out_dir, follow_symlinks=True)
    # Add route for root to serve index.html
    async def index_handler(request):
        return web.FileResponse(out_dir / "index.html")
    app.router.add_get("/", index_handler)

    # WebSocket connections for live reload
    websockets: set[web.WebSocketResponse] = set()

    async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        websockets.add(ws)
        try:
            async for msg in ws:
                pass
        finally:
            websockets.discard(ws)
        return ws

    app.router.add_get("/__reload", websocket_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"Server running at http://{host}:{port}")
    print("Watching for changes... (Ctrl+C to stop)")

    # Watch for file changes using awatch (async iterator)
    try:
        async for changes in awatch(vault_path, recursive=True):
            # Filter relevant changes
            relevant = any(
                Path(c[1]).suffix in (".md", ".markdown")
                for c in changes
            )

            if relevant:
                print(f"Changes detected: {changes}")
                await build_site()
                # Notify clients
                for ws in websockets:
                    try:
                        await ws.send_str("reload")
                    except Exception:
                        pass
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()


def run(vault_path: Path, out_dir: Path, port: int = 8000, host: str = "0.0.0.0") -> None:
    """Entry point for CLI."""
    from watchfiles import awatch  # Verify awatch is available

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nShutting down...")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(run_server(vault_path, out_dir, port, host))