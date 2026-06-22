#!/usr/bin/env python3
"""Lightweight desktop GUI for fontadhd.

A thin pywebview host that renders web/index.html in a native OS webview and
exposes the existing fontadhd operations to JavaScript. All folder-organizing
logic lives in fontadhd.py — this module only bridges UI <-> those functions and
never reimplements an op.

Run with:  python fontadhd.py --gui   (or)   python gui.py
"""

from pathlib import Path
import os
import shutil
import tempfile

from fontadhd import OPS, DEFAULT_ORDER, FONT_EXTS, install_fonts

# pywebview is an optional dependency (the 'gui' extra). Import it lazily so the
# core bridge logic — preview/apply/scan, which is pure fontadhd + stdlib — stays
# importable and unit-testable without it. Only pick_folder() and main() need it.


WEB_DIR = Path(__file__).resolve().parent / "web"

# Params the UI can expose per run. Mirrors the kwargs main() builds in fontadhd.
# Each op only consumes what it needs (the rest are absorbed by **_).
OP_PARAMS = {
    "rename": ["strip", "no_lowercase", "no_hyphenate"],
    "flatten": ["no_recursive"],
    "consolidate": ["separator", "standalone_name"],
    "prune": ["prune"],
    "clean": [],
}


def _build_kwargs(opts):
    """Translate UI options into the kwargs dict fontadhd ops expect.

    Mirrors the kwargs assembled in fontadhd.main(), but with assume_yes=True so
    the GUI never blocks on input() prompts (the user has already confirmed via
    the UI and seen the preview).
    """
    opts = opts or {}
    prune = opts.get("prune", [])
    if isinstance(prune, str):
        prune = [e.strip() for e in prune.split(",") if e.strip()]
    return dict(
        strip=opts.get("strip", ""),
        lowercase=not opts.get("no_lowercase", False),
        space_to_hyphen=not opts.get("no_hyphenate", False),
        recursive=not opts.get("no_recursive", False),
        separator=opts.get("separator", "-"),
        standalone_name=opts.get("standalone_name", "regular"),
        prune=prune,
        assume_yes=True,
    )


def _snapshot(root):
    """Return a nested {name, type, children} tree of the folder.

    Only directories and font files are shown (matches what the ops act on), so
    the before/after panes stay focused on what actually changes.
    """
    root = Path(root)

    def walk(path):
        children = []
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            entries = []
        for entry in entries:
            if entry.is_dir():
                children.append({"name": entry.name, "type": "dir", "children": walk(entry)})
            elif entry.suffix.lower().lstrip(".") in FONT_EXTS or _is_web_font(entry):
                children.append({"name": entry.name, "type": "file"})
        return children

    return {"name": root.name, "type": "dir", "children": walk(root)}


def _is_web_font(path):
    return path.suffix.lower().lstrip(".") in {"woff", "woff2", "eot"}


def _run_pipeline(target, ops, opts):
    unknown = [o for o in ops if o not in OPS]
    if unknown:
        raise ValueError(f"Unknown op(s): {', '.join(unknown)}")
    kwargs = _build_kwargs(opts)
    for op in ops:
        OPS[op](target, **kwargs)


class Api:
    """Methods exposed to the frontend as window.pywebview.api.*

    Note: do NOT store the pywebview Window as an attribute here. pywebview's
    JS-API serializer walks this object's attributes to expose them to JS; a
    reference to the Window leads into its native (WinForms/Cocoa) object and
    recurses infinitely. Fetch the window from webview.windows when needed.
    """

    # --- folder selection -------------------------------------------------
    def pick_folder(self):
        """Open a native folder picker; returns the absolute path or None."""
        import webview
        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return None
        return os.fspath(result[0])

    def resolve_dropped(self, path):
        """Given a path dropped onto the window, return a usable folder path.

        pywebview exposes the real filesystem path of dropped items; if a file
        was dropped we use its parent directory.
        """
        if not path:
            return None
        p = Path(path)
        if p.is_dir():
            return os.fspath(p)
        if p.exists():
            return os.fspath(p.parent)
        return None

    # --- introspection ----------------------------------------------------
    def list_ops(self):
        return {
            "available": list(OPS.keys()),
            "default": list(DEFAULT_ORDER),
            "params": OP_PARAMS,
        }

    # --- trees ------------------------------------------------------------
    def scan(self, path):
        target = Path(path)
        if not target.is_dir():
            return {"error": f"Not a folder: {path}"}
        return {"tree": _snapshot(target)}

    def preview(self, path, ops, opts=None):
        """Run the pipeline on a throwaway copy and return before/after trees.

        The user's real folder is never touched — copytree to a temp dir, run
        the exact same ops there, snapshot, then discard.
        """
        target = Path(path)
        if not target.is_dir():
            return {"error": f"Not a folder: {path}"}
        before = _snapshot(target)
        tmp = tempfile.mkdtemp(prefix="fontadhd_preview_")
        try:
            work = Path(tmp) / target.name
            shutil.copytree(target, work)
            try:
                _run_pipeline(work, ops, opts)
            except ValueError as e:
                return {"error": str(e)}
            after = _snapshot(work)
            # Re-root the after tree under the real folder's name for display.
            after["name"] = target.name
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return {"before": before, "after": after}

    def apply(self, path, ops, opts=None):
        """Run the pipeline on the real folder, return the resulting tree."""
        target = Path(path)
        if not target.is_dir():
            return {"error": f"Not a folder: {path}"}
        try:
            _run_pipeline(target, ops, opts)
        except ValueError as e:
            return {"error": str(e)}
        return {"tree": _snapshot(target)}

    def install(self, path):
        target = Path(path)
        if not target.is_dir():
            return {"error": f"Not a folder: {path}"}
        install_fonts(target, assume_yes=True)
        return {"ok": True}

    # --- session state (survives dev live-reloads) ------------------------
    def remember(self, state):
        """Stash plain UI state (folder, pipeline, opts) on the Python side.

        Only JSON-ish data is stored — never a window/native reference — so the
        frontend can restore itself after a dev reload re-runs the page.
        """
        self._state = state
        return True

    def recall(self):
        return getattr(self, "_state", None)


_WATCH_EXTS = {".html", ".css", ".js"}


def _latest_mtime():
    """Most recent mtime across watched web/ assets (a change token)."""
    latest = 0.0
    for p in WEB_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in _WATCH_EXTS:
            try:
                latest = max(latest, p.stat().st_mtime)
            except OSError:
                pass
    return latest


def _start_dev_server():
    """Serve web/ over localhost with caching disabled, plus a /__mtime change
    token the page polls to live-reload itself.

    WebView2 caches file:// assets, so reloading a file:// URL shows stale
    CSS/JS. Serving over http with 'Cache-Control: no-store' makes every reload
    fetch fresh. The reload is driven by the page (see the dev poller in
    index.html) rather than a cross-thread window.load_url() from Python, which
    is unreliable on the Windows backend. Stdlib only.
    """
    import functools
    import threading
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?", 1)[0] == "/__mtime":
                body = repr(_latest_mtime()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            return super().do_GET()

        def end_headers(self):
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.send_header("Expires", "0")
            super().end_headers()

        def log_message(self, *_):
            pass  # keep the console quiet

    handler = functools.partial(Handler, directory=str(WEB_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    print(f"[fontadhd] dev server on http://127.0.0.1:{port} (live-reload on)")
    return f"http://127.0.0.1:{port}/index.html"


def main(dev=False):
    import webview
    url = _start_dev_server() if dev else str(WEB_DIR / "index.html")
    webview.create_window(
        "fontadhd",
        url,
        js_api=Api(),
        width=1000,
        height=720,
        min_size=(720, 560),
    )
    webview.start(debug=dev)


if __name__ == "__main__":
    import sys
    main(dev="--dev" in sys.argv)
