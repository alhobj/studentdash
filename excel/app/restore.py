"""Restore a private database to a new location, with the app stopped."""
import argparse
from pathlib import Path
import sqlite3

from .storage import Store, ValidationError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    parser.add_argument('destination', type=Path, help='New, nonexistent destination .sqlite3 file')
    args = parser.parse_args()
    try:
        Store.restore(args.backup, args.destination)
    except (ValidationError, sqlite3.Error, OSError) as exc:
        parser.error(str(exc))
    print('Backup validated and restored. Keep the original backup; start the app only after selecting the restored private directory.')


if __name__ == '__main__':
    main()
