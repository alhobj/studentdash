"""Create or restore a complete selected-course backup into a new folder."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studentdash.config import Config
from studentdash.portability import backup_workspace, restore_workspace

parser = argparse.ArgumentParser(description=__doc__)
sub = parser.add_subparsers(dest='command', required=True)
backup = sub.add_parser('backup')
backup.add_argument('source', type=Path)
backup.add_argument('archive', type=Path)
restore = sub.add_parser('restore')
restore.add_argument('archive', type=Path)
restore.add_argument('new_folder', type=Path)
if __name__ == '__main__':
    args = parser.parse_args()
    if args.command == 'backup':
        content = backup_workspace(Config(args.source.resolve(), Path('output')))
        with args.archive.open('xb') as target:
            target.write(content)
        print('Backup created:', args.archive)
    else:
        config = restore_workspace(args.archive.read_bytes(), args.new_folder)
        print('Restored source:', config.workbook)
        print('Set STUDENTDASH_WORKBOOK to this path and restart the local teacher app.')
