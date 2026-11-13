"""Prepare and open the combined local app."""
import argparse
from pathlib import Path
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prepare import prepare

parser = argparse.ArgumentParser()
parser.add_argument('--no-browser', action='store_true')
parser.add_argument('--prepared', action='store_true')
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=5000)
args = parser.parse_args()
if not args.prepared:
    prepare()
from arborsynapse import create_app
from waitress import serve
app = create_app()
address = f'http://127.0.0.1:{args.port}/classes'
print('ArborSynapse: ' + address, flush=True)
if not args.no_browser:
    threading.Timer(1, lambda: webbrowser.open(address)).start()
serve(app, host=args.host, port=args.port, threads=4, max_request_body_size=110 * 1024 * 1024)
