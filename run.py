#!/usr/bin/env python3
"""Run with Python 3.11+. No install, account, network, or API key is required."""
import argparse
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit('Intake Desk needs Python 3.11 or newer. See README.md for setup.')

from backend.database import initialize
from backend.server import create_server
from backend.service import Workshop


def main():
    parser = argparse.ArgumentParser(description='Intake Desk — fictional workshop demo')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--reset', action='store_true', help='Replace local demo data with the original fictional fixtures.')
    args = parser.parse_args()
    path = Path(__file__).resolve().parent / 'data' / 'workshop.sqlite3'
    try:
        # Claim the port before touching the database, especially when resetting.
        server = create_server(Workshop(path), args.port)
    except OSError as error:
        raise SystemExit(f'Could not start on port {args.port}: {error}\nTry: python3 run.py --port 8001')
    if args.reset:
        for suffix in ['', '-wal', '-shm']:
            candidate = Path(str(path) + suffix)
            if candidate.exists():
                candidate.unlink()
    try:
        initialize(path)
    except Exception:
        server.server_close()
        raise
    print(f'\n  Intake Desk · Benchside Repair Collective\n  Open http://127.0.0.1:{args.port}\n  Local demo only. No messages are sent.\n  Press Ctrl+C to stop.\n', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nIntake Desk stopped.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
