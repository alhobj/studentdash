"""Build offline booklet companions using profile-local references and mappings."""
import json
from html import escape
from practice_booklet_tasks import build_booklet_tasks


def load_booklet(root):
    return json.loads((root / 'booklet.json').read_text(encoding='utf-8'))


def booklet_link(root):
    data = load_booklet(root)
    return ('<a href="' + escape(data['filename']) + '">' + escape(data['title']) + '</a>'
            ' · <a href="booklet-practice.html">Practise using the booklet</a>')


def render_booklet_help(root, codes=(), prior=None):
    codes = list(codes)
    data = load_booklet(root)
    selected = list(dict.fromkeys(key for code in codes for key in data['sections'].get(code, [])))
    if prior:
        selected += [key for key in data.get('prior', {}).get(prior, []) if key not in selected]
    if not selected:
        return ''
    entries = {entry['id']: entry for entry in data['entries']}
    parts = []
    for key in selected:
        entry = entries[key]
        parts.append('<div class="booklet-help-entry"><a href="' + escape(data['filename'])
                     + '#' + escape(key) + '">' + escape(entry['title']) + '</a>'
                     + ('<p class="booklet-formula">' + escape(entry['formula']) + '</p>' if entry['formula'] else '')
                     + '<p>' + escape(entry['note']) + '</p></div>')
    packs = json.loads((root / 'booklet-practice.json').read_text(encoding='utf-8'))
    practice = ''.join('<p><a href="booklet-practice.html#' + escape(p['id']) + '">Practise: '
                       + escape(p['title']) + '</a></p>' for p in packs if set(codes) & set(p['codes']))
    return ('<details class="booklet-help"><summary>Booklet help: formulas and data</summary>'
            '<p>Related references for this section. Use values and assumptions stated in the question.</p>'
            + ''.join(parts) + practice + '</details>')


def build_booklet(root):
    data = load_booklet(root)
    build_booklet_tasks(root, data)
    packs = json.loads((root / 'booklet-practice.json').read_text(encoding='utf-8'))
    targets = json.loads((root / 'syllabus-cross-references.json').read_text(encoding='utf-8'))['targets']
    assert len({e['id'] for e in data['entries']}) == len(data['entries'])
    entries = {e['id']: e for e in data['entries']}
    assert all(key in entries for values in data['sections'].values() for key in values)
    body = ('<header><a href="' + escape(data['hub']) + '">← Practice hub</a><h1>'
            + escape(data['title']) + '</h1><p>' + escape(data['edition']) + '</p>'
            '<p>This is an independent study companion, with selected formulas, brief reminders and '
            'links to the IB-authored booklet. It does not reproduce or replace the full booklet.</p><p>'
            + escape(data['scope']) + '</p><p><a href="' + escape(data['url'], quote=True)
            + '">Open the full IB booklet (PDF)</a> · Copy hosted by ' + escape(data['host'])
            + '.</p><p>The notes below work offline. PDF links require internet. '
            'For examinations, use the current clean copy supplied by your school.</p>'
            '<p><a href="booklet-practice.html">Practise finding entries, choosing units and calculating →</a></p></header>'
            '<nav aria-label="Booklet contents">'
            + ''.join('<a href="#' + escape(e['id']) + '">' + escape(e['title']) + '</a>' for e in data['entries'])
            + '</nav>')
    for entry in data['entries']:
        related = [code for code, keys in data['sections'].items() if entry['id'] in keys]
        body += ('<section class="booklet-entry" id="' + escape(entry['id']) + '"><h2>'
                 + escape(entry['title']) + '</h2><p class="eyebrow">Booklet '
                 + escape(entry['section']) + ' · printed page ' + str(entry['pdf_page'] - data['page_offset'])
                 + '</p>'
                 + ('<p class="booklet-formula">' + escape(entry['formula']) + '</p>' if entry['formula'] else '')
                 + '<p>' + escape(entry['note']) + '</p><p><a href="' + escape(data['url'], quote=True)
                 + '#page=' + str(entry['pdf_page']) + '">Open this part of the booklet</a></p>')
        if related:
            body += '<nav aria-label="Practise with ' + escape(entry['title'], quote=True) + '">' + ''.join(
                '<a href="' + escape(targets[c]['href'], quote=True) + '">' + escape(targets[c]['label']) + '</a>' for c in related) + '</nav>'
        body += ''.join('<p><a href="booklet-practice.html#' + escape(p['id']) + '">Guided to independent practice: '
                        + escape(p['title']) + '</a></p>' for p in packs if p['reference'] == entry['id'])
        body += '</section>'
    text = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>'
            + escape(data['title']) + '</title><link rel="stylesheet" href="' + escape(data['stylesheet'])
            + '"></head><body><main>' + body + '<footer><a href="' + escape(data['hub'])
            + '">Return to practice</a></footer></main></body></html>\n')
    (root / data['filename']).write_text(text, encoding='utf-8')
