"""Additive classification defaults for an exact captured course identity.

No curriculum nodes, saved tags or existing configuration values are replaced.
Reads expose an effective profile without a database write or version change.
"""
from copy import deepcopy
from .curriculum import catalog

def effective(profile):
    result = deepcopy(profile)
    captured = result.get('curriculum') or {}
    if not captured.get('id') or not captured.get('version'):
        return result
    current = catalog().get(captured['id'])
    if not current or current['version'] != captured['version']:
        return result
    defaults = current.get('profile', {})
    categories = result.setdefault('categories', {})
    for category, values in defaults.get('categories', {}).items():
        categories[category] = list(dict.fromkeys([*categories.get(category, []), *values]))
    for category, options in defaults.get('category_options', {}).items():
        configured = result.setdefault('category_options', {}).setdefault(category, {})
        for key, value in options.items():
            configured.setdefault(key, deepcopy(value))
    for key in ('command_category', 'vocabulary_source'):
        if key in defaults:
            result.setdefault(key, deepcopy(defaults[key]))
    return result
