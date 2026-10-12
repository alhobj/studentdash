"""Import legacy Chemistry exports into an offline teacher reference bank.

Source adapter only: no current-curriculum mappings or student assets are changed.
"""
import argparse
import base64
from collections import Counter
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.migrate_exam_databases import inspect

ROOT = Path(__file__).resolve().parents[1]
TAGS = set('p br sub sup strong em b i u table thead tbody tr td th ul ol li span div math mrow mi mn mo mtext msub msup msubsup mfrac msqrt mroot mfenced mtable mtr mtd munder mover munderover mmultiscripts mprescripts none mspace'.split())
VOID = {'br', 'mspace', 'mprescripts', 'none'}


class SafeMarkup(HTMLParser):
    """Retain chemistry formatting, never source scripts, URLs or attributes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output, self.stack, self.issues = [], [], set()

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            src = dict(attrs).get('src', '')
            try:
                payload = base64.b64decode(src.removeprefix('data:image/png;base64,'), validate=True)
                if not src.startswith('data:image/png;base64,') or not payload.startswith(b'\x89PNG\r\n\x1a\n') or b'IEND' not in payload[-20:]:
                    raise ValueError()
                self.output.append('<img alt="Source diagram" src="'+escape(src, quote=True)+'">')
            except (ValueError, TypeError):
                self.issues.add('Missing, external or incomplete diagram')
                self.output.append('<p class="warning">Diagram unavailable in this export.</p>')
        elif tag in TAGS:
            self.output.append('<'+tag+'>')
            if tag not in VOID:
                self.stack.append(tag)
        else:
            self.issues.add('Unsupported source markup omitted')

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                current = self.stack.pop()
                self.output.append('</'+current+'>')
                if current == tag:
                    break

    def handle_data(self, data):
        self.output.append(escape(data))

    def finish(self, raw):
        self.feed(str(raw or ''))
        self.close()
        if self.stack:
            self.issues.add('Unclosed source markup; content may be incomplete')
        self.output.extend('</'+tag+'>' for tag in reversed(self.stack))
        return ''.join(self.output)


def page(title, body, prefix=''):
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'self\'; script-src \'self\'; base-uri \'none\'; form-action \'none\'">'
            '<title>'+escape(title)+'</title><link rel="stylesheet" href="'+prefix+'bank.css">'
            '<main>'+body+'</main></html>')


def build(sources, destination):
    destination = Path(destination).resolve()
    # Only local ignored output is supported; never permit a public resource bank.
    if not destination.is_relative_to(ROOT / 'output'):
        raise ValueError('The teacher bank must be inside the local output directory.')
    if destination.exists():
        raise ValueError('Destination already exists. Choose a new directory to preserve prior imports.')
    loaded = [(Path(p), inspect(Path(p))) for p in sources]
    hashes = {str(p): sha256(p.read_bytes()).hexdigest() for p, _ in loaded}
    if len(set(hashes.values())) != len(loaded):
        raise ValueError('The same workbook was supplied more than once.')
    records, manifest, summaries = [], [], []
    destination.mkdir(parents=True)
    (destination / 'questions').mkdir()
    (destination / 'sources').mkdir()
    for source, rows in loaded:
        digest = hashes[str(source)]
        archive_name = digest[:12]+'-'+source.name
        shutil.copyfile(source, destination / 'sources' / archive_name)
        manifest.append(dict(file=source.name, sha256=digest, records=len(rows), archive='sources/'+archive_name))
        for row in rows:
            qid = str(row['URL number'])
            key = digest[:12]+'-'+sha256(qid.encode()).hexdigest()[:16]
            issues = set()
            limit_fields = [k for k, v in row.items() if isinstance(v, str) and len(v) >= 32767]
            if limit_fields:
                issues.add('Possible Excel cell truncation: '+', '.join(limit_fields))
            if row.get('Question part'):
                issues.add('Grouped source parts: question, marks and answers need manual matching')
            fragments = {}
            for field in ('Specification', 'Question', 'Markscheme', 'Examiners report'):
                parser = SafeMarkup()
                fragments[field] = parser.finish(row.get(field))
                issues.update(parser.issues)
            title = str(row.get('Reference code') or qid)
            metadata = {k: row.get(k) for k in ('Date', 'Paper', 'Level', 'Marks available', 'Question part', 'Marks for each part', 'Syllabus section') if k in row}
            record = dict(id=key, source_id=qid, source_file=source.name, source_sha256=digest,
                          source_sheet=row['_sheet'], source_row=row['_row'], raw=row,
                          current_curriculum_status='unreviewed', issues=sorted(issues))
            records.append(record)
            body = '<a href="../index.html">Back to question bank</a><h1>'+escape(title)+'</h1>'
            body += '<p>Legacy syllabus. Current syllabus mapping has not been reviewed.</p>'
            body += '<p>'+escape(f'{source.name} / {row["_sheet"]} / row {row["_row"]} / source ID {qid}')+'</p>'
            body += '<dl>'+''.join('<dt>'+escape(k)+'</dt><dd>'+escape(str(v or '—'))+'</dd>' for k,v in metadata.items())+'</dl>'
            body += ''.join('<p class="warning">'+escape(i)+'</p>' for i in sorted(issues))
            body += '<h2>Context</h2>'+fragments['Specification']+'<h2>Question</h2>'+fragments['Question']
            body += '<details><summary>Show source markscheme</summary>'+fragments['Markscheme']+'</details>'
            body += '<details><summary>Show source examiner report</summary>'+fragments['Examiners report']+'</details>'
            (destination/'questions'/f'{key}.html').write_text(page(title, body, '../'), encoding='utf-8')
            summaries.append(dict(id=key, title=title, paper=str(row.get('Paper') or ''), level=str(row.get('Level') or ''),
                                  topic=str(row.get('Syllabus section') or ''), date=str(row.get('Date') or ''),
                                  review=bool(issues), text=re.sub('<[^>]*>', ' ', str(row.get('Question') or ''))[:4000]))
    for source, _ in loaded:
        if sha256(source.read_bytes()).hexdigest() != hashes[str(source)]:
            raise ValueError('Source changed during import: '+str(source))
    report = dict(schema_version=1, sources=manifest, records=len(records),
                  records_with_issues=sum(bool(r['issues']) for r in records),
                  issues=dict(Counter(i for r in records for i in r['issues'])))
    (destination/'bank.json').write_text(json.dumps(dict(manifest=report, questions=records), ensure_ascii=False), encoding='utf-8')
    (destination/'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    (destination/'catalog.js').write_text('const catalog = '+json.dumps(summaries, ensure_ascii=True)+';', encoding='utf-8')
    assets = ROOT/'tools'/'exam_bank_assets'
    for name in ('bank.css', 'bank.js'):
        shutil.copyfile(assets/name, destination/name)
    body = '<h1>Chemistry exam question bank</h1><p>Teacher reference · '+str(len(records))+' source records</p>'
    body += '<p>Legacy syllabus content, including options. Not linked or included in student downloads. Review warnings before using questions.</p>'
    body += '<label>Search wording, reference or topic <input id="search" type="search"></label>'
    for key,label in [('paper','Paper'),('level','Level')]:
        body += '<label>'+label+' <select id="'+key+'"><option value="">All</option></select></label>'
    body += '<label><input id="review" type="checkbox"> Only records with source warnings</label><p id="count" role="status"></p><div id="results"></div><button id="more">Show more</button>'
    body += '<script src="catalog.js"></script><script src="bank.js"></script>'
    (destination/'index.html').write_text(page('Chemistry exam question bank',body), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'output'/'chemistry-exam-bank')
    args = parser.parse_args()
    print(json.dumps(build(args.sources, args.output), indent=2))
