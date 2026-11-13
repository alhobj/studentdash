"""Generic, single-learner, direct-question export for a local curriculum viewer.

No topic inference, ancestor rollups, confidence writes, or network operations.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import os
import shutil
import tempfile
import uuid


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, value):
    path = Path(path)
    content = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.tree-', suffix='.tmp', delete=False) as target:
        temp = Path(target.name)
        target.write(content)
        target.flush()
        os.fsync(target.fileno())
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def evidence(data, student_id, mapping, registry):
    if student_id not in data.students:
        raise ValueError('Choose an existing student ID.')
    ids = {node['id'] for node in registry['nodes']}
    if not isinstance(mapping, dict) or any(not isinstance(q, str) or q not in data.questions or not isinstance(n, str) or n not in ids for q, n in mapping.items()):
        raise ValueError('Every mapping must identify an existing question and one exact curriculum node. Broad topic mappings are not accepted.')
    rows, seen = [], set()
    for result in data.question_results:
        if result.student_id != student_id or result.status != 'graded' or result.question_id not in mapping:
            continue
        key = (result.assessment_id, result.question_id)
        if key in seen:
            raise ValueError('Duplicate question evidence. Export cancelled.')
        seen.add(key)
        question = data.questions[result.question_id]
        assessment = data.assessments[result.assessment_id]
        if question.assessment_id != result.assessment_id:
            raise ValueError('Question and assessment do not match.')
        score, maximum = result.score, question.marks
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (score, maximum)) or not 0 <= score <= maximum <= 1000000 or maximum <= 0:
            raise ValueError('Graded questions require valid earned and possible marks.')
        fields = dict(assessmentId=assessment.id, assessmentTitle=assessment.name, questionId=question.id, questionNumber=question.number, nodeId=mapping[question.id])
        if any(not isinstance(v, str) or not 1 <= len(v) <= 200 for v in fields.values()):
            raise ValueError('Export labels and IDs must be nonempty strings of at most 200 characters.')
        rows.append(dict(**fields, score=score, maxScore=maximum, status='graded'))
    if len(rows) > 10000:
        raise ValueError('Too many question records for one local package.')
    return sorted(rows, key=lambda row: (row['assessmentId'], row['questionId']))


def export_package(data, student_id, mapping, viewer, destination):
    """Create/update exactly one destination; retain its binding and revision identity."""
    viewer, destination = Path(viewer).resolve(), Path(destination).resolve()
    if viewer == destination or viewer in destination.parents or destination in viewer.parents:
        raise ValueError('Viewer template and student destination must be separate folders.')
    registry = read_json(viewer / 'curriculum.json')
    for field in ('mapId', 'mapVersion'):
        if not isinstance(registry.get(field), str) or not registry[field]:
            raise ValueError('Invalid curriculum registry.')
    rows = evidence(data, student_id, mapping, registry)
    assets = read_json(viewer / 'assets-manifest.json')
    files = ['app/index.html', 'assets-manifest.json', 'Start.cmd', 'Start.ps1', 'serve.py', 'LOCAL_STUDENT_GUIDE.md']
    for asset in assets:
        p = Path(asset)
        if not isinstance(asset, str) or p.is_absolute() or '..' in p.parts or '\\' in asset or len(p.parts) != 2 or p.parts[0] != 'assets' or p.suffix not in {'.js', '.css'}:
            raise ValueError('Invalid viewer asset path.')
        files.append('app/' + asset)
    for name in files:
        if not (viewer / name).is_file() or not (viewer / name).resolve().is_relative_to(viewer):
            raise ValueError('Viewer build is missing or contains linked files. Rebuild it first.')
    destination.mkdir(parents=True, exist_ok=True)
    config_path = destination / 'package.json'
    results_path = destination / 'results.json'
    for path in (config_path, results_path):
        if path.is_symlink():
            raise ValueError('Linked package files are not supported.')
    if config_path.exists():
        config = read_json(config_path)
        if config.get('learnerId') != student_id or config.get('mapId') != registry['mapId'] or config.get('mapVersion') != registry['mapVersion']:
            raise ValueError('This folder belongs to another learner or curriculum. Choose a new destination; do not overwrite it.')
        uuid.UUID(config['packageId'])
    else:
        if any(destination.iterdir()):
            raise ValueError('Initial destination must be empty. Never reuse an unrelated folder.')
        config = dict(schemaVersion='1.0', mapId=registry['mapId'], mapVersion=registry['mapVersion'], learnerId=student_id, packageId=str(uuid.uuid4()))
    previous = read_json(results_path) if results_path.exists() else None
    if previous and (previous.get('packageId') != config['packageId'] or not isinstance(previous.get('revision'), int)):
        raise ValueError('Existing results do not match this package. Export cancelled.')
    changed = previous is None or previous.get('evidence') != rows
    payload = dict(schemaVersion='1.0', mapId=registry['mapId'], mapVersion=registry['mapVersion'], packageId=config['packageId'], revision=(previous['revision'] + 1 if previous else 1), generatedAt=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), evidence=rows)
    if len(json.dumps(payload, ensure_ascii=False).encode('utf-8')) > 2 * 1024 * 1024:
        raise ValueError('Results exceed the 2 MB viewer limit.')
    # Versioned assets first, HTML last. A running browser can retain its old assets.
    # Confidence never lives in this folder and is never read/written by the exporter.
    for name in sorted(files, key=lambda n: n == 'app/index.html'):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or not target.resolve().is_relative_to(destination):
            raise ValueError('Destination contains an unsafe linked file.')
        if target.exists() and target.read_bytes() == (viewer / name).read_bytes():
            continue
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            temp = Path(handle.name)
        try:
            shutil.copyfile(viewer / name, temp)
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    if not config_path.exists():
        atomic_json(config_path, config)
    if changed:
        atomic_json(results_path, payload)
    return dict(changed=changed, revision=payload['revision'] if changed else previous['revision'], questions=len(rows))
