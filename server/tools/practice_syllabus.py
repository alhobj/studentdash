"""Render syllabus references from resource-profile data, without core curriculum rules."""
import json
from html import escape
from practice_booklets import booklet_link
from practice_skills import load_skills


def render_cross_references(data, references, code, expanded=False):
    """Keep source direction and qualifiers; guide-only targets have no local proxy."""
    links = references['sections'][code]
    if not links:
        return ''
    targets = references['targets']
    parts = []
    for link in links:
        target = targets[link['target']]
        label = target['label']
        if link.get('qualifier'):
            label += ' (' + link['qualifier'] + ')'
        if target.get('guide_only'):
            label += ' · guide'
        parts.append('<a href="' + escape(target['href'], quote=True) + '">'
                     + escape(label) + '</a>')
    pages = sorted({page for link in links for page in link['source_pages']})
    # The profile supplies both page numbering systems, including their offset.
    row = data['sections'][code]
    offset = row['pdf_page'] - row['printed_page']
    sources = ', '.join('<a href="' + escape(data['copy_url'], quote=True)
                        + '#page=' + str(page) + '">' + str(page - offset) + '</a>'
                        for page in pages)
    return ('<details class="syllabus-cross-references"' + (' open' if expanded else '')
            + '><summary>Syllabus cross-references (' + str(len(links)) + ')</summary>'
            '<nav aria-label="Cross-references for ' + escape(row['label'], quote=True) + '">'
            + ''.join(parts) + '</nav><p class="syllabus-source">'
            + escape(references['note']) + ' References appear on guide page(s) '
            + sources + '.</p></details>')


def render_syllabus(root, codes):
    data = json.loads((root / 'syllabus-reference.json').read_text(encoding='utf-8'))
    references = json.loads((root / 'syllabus-cross-references.json').read_text(encoding='utf-8'))
    skills=load_skills(str(root))
    if skills:
        for key in skills.get("cross_reference_groups", {}):
            if key in references["targets"]:
                references["targets"][key]["href"]="skills-practice.html#group-"+key
                references["targets"][key]["guide_only"]=False
    codes = list(codes)
    items = []
    for code in codes:
        row = data['sections'][code]
        url = data['copy_url'] + '#page=' + str(row['pdf_page'])
        items.append(
            '<li><strong>' + escape(row['label']) + '</strong> '
            '<span class="syllabus-level">' + escape(row['level']) + '</span>'
            '<p>' + escape(row['summary']) + '</p>'
            '<a href="' + escape(url, quote=True) + '">Read syllabus content '
            '(guide p. ' + str(row['printed_page']) + ' onwards)</a>'
            + render_cross_references(data, references, code, len(codes) == 1) + '</li>')
    return (
        '<aside class="syllabus-reference" aria-label="Official IB syllabus reference">'
        '<h2>Official IB syllabus reference</h2><p>' + escape(data['title']) + ' · '
        + escape(data['edition']) + '</p><p>Brief study summaries below are paraphrases, '
        'not the official wording or a complete checklist. Open the linked guide section for '
        'the full content and guidance. These practice activities are independently written.</p>'
        '<p>Companion reference: ' + booklet_link(root) + '</p>'
        '<ul>' + ''.join(items) + '</ul><p class="syllabus-source">'
        '<a href="' + escape(data['official_url'], quote=True) + '">IB guide download</a>'
        ' · Section links open an IB-authored guide hosted by ' + escape(data['copy_host'])
        + '. Guide links require internet; practice works offline.</p></aside>')
