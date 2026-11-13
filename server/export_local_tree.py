"""Teacher-side export of one learner's local tree package; source stays private."""
import argparse
from pathlib import Path
import time

from studentdash.excel import read_workbook
from studentdash.local_tree import export_package, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='Private workbook (.xlsx) or class (.sdclass)')
    parser.add_argument('--student', required=True, help='One exact existing student ID')
    parser.add_argument('--mapping', required=True, type=Path, help='Teacher-reviewed JSON: question ID to one directly assessed node ID')
    parser.add_argument('--viewer', required=True, type=Path, help='Chemistree local-package build folder')
    parser.add_argument('--destination', required=True, type=Path, help='Individual restricted OneDrive folder')
    parser.add_argument('--watch', action='store_true', help='Re-read saved source/mapping changes every 10 seconds')
    args = parser.parse_args()
    previous = None
    while True:
        try:
            fingerprint = tuple((path.stat().st_mtime_ns, path.stat().st_size) for path in (args.source, args.mapping))
            if fingerprint != previous:
                data, mapping = read_workbook(args.source), read_json(args.mapping)
                if fingerprint != tuple((path.stat().st_mtime_ns, path.stat().st_size) for path in (args.source, args.mapping)):
                    raise ValueError('Source changed during export. Retry after it has finished saving.')
                result = export_package(data, args.student, mapping, args.viewer, args.destination)
                print(f"Revision {result['revision']}: {result['questions']} mapped graded questions. " + ('Updated.' if result['changed'] else 'Unchanged.'))
                previous = fingerprint
        except (OSError, ValueError) as exc:
            if not args.watch:
                parser.exit(1, f'Export failed; existing results retained: {exc}\n')
            print(f'Waiting; existing results retained: {exc}')
        if not args.watch:
            return
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            return


if __name__ == '__main__':
    main()
