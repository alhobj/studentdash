"""Render authored lookup, unit-selection and calculation practice."""
import json
import math
from html import escape
from pathlib import Path


def build_booklet_tasks(root, booklet):
    packs = json.loads((root / 'booklet-practice.json').read_text(encoding='utf-8'))
    entries = {e['id']: e for e in booklet['entries']}
    assert len({p['id'] for p in packs}) == len(packs)
    body = ('<header><a href="' + escape(booklet['hub']) + '">← Practice hub</a><h1>Practise using your booklet</h1>'
            '<p>Find the right entry, choose the requested unit or answer type, then calculate. Each set has three '
            'similar questions: a guided setup, a short cue, then an independent attempt. More support is always available.</p>'
            '<p>Use the supplied values. Numerical answers allow 0.1% rounding tolerance; give at least three significant '
            'figures when rounding. You may skip or repeat questions. Nothing is saved and there is no timer.</p>'
            '<p><a href="' + escape(booklet['filename']) + '">Browse the booklet companion</a></p></header>'
            '<nav aria-label="Lookup practice sets">' + ''.join('<a href="#' + escape(p['id']) + '">'
                + escape(p['title']) + '</a>' for p in packs) + '</nav>')
    for pack in packs:
        key = pack['id']
        assert len(pack['questions']) == 3
        assert pack['reference'] in {c['id'] for c in pack['choices']}
        assert pack['unit'] in {u['label'] for u in pack['units']}
        assert all(c['id'] in entries for c in pack['choices'])
        for q in pack['questions']:
            assert math.isfinite(q['answer']) and q['hint'] and q['cue'] and q['working']
            assert all(not math.isclose(a['value'], b['value'], rel_tol=.001, abs_tol=1e-8)
                       for i, a in enumerate(q['mistakes']) for b in q['mistakes'][i+1:]), 'Ambiguous diagnostic values'
            assert all(math.isfinite(m['value']) and not math.isclose(m['value'], q['answer'], rel_tol=.001, abs_tol=1e-8)
                       for m in q['mistakes'])
        first = pack['questions'][0]
        payload = escape(json.dumps(pack, ensure_ascii=False), quote=True)
        body += ('<section id="' + key + '" data-booklet-task="' + payload + '"><h2 tabindex="-1">'
                 + escape(pack['title']) + '</h2><p class="lookup-position">Question 1 of 3 · Guided setup</p>'
                 '<p class="lookup-prompt">' + escape(first['prompt']) + '</p>'
                 '<p class="lookup-guidance">' + escape(first['hint']) + '</p>'
                 '<details class="lookup-support"><summary>More support</summary><p>' + escape(first['hint']) + '</p></details>'
                 '<details><summary>Browse possible booklet entries</summary><nav aria-label="Booklet choices">'
                 + ''.join('<a href="' + escape(booklet['filename']) + '#' + escape(c['id']) + '" target="_blank" rel="noopener">'
                     + escape(entries[c['id']]['title']) + ' (new tab)</a>' for c in sorted(pack['choices'], key=lambda c: entries[c['id']]['title']))
                 + '</nav></details><form class="lookup-form" novalidate>'
                 '<label for="' + key + '-reference">1. Which booklet entry fits?</label><select id="' + key + '-reference" class="lookup-reference" aria-describedby="' + key + '-feedback">'
                 '<option value="">Choose an entry</option>'
                 + ''.join('<option value="' + escape(c['id']) + '">' + escape(entries[c['id']]['title']) + '</option>'
                           for c in sorted(pack['choices'], key=lambda c: entries[c['id']]['title']))
                 + '</select><label for="' + key + '-unit">2. Which unit or answer type is requested?</label>'
                 '<select id="' + key + '-unit" class="lookup-unit" aria-describedby="' + key + '-feedback"><option value="">Choose a unit or type</option>'
                 + ''.join('<option>' + escape(u['label']) + '</option>' for u in sorted(pack['units'], key=lambda u: u['label']))
                 + '</select><label for="' + key + '-answer">3. Your numerical answer</label>'
                 '<input type="number" step="any" id="' + key + '-answer" class="lookup-answer" aria-describedby="' + key + '-feedback">'
                 '<button type="submit" hidden>Check my choices and answer</button>'
                 '<p id="' + key + '-feedback" class="lookup-feedback feedback" role="status"></p></form>'
                 '<details class="lookup-working"><summary>Show worked answer</summary><p>' + escape(first['working']) + '</p></details>'
                 '<div class="lookup-controls" hidden><button type="button" class="lookup-previous" disabled>Previous</button>'
                 '<button type="button" class="lookup-next">Next question</button><button type="button" class="lookup-reset">Restart set</button></div>'
                 '<details class="lookup-worksheet"><summary>Read all questions and solutions</summary>')
        for i, q in enumerate(pack['questions'], 1):
            body += '<h3>Question ' + str(i) + '</h3><p>' + escape(q['prompt']) + '</p><details><summary>Solution</summary><p>'
            body += escape(entries[pack['reference']]['title'] + '; ' + pack['unit'] + '. ' + q['working']) + '</p></details>'
        body += '</details><noscript><p>Enable JavaScript to check answers. All questions and solutions are available above.</p></noscript></section>'
    (root / 'booklet-practice.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Booklet lookup practice</title><link rel="stylesheet" href="' + escape(booklet['stylesheet']) + '"></head><body><main>'
        + body + '</main><script src="booklet-practice.js"></script></body></html>\n', encoding='utf-8')
    (root / 'booklet-practice.js').write_text(Path(__file__).with_name('booklet-practice.js').read_text(encoding='utf-8'), encoding='utf-8')
