"""Prepare reversible, evidence-labelled repairs and an offline source editor."""
import argparse
import ast
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil

from tools.import_chem_exam_bank import ROOT, SafeMarkup, page

FIELDS = ('Specification', 'Question', 'Markscheme', 'Examiners report')


def parts(raw):
    """Split exported paragraph lists only at explicit outer group boundaries."""
    raw = str(raw or '').strip()
    if len(raw) >= 32767 or not raw.startswith('[[') or not raw.endswith(']]'):
        return None
    return re.split(r'(?<=</p>)\s*\]\s*,\s*\[\s*(?=<)', raw[2:-2])


def list_values(raw):
    try:
        value = ast.literal_eval(str(raw))
        if not isinstance(value, list) or not all(isinstance(v, list) and len(v) == 1 for v in value):
            return []
        return [str(v[0]) for v in value]
    except (ValueError, SyntaxError):
        return []


def clean(raw):
    raw = str(raw or '')
    # Remove only Python-list punctuation outside HTML, never chemical brackets.
    raw = re.sub(r'^\s*\[+(?=<)', '', raw)
    raw = re.sub(r'(?<=>)\s*\]+\s*$', '', raw)
    raw = re.sub(r'(?<=</p>)\s*,\s*(?=<)', '\n', raw)
    raw = re.sub(r'(?<=</p>)\s*\]\s*,\s*\[\s*(?=<)', '\n<hr>\n', raw)
    if len(str(raw)) and re.search(r'<[^>]*$', raw):
        raw = re.sub(r'<[^>]*$', '<p>Source ends here; missing content needs repair.</p>', raw)
    parser = SafeMarkup()
    result = parser.finish(raw.replace('<hr>', '<p>— Next source part —</p>'))
    return result


def suggestions(records):
    groups = defaultdict(list)
    for q in records:
        groups[(q['source_sha256'], q['raw'].get('Reference code', q['id']))].append(q)
    drafts = {}
    for group in groups.values():
        group.sort(key=lambda q: q['source_row'])
        first = group[0]['raw']
        labels = list_values(first.get('Question part'))
        marks = list_values(first.get('Marks for each part'))
        matching = bool(labels) and len(group) == len(labels) == len(marks)
        matching = matching and len(set(labels)) == len(labels)
        matching = matching and all(str(q['raw'].get('Marks available')) == m.strip('[]') for q, m in zip(group, marks))
        matching = matching and all(q['raw'].get('Question part') == first.get('Question part') and
                                    q['raw'].get('Marks for each part') == first.get('Marks for each part') for q in group)
        for index, q in enumerate(group):
            proposed = {f: str(q['raw'].get(f) or '') for f in FIELDS}
            notes = ['Presentation normalized: list separators removed, safe HTML balanced. Original source retained.']
            matched = []
            if matching:
                for field in ('Question', 'Markscheme'):
                    blocks = parts(proposed[field])
                    if blocks and len(blocks) == len(labels) and all(other['raw'].get(field) == first.get(field) for other in group):
                        proposed[field] = blocks[index]
                        matched.append(field)
                if matched:
                    notes.append('INFERRED part '+labels[index]+': source row order, part count and marks agree. Matched '+', '.join(matched)+'. Check against the full source before approving.')
            if q['raw'].get('Question part') and len(matched) != 2:
                notes.append('Part alignment remains unresolved for one or both question/markscheme fields; grouped content is retained where unresolved.')
            context = parts(proposed['Specification'])
            if context and len(context) == 1:
                proposed['Specification'] = context[0]
            if proposed['Examiners report'] not in ('', '-') and q['raw'].get('Question part'):
                notes.append('Examiner-report field retained as a group; source may contain shifted or mislabeled answers.')
            drafts[q['id']] = dict(id=q['id'], fields={f:clean(v) for f,v in proposed.items()},
                                  part=labels[index] if matched else '', inferred=bool(matched),
                                  notes=notes, original={f:str(q['raw'].get(f) or '') for f in FIELDS},
                                  issues=q['issues'], siblings=[other['id'] for other in group],
                                  provenance={k:q[k] for k in ('source_file','source_sheet','source_row','source_id')})
    return drafts


def prepare(folder):
    folder = Path(folder).resolve()
    if not folder.is_relative_to(ROOT/'output'):
        raise ValueError('Repair bank must remain in local output.')
    bank = json.loads((folder/'bank.json').read_text(encoding='utf-8'))
    drafts = suggestions(bank['questions'])
    fingerprint = sha256(json.dumps(bank['manifest']['sources'], sort_keys=True).encode()).hexdigest()
    (folder/'repair-data').mkdir(exist_ok=True)
    for key, draft in drafts.items():
        (folder/'repair-data'/f'{key}.js').write_text('window.receiveQuestion('+json.dumps(draft, ensure_ascii=True)+');', encoding='utf-8')
    report = dict(records=len(drafts), inferred_records=sum(d['inferred'] for d in drafts.values()),
                  inferred_complete_pairs=sum(d['inferred'] and 'Matched Question, Markscheme.' in ' '.join(d['notes']) for d in drafts.values()),
                  status='All suggestions require teacher review; original warnings retained.')
    (folder/'repair-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    labels = {key: {'part': d['part'], 'source': d['provenance']['source_id']} for key, d in drafts.items()}
    (folder/'repair-config.js').write_text('const bankFingerprint = '+json.dumps(fingerprint)+';\nconst repairLabels = '+json.dumps(labels)+';', encoding='utf-8')
    for name in ('repair.js', 'repair.css'):
        shutil.copyfile(ROOT/'tools'/'exam_bank_assets'/name, folder/name)
    body = '''<a href="index.html">Original bank</a><h1>Repair exam questions</h1>
<p>Suggestions are drafts. Source records and student pages are unchanged. Saves stay in this browser; export a corrections file to keep a portable backup.</p>
<div class="actions"><button id="export">Export all corrections</button><label>Import corrections <input type="file" id="import" accept=".json"></label></div>
<p id="message" role="status"></p><label>Find reference, topic or wording <input id="find" type="search"></label>
<label>Show <select id="filter"><option value="all">All records</option><option value="warning">Source warnings</option><option value="saved">Saved corrections</option><option value="unreviewed">Not approved</option></select></label>
<label>Question <select id="questions"></select></label><div class="actions"><button id="previous">Previous</button><button id="next">Next</button></div>
<section id="work" hidden><h2 id="title"></h2><p id="provenance"></p><div id="notes"></div><div id="siblings"></div>
<label>Field <select id="field"><option>Specification</option><option>Question</option><option>Markscheme</option><option>Examiners report</option></select></label>
<div class="columns"><div><label>Editable HTML source <textarea id="source" spellcheck="false"></textarea></label>
<details><summary>Original source (unchanged)</summary><pre id="original"></pre></details></div>
<div><h3>Preview of selected field</h3><iframe id="preview" title="Safe source preview" sandbox=""></iframe></div></div>
<label>Repair notes / replacement source reference <textarea id="repairNotes" rows="3"></textarea></label>
<label>Review status <select id="status"><option value="draft">Draft</option><option value="needs-source">Needs better source</option><option value="approved">Teacher approved</option></select></label>
<div class="actions"><button id="save">Save correction</button><button id="suggestion">Restore suggested field</button><button id="restore">Restore original field</button><button id="download">Download corrected question HTML</button></div>
<p>Approval is your review decision. Source warnings remain visible even after approval. Exported corrections do not automatically replace the original bank.</p></section>
<script src="catalog.js"></script><script src="repair-config.js"></script><script src="repair.js"></script>'''
    html = page('Repair exam questions', body).replace("script-src 'self';", "script-src 'self'; frame-src 'self' about:;").replace('</main>', '</main><link rel="stylesheet" href="repair.css">')
    (folder/'repair.html').write_text(html, encoding='utf-8')
    index = folder/'index.html'
    text = index.read_text(encoding='utf-8')
    if 'href="repair.html"' not in text:
        index.write_text(text.replace('<h1>', '<p><a href="repair.html">Repair questions and review suggestions</a></p><h1>', 1), encoding='utf-8')
    for key in drafts:
        file = folder/'questions'/f'{key}.html'
        text = file.read_text(encoding='utf-8')
        if '../repair.html#' not in text:
            file.write_text(text.replace('<h1>', '<p><a href="../repair.html#'+key+'">Edit source / review suggested repair</a></p><h1>', 1), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', nargs='?', default=ROOT/'output'/'chemistry-exam-bank')
    print(json.dumps(prepare(parser.parse_args().folder), indent=2))
