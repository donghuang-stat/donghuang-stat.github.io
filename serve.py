#!/usr/bin/env python3
"""Preview locally; rebuild saved Markdown automatically when the browser refreshes."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import subprocess
import sys
from threading import Lock
from urllib.parse import urlsplit


class Rebuilder:
    def __init__(self, root):
        self.root = root
        self.last_attempt = None
        self.lock = Lock()

    def fingerprint(self):
        files = [self.root / name for name in
                 ('home.md', 'research.md', 'news.md', 'build.py', 'content.py')]
        result = []
        for path in files:
            try:
                stat = path.stat()
                result.append((str(path.relative_to(self.root)), stat.st_mtime_ns, stat.st_size))
            except FileNotFoundError:
                result.append((str(path.relative_to(self.root)), None, None))
        return tuple(result)

    def refresh(self):
        # A request can arrive for each page and asset; build only once per edit.
        with self.lock:
            fingerprint = self.fingerprint()
            if fingerprint == self.last_attempt:
                return
            self.last_attempt = fingerprint
            print('Building Markdown content…', flush=True)
            try:
                result = subprocess.run([sys.executable, 'build.py'], cwd=self.root,
                                        capture_output=True, text=True)
            except OSError as exc:
                print(f'Build failed; keeping the last generated pages. {exc}', file=sys.stderr, flush=True)
                return
            if result.returncode:
                detail = '\n'.join(part.strip() for part in (result.stderr, result.stdout) if part.strip())
                print(f'Build failed; keeping the last generated pages.\n{detail}\n'
                      'Fix the content, save, and refresh to retry.', file=sys.stderr, flush=True)
            else:
                print('Build complete. Refresh after saving Markdown to see your changes.', flush=True)


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, rebuilder, **kwargs):
        self.rebuilder = rebuilder
        super().__init__(*args, **kwargs)

    def send_head(self):
        path = urlsplit(self.path).path
        if not path or path.endswith(('/', '.html')):
            self.rebuilder.refresh()
            # A rebuild may happen within one second of the previous response.
            if 'If-Modified-Since' in self.headers:
                del self.headers['If-Modified-Since']
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4173, help='Local preview port (default: 4173)')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    rebuilder = Rebuilder(root)
    handler = partial(PreviewHandler, directory=str(root), rebuilder=rebuilder)
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except OSError as exc:
        parser.exit(1, f'Cannot start preview on port {args.port}: {exc}\nTry --port 4174.\n')
    rebuilder.refresh()
    print(f'Local preview: http://127.0.0.1:{args.port}/', flush=True)
    print('Edit home.md, research.md, or news.md, save, and refresh. Pages rebuild automatically.', flush=True)
    print('Press Control-C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
