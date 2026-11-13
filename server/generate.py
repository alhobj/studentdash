import argparse

from studentdash.config import Config
from studentdash.excel import WorkbookError
from studentdash.render import generate_dashboards


def main():
    parser = argparse.ArgumentParser(description='Generate private, standalone student dashboards.')
    parser.add_argument('--no-examples', action='store_true', help='Omit fictional question practice.')
    args = parser.parse_args()
    config = Config.from_env()
    print(f'Workbook: {config.workbook}')
    try:
        data, names = generate_dashboards(config, include_examples=not args.no_examples)
    except (WorkbookError, OSError) as exc:
        parser.exit(1, f'Generation failed: {exc}\n')
    print(f'Generated {len(names)} dashboards in {config.output}')
    for warning in data.warnings:
        print(f'Warning: {warning}')


if __name__ == '__main__':
    main()
