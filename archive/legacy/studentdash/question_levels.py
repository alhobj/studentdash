"""Presentation defaults from explicit course/profile metadata, never class names."""
from .assessment_import import import_profile
from .curriculum import catalog


def settings(doc):
    profile = import_profile(doc)
    curriculum = profile.get('curriculum') or {}
    configuration = curriculum
    # Additive UI metadata can be supplied for earlier captured curriculum copies.
    if not curriculum.get('course_levels') and curriculum.get('id'):
        current = next((c for c in catalog().values() if c['id'] == curriculum['id'] and c['version'] == curriculum.get('version')), None)
        if current:
            configuration = current
    course_options = configuration.get('course_levels') or profile.get('course_levels') or (profile.get('levels', []) if len(profile.get('levels', [])) == 1 else [])
    selected = doc.get('course_levels', course_options)
    options = list(dict.fromkeys(configuration.get('question_levels') or profile.get('levels', []) or course_options))
    labels = dict(profile.get('question_level_labels', {}), **configuration.get('question_level_labels', {}))
    help_text = configuration.get('question_level_help') or profile.get('question_level_help', '')
    return dict(single=selected[0] if len(selected) == 1 else '', selected=selected,
                course_options=course_options, options=options, labels=labels, help=help_text)
