"""Conservative, replaceable classification and question-level diagnostic queries."""
from dataclasses import dataclass
from html import unescape
from math import isfinite
import re

VOCABULARY = {
    'CommandTerm': 'State|Identify|Outline|Describe|Calculate|Determine|Deduce|Explain|Suggest|Predict|Justify|Compare|Contrast|Discuss|Evaluate|Interpret|Draw|Sketch|Apply|Derive|Estimate|Comment|Formulate|Solve|Distinguish|List|Classify|Write|Label|Show|Annotate|Demonstrate|Construct|Examine|Name|Complete'.split('|'),
    'Skill': 'Recall knowledge|Chemical reasoning|Quantitative problem solving|Data interpretation|Graphical analysis|Experimental design|Experimental evaluation|Equation/formula writing|Chemical representation|Prediction/deduction|Comparison/classification|Multi-step problem solving'.split('|'),
    'CognitiveDemand': ['Recall', 'Apply', 'Analyse/Reason', 'Evaluate/Create'],
    'Context': ['Direct', 'Applied', 'Unfamiliar'],
    'Representation': 'Written|Calculation|Chemical equation|Structural formula|Lewis structure|Mechanism|Graph|Table|Diagram/model|Spectrum|Experimental data'.split('|'),
    'QuantitativeSkill': 'Stoichiometry|Algebra|Proportional reasoning|Logarithms|Units/conversions|Significant figures|Graph calculation|Uncertainty'.split('|'),
    'ExperimentalSkill': 'Procedure|Variables|Measurement|Data processing|Uncertainty|Error|Accuracy/precision|Evaluation|Improvement|Conclusion|Assumptions|Safety'.split('|'),
}
SOURCES = {'existing': 3, 'teacher': 4, 'rule': 2, 'inferred': 1}


@dataclass(frozen=True)
class QuestionTag:
    question_id: str
    category: str
    tag: str
    source: str
    confidence: float | None = None

    def __post_init__(self):
        if self.category not in VOCABULARY or self.tag not in VOCABULARY[self.category]:
            raise ValueError(f'Unknown classification: {self.category}/{self.tag}')
        if self.source not in SOURCES:
            raise ValueError(f'Unknown tag source: {self.source}')
        c = self.confidence
        if c is not None and (isinstance(c, bool) or not isinstance(c, (float, int)) or not isfinite(c) or not 0 <= c <= 1):
            raise ValueError('Confidence must be blank or a finite number from 0 to 1.')


def merge_tags(tags):
    """A reviewed category replaces lower-priority proposals; retain multiple peer tags."""
    groups = {}
    for t in tags:
        groups.setdefault((t.question_id, t.category), []).append(t)
    result = []
    for group in groups.values():
        priority = max(SOURCES[t.source] for t in group)
        protected = priority >= SOURCES['existing']
        selected = {}
        for t in group:
            if protected and SOURCES[t.source] != priority:
                continue
            old = selected.get(t.tag)
            if old is None or (SOURCES[t.source], t.confidence or 0) > (SOURCES[old.source], old.confidence or 0):
                selected[t.tag] = t
        result.extend(selected.values())
    return sorted(result, key=lambda t: (t.question_id, t.category, t.tag))


def syllabus_hierarchy(code):
    """Aggregate only supplied codes; never translate a legacy code to a current one."""
    code = str(code or '').strip()
    if not re.fullmatch(r'(?:[SR]\d+|\d+|[A-D])(?:\.\d+)*', code):
        return []
    parts = code.split('.')
    return ['.'.join(parts[:n]) for n in range(len(parts), 0, -1)]


def plain_text(value):
    # Broken/truncated embedded image markup is common in these source exports.
    value = re.sub(r'<img\b[^>]*(?:>|$)', ' ', str(value or ''), flags=re.I)
    return unescape(re.sub(r'<[^>]*>', ' ', value))


def command_terms(value):
    return [t for t in VOCABULARY['CommandTerm'] if re.search(r'\b' + re.escape(t) + r'\b', str(value or ''), re.I)]


# Rules describe visible evidence, not calibrated probabilities or cognitive demand.
RULES = [
    ('Representation', 'Calculation', r'\bcalculate\b', .95),
    ('Representation', 'Graph', r'\b(graph|graphs|plot|plotted)\b', .90),
    ('Representation', 'Table', r'\btable\b', .90),
    ('Representation', 'Spectrum', r'\b(spectrum|spectra)\b', .90),
    ('Representation', 'Lewis structure', r'\blewis (structure|diagram)', .95),
    ('Representation', 'Structural formula', r'\b(structural|displayed|skeletal) formula', .95),
    ('Representation', 'Chemical equation', r'\b(balanced|chemical|ionic) equation', .95),
    ('Representation', 'Mechanism', r'\b(reaction mechanism|mechanism for the reaction)\b', .90),
    ('Representation', 'Diagram/model', r'\b(diagram|apparatus)\b', .85),
    ('Representation', 'Experimental data', r'\b(experimental (data|results)|results of the experiment)\b', .90),
    ('QuantitativeSkill', 'Significant figures', r'\bsignificant figures\b', .95),
    ('QuantitativeSkill', 'Uncertainty', r'\b(calculate|determine|estimate)\b.{0,70}\buncertainty\b', .90),
    ('QuantitativeSkill', 'Graph calculation', r'\b(calculate|determine)\b.{0,70}\b(gradient|slope|area under)\b', .90),
    ('Skill', 'Equation/formula writing', r'\b(write|formulate)\b.{0,60}\b(equation|formula)\b', .85),
    ('Skill', 'Quantitative problem solving', r'\bcalculate\b.{0,90}\b(mass|volume|amount|concentration|enthalpy|energy|temperature|rate|pressure|percentage|yield|pH)\b', .90),
    ('Skill', 'Graphical analysis', r'\b(use|using|interpret|analyse|analyze)\b.{0,60}\bgraph\b', .80),
    ('ExperimentalSkill', 'Safety', r'\b(safety precaution|safety consideration)\b', .90),
    ('ExperimentalSkill', 'Variables', r'\b(independent|dependent|controlled) variable', .90),
    ('ExperimentalSkill', 'Error', r'\b(systematic|random) error', .90),
    ('ExperimentalSkill', 'Accuracy/precision', r'\b(accuracy|precision)\b', .80),
]


def classify(question_id, text, existing_command='', *, ambiguous_parts=False):
    tags = [QuestionTag(question_id, 'CommandTerm', t, 'existing') for t in command_terms(existing_command)]
    # Do not copy whole-parent evidence onto an unidentified subpart.
    if ambiguous_parts:
        return tags
    text = plain_text(text)
    if not tags:
        tags.extend(QuestionTag(question_id, 'CommandTerm', t, 'rule', .85) for t in command_terms(text))
    for category, tag, pattern, confidence in RULES:
        if re.search(pattern, text, re.I | re.S):
            tags.append(QuestionTag(question_id, category, tag, 'rule', confidence))
    return merge_tags(tags)


def performance(data, student_id, filters=(), *, syllabus=None):
    """AND across (category, tag) filters, weighted once per graded question.

    Syllabus filtering uses only teacher-reviewed current mappings. Old syllabus
    labels are never silently included in current curriculum diagnostics.
    """
    if student_id not in data.students:
        raise ValueError('Unknown student.')
    tags = {}
    for t in merge_tags(data.question_tags):
        tags.setdefault(t.question_id, set()).add((t.category, t.tag))
    score = maximum = 0.0
    ids = []
    for r in data.question_results:
        if r.student_id != student_id or r.status != 'graded':
            continue
        if not set(filters) <= tags.get(r.question_id, set()):
            continue
        mapping = data.question_syllabus.get(r.question_id, {})
        if syllabus is not None and (mapping.get('Status') != 'current' or syllabus not in syllabus_hierarchy(mapping.get('CurrentCode'))):
            continue
        q = data.questions[r.question_id]
        score += r.score
        maximum += q.marks
        ids.append(q.id)
    return {'score': score, 'maximum': maximum, 'percent': 100 * score / maximum if maximum else None, 'question_ids': ids}
