"""Shared teacher navigation, reusing existing routes and preserving class context."""
from flask import request, session, url_for
import sqlite3

from .entry import EntryError
from .question_levels import settings


def register_navigation(app, store):
    @app.context_processor
    def navigation():
        if session.get('simulated_student'):
            return dict(teacher_nav=[], teacher_section='', nav_class=None, nav_levels=None)
        key = (request.view_args or {}).get('key') or request.values.get('class_key') or session.get('entered_class')
        doc = None
        if key:
            try:
                doc = store.read(key)
            except (EntryError, sqlite3.Error, OSError, ValueError):
                pass
        key = doc['id'] if doc else None
        if doc:
            session['entered_class'] = key
        endpoint = request.endpoint or ''
        section = request.args.get('section')
        if section not in {'home', 'classes', 'assessments', 'students', 'curriculum', 'settings'}:
            if endpoint.startswith('portability.'):
                section = 'settings'
            elif endpoint == 'entry.curriculum_review':
                section = 'curriculum'
            elif endpoint in {'entry.classes', 'entry.class_page', 'entry.legacy'}:
                section = 'classes'
            elif endpoint.startswith('assessment_import.') or endpoint in {'entry.edit', 'entry.scores', 'entry.learning_workspace'} or endpoint.startswith('exit_tickets.'):
                section = 'assessments'
            elif endpoint == 'index':
                section = 'home'
            else:
                section = 'students'
        fallback = url_for('entry.classes')
        links = [
            ('home', 'Studentdash', url_for('index', class_key=key or '', section='home')),
            ('classes', 'Classes', fallback),
            ('assessments', 'Assessments', url_for('entry.class_page', key=key, section='assessments', _anchor='assessments') if key else fallback),
            ('students', 'Students', url_for('index', class_key=key or '', section='students', _anchor='students')),
            ('curriculum', 'Curriculum', url_for('entry.curriculum_review', key=key) if key else fallback),
            ('settings', 'Settings', url_for('portability.transfer', class_key=key or '')),
        ]
        return dict(teacher_nav=links, teacher_section=section, nav_class=doc,
                    nav_levels=settings(doc) if doc else None)
