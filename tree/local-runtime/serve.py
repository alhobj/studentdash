"""Read-only loopback launcher. No directory listings, writes or network binding."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes
import webbrowser

PORT = 8765
ORIGIN = f'http://127.0.0.1:{PORT}'
CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"


def allowed_paths(root):
    assets = json.loads((root / 'assets-manifest.json').read_text(encoding='utf-8'))
    result = {'/': root / 'app/index.html', '/package.json': root / 'package.json', '/results.json': root / 'results.json'}
    for path in assets:
        if not isinstance(path, str) or not path.startswith('assets/') or '..' in path or '\\' in path or Path(path).suffix not in {'.js', '.css'}:
            raise ValueError('Invalid application asset manifest.')
        result['/' + path] = root / 'app' / path
    return result


def handler(root):
    paths = allowed_paths(root)
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *_):
            pass

        def do_GET(self):
            self.reply(False)

        def do_HEAD(self):
            self.reply(True)

        def reply(self, head):
            if self.headers.get('Host') != f'127.0.0.1:{PORT}' or self.headers.get('Sec-Fetch-Site') == 'cross-site' or self.headers.get('Origin', ORIGIN) != ORIGIN:
                self.send_error(403)
                return
            path = paths.get(self.path.split('?', 1)[0])
            if path is None:
                self.send_error(404)
                return
            try:
                # Refuse symlinks escaping the packaged app; personal files are only these two paths.
                resolved = path.resolve(strict=True)
                if not resolved.is_relative_to(root.resolve()):
                    raise OSError('Outside package')
                limit = 2 * 1024 * 1024 if path.name == 'results.json' else 8 * 1024 * 1024
                with path.open('rb') as f:
                    content = f.read(limit + 1)
                if len(content) > limit:
                    raise OSError('File too large')
            except OSError:
                self.send_error(503, 'Local file unavailable; wait for OneDrive to download it')
                return
            self.send_response(200)
            self.send_header('Content-Type', {'.js':'application/javascript','.css':'text/css','.html':'text/html','.json':'application/json'}.get(path.suffix,'application/octet-stream'))
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', CSP)
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            if not head:
                self.wfile.write(content)
    return Handler


def main():
    root = Path(__file__).resolve().parent
    try:
        server = ThreadingHTTPServer(('127.0.0.1', PORT), handler(root))
    except OSError:
        raise SystemExit('Port 8765 is in use. Close the other local viewer and try again. Do not change the port: confidence belongs to this address.')
    print(f'Local student viewer: {ORIGIN}/\nKeep this window open. Ctrl+C stops it.')
    webbrowser.open(ORIGIN + '/')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
