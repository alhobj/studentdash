"""Add a repeatable fictional ticket draft; never replace existing work or submissions."""
import argparse
from pathlib import Path

from studentdash.config import Config, ROOT
from studentdash.excel import read_workbook
from studentdash.exit_schema import parse_ticket
from studentdash.exit_store import TicketRepository
from studentdash.exit_tickets import TicketService


def seed(config):
    raw = (ROOT / 'examples' / 'exit-ticket.json').read_text(encoding='utf-8')
    parsed = parse_ticket(raw)
    repository = TicketRepository(config.workspace)
    existing = next((t for t in repository.list() if t['title'] == parsed['title']), None)
    if existing:
        return existing['id'], False
    data = read_workbook(config.workbook)
    ticket_id = TicketService(repository).save(raw, ['all'], data.students)
    return ticket_id, True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', type=Path, help='Fictional workbook to seed; defaults to the configured workbook.')
    args = parser.parse_args()
    config = Config.from_env()
    if args.workbook:
        config = Config(args.workbook.resolve(), config.output)
    ticket_id, created = seed(config)
    print(f'{"Created fictional draft" if created else "Kept existing fictional ticket"}: {ticket_id}')
    print('Open the teacher Exit Tickets area to preview and publish. No submissions were invented.')
