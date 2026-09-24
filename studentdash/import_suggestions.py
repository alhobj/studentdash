"""Replaceable, profile-driven suggestion interface; no subject vocabulary in code.

The initial provider uses explicit signals and definition/keyword overlap, not an
LLM. Confidence values are heuristic strengths, never calibrated probabilities.
"""
import math
import re
from typing import Protocol

from .entry import EntryError


class SuggestionProvider(Protocol):
    def suggest(self, question: dict, context: str, profile: dict) -> list[dict]: ...


def curriculum_nodes(profile):
    nodes = profile.get('curriculum', {}).get('nodes', [])
    index = {}
    for node in nodes:
        key = node.get('id')
        if not isinstance(key, str) or not key or key in index or not node.get('label'):
            raise EntryError('The course curriculum has missing or duplicate node references.')
        index[key] = node
    for node in nodes:
        seen, current = set(), node
        while current.get('parent'):
            key = current['parent']
            if key not in index or key in seen or key == node['id']:
                raise EntryError('The course curriculum has an invalid parent relationship.')
            seen.add(key)
            current = index[key]
    return index


def valid_suggestion(suggestion, profile):
    confidence = suggestion.get('confidence')
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        return False
    if suggestion.get('source') not in {'existing', 'rule', 'inferred', 'teacher'}:
        return False
    if suggestion.get('kind') == 'curriculum':
        return suggestion.get('value') in curriculum_nodes(profile)
    return (suggestion.get('kind') == 'tag' and suggestion.get('category') in profile['categories']
            and suggestion.get('value') in profile['categories'][suggestion['category']])


def tokens(value):
    return {word for word in re.findall(r'\w+', value.lower()) if len(word) > 3}


class ProfileSuggestionProvider:
    name = 'local-profile-evidence-v1'

    def suggest(self, question, context, profile):
        own = question.get('text', '')
        combined = own + '\n' + context
        candidates = []

        def add(kind, value, source, confidence, reason, category=None):
            candidate = dict(kind=kind, value=value, category=category, source=source,
                             confidence=confidence, reason=reason)
            if valid_suggestion(candidate, profile):
                candidates.append(candidate)

        command_category = profile.get('command_category')
        for term in profile['categories'].get(command_category, []):
            if re.search(r'^\s*' + re.escape(term) + r'\b', own, re.I | re.M):
                add('tag', term, 'rule', .97, f'Explicit instruction: {term}.', command_category)
        for rule in profile.get('suggestion_rules', []):
            hit = re.search(rule['pattern'], own, re.I | re.S) if rule.get('pattern') else None
            in_context = not hit and rule.get('pattern') and re.search(rule['pattern'], context, re.I | re.S)
            feature = rule.get('feature')
            feature_hit = (feature == 'table' and bool(question.get('tables'))) or (feature == 'figure' and bool(question.get('figures')))
            if hit or in_context or feature_hit:
                confidence = min(float(rule.get('confidence', .7)), .7) if in_context else float(rule.get('confidence', .7))
                source = 'inferred' if in_context else rule.get('source', 'rule')
                evidence = 'parent context' if in_context else 'source table/figure' if feature_hit else repr(hit.group(0)[:100])
                add('tag', rule['tag'], source, confidence, f"Configured signal in {evidence}.", rule['category'])
        # Definitions are optional configuration; low-confidence overlap is always reviewable.
        evidence_tokens = tokens(combined)
        for category, tags in profile.get('tag_definitions', {}).items():
            for tag, definition in tags.items():
                definition = {'definition': definition} if isinstance(definition, str) else definition
                hits = [word for word in definition.get('keywords', []) if re.search(r'\b' + re.escape(word) + r'\b', combined, re.I)]
                shared = evidence_tokens & tokens(definition.get('definition', ''))
                if hits or len(shared) >= 2:
                    strength = min(.84, .55 + .07 * len(hits) + .03 * len(shared))
                    add('tag', tag, 'inferred', strength, 'Definition/keyword overlap: ' + ', '.join(hits or sorted(shared)), category)
        for key, node in curriculum_nodes(profile).items():
            code = node.get('code', '')
            if code and re.search(r'(?<!\w)' + re.escape(code) + r'(?!\w)', combined, re.I):
                add('curriculum', key, 'existing', .97, f'Source explicitly names configured curriculum code {code}.')
                continue
            keywords = node.get('keywords', [])
            hits = [word for word in keywords if re.search(r'\b' + re.escape(word) + r'\b', combined, re.I)]
            shared = evidence_tokens & tokens(node.get('label', '') + ' ' + node.get('definition', ''))
            if hits or len(shared) >= 2:
                add('curriculum', key, 'inferred', min(.85, .5 + .1 * len(hits) + .04 * len(shared)),
                    'Matches configured curriculum terms: ' + ', '.join(hits or sorted(shared)))
        best = {}
        for candidate in candidates:
            key = candidate['kind'], candidate['category'], candidate['value']
            if key not in best or candidate['confidence'] > best[key]['confidence']:
                best[key] = candidate
        return sorted(best.values(), key=lambda c: (-c['confidence'], c['value']))


def suggest_draft(draft, provider=None):
    provider = provider or ProfileSuggestionProvider()
    profile = draft['profile']
    curriculum_nodes(profile)  # Validate tree independently of whether any text matches.
    index = {n['id']: n for n in draft['nodes']}
    for node in draft['nodes']:
        context, parent, seen = [], node.get('parent'), set()
        while parent in index and parent not in seen:
            seen.add(parent)
            context.append(index[parent]['text'])
            parent = index[parent].get('parent')
        suggestions = provider.suggest(node, '\n'.join(reversed(context)), profile)
        node['suggestions'] = []
        for candidate in suggestions:
            if not valid_suggestion(candidate, profile):
                node.setdefault('warnings', []).append('An unsupported classification proposal was discarded.')
                continue
            candidate = dict(candidate)
            candidate['key'] = '|'.join([candidate['kind'], candidate.get('category') or '', candidate['value']])
            # Never repopulate a category that the teacher has reviewed, including rejection of all tags.
            category = candidate.get('category') if candidate['kind'] == 'tag' else '__curriculum__'
            candidate['decision'] = node.get('decisions', {}).get(candidate['key'],
                'rejected' if category in node.get('reviewed_categories', []) else 'pending')
            node['suggestions'].append(candidate)
        node['suggestion_note'] = '' if node['suggestions'] else 'Needs review: no supported classification match found.'
    draft['suggestion_method'] = getattr(provider, 'name', type(provider).__name__)
