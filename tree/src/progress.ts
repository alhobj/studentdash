import {map} from './curriculum';

/** Student-only progress. An absent entry means Not reviewed. */
export const STORAGE_KEY = 'chemistree-self-assessment-v1';
export const MAX_IMPORT_BYTES = 128 * 1024;
export const EXPORT_FILENAME = 'chemistree-self-assessment.json';
export const STATUS_LABELS = {
  'not-reviewed': 'Not reviewed',
  'needs-practice': 'Needs practice',
  developing: 'Developing',
  confident: 'Confident',
} as const;
export type SelfAssessment = Exclude<keyof typeof STATUS_LABELS, 'not-reviewed'>;
export type Progress = Record<string, SelfAssessment>;
export type ImportMode = 'merge' | 'replace' | 'cancel';
export type ProgressFile = {schemaVersion: '1.0'; mapVersion: '2.0'; selfAssessments: Progress};
export type ProgressStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> | null;
export type StorageResult = {ok: boolean; message?: string};

const knownIds = new Set(map.nodes.map(node => node.id));
const storedStatuses = new Set<string>(['needs-practice', 'developing', 'confident']);
const owns = (object: object, key: string) => Object.prototype.hasOwnProperty.call(object, key);
const isObject = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

/** Validate all fields before returning an independent copy. No timestamps or identifiers. */
function validateProgress(value: unknown): Progress {
  if (!isObject(value)) throw new Error('Self-assessments must be an object containing node IDs and status values.');
  const result: Progress = {};
  for (const [id, status] of Object.entries(value)) {
    if (!knownIds.has(id)) throw new Error('The file contains an unknown curriculum node ID. Use a file for the current Chemistree map.');
    if (typeof status !== 'string' || !storedStatuses.has(status)) {
      throw new Error('The file contains an invalid self-assessment. Allowed saved values are needs-practice, developing and confident. Not reviewed is represented by an absent entry.');
    }
    result[id] = status as SelfAssessment;
  }
  return result;
}

/** Strict student-transfer format: assessment envelopes and arbitrary fields are rejected. */
export function parseProgressFile(text: string): Progress {
  if (new TextEncoder().encode(text).byteLength > MAX_IMPORT_BYTES) {
    throw new Error('The file is too large. Choose a self-assessment JSON file no larger than 128 KB.');
  }
  let raw: unknown;
  try { raw = JSON.parse(text); }
  catch { throw new Error('This is not valid JSON. Choose a Chemistree self-assessment export.'); }
  if (!isObject(raw)) throw new Error('Choose a Chemistree self-assessment file containing one JSON object.');
  const allowed = new Set(['schemaVersion', 'mapVersion', 'selfAssessments']);
  if (Object.keys(raw).some(key => !allowed.has(key))) {
    throw new Error('The file contains unexpected fields. Only curriculum versions and self-assessments are accepted; identity, results, scores and comments are not supported.');
  }
  if (raw.schemaVersion !== '1.0') throw new Error('This self-assessment file version is not supported. Expected schemaVersion 1.0.');
  if (raw.mapVersion !== map.version) throw new Error('This file targets a different curriculum map. No progress has been changed.');
  if (!owns(raw, 'selfAssessments')) throw new Error('The file is missing its selfAssessments entries.');
  return validateProgress(raw.selfAssessments);
}

export function exportProgress(progress: Progress): string {
  const file: ProgressFile = {
    schemaVersion: '1.0',
    mapVersion: '2.0',
    selfAssessments: validateProgress(progress),
  };
  return JSON.stringify(file, null, 2) + '\n';
}

export function setSelfAssessment(progress: Progress, id: string, status: SelfAssessment | 'not-reviewed'): Progress {
  if (!knownIds.has(id)) throw new Error('Cannot save self-assessment for an unknown curriculum node.');
  const next = validateProgress(progress);
  if (status === 'not-reviewed') delete next[id];
  else {
    if (!storedStatuses.has(status)) throw new Error('This self-assessment value is not supported.');
    next[id] = status;
  }
  return next;
}

/** Only different existing values need an explicit overwrite decision. */
export function importConflicts(current: Progress, incoming: Progress): string[] {
  const validCurrent = validateProgress(current), validIncoming = validateProgress(incoming);
  return Object.keys(validIncoming).filter(id => owns(validCurrent, id) && validCurrent[id] !== validIncoming[id]);
}

/** Immutable transaction. A cancelled preview never changes or validates current state. */
export function applyImport(current: Progress, incoming: Progress, mode: ImportMode, acceptedConflicts: readonly string[] = []): Progress {
  if (mode === 'cancel') return current;
  const validCurrent = validateProgress(current), validIncoming = validateProgress(incoming);
  if (mode === 'replace') return validIncoming;
  if (mode !== 'merge') throw new Error('Choose merge or replace before importing.');
  const accepted = new Set(acceptedConflicts);
  const result = {...validCurrent};
  for (const [id, status] of Object.entries(validIncoming)) {
    if (!owns(validCurrent, id) || validCurrent[id] === status || accepted.has(id)) result[id] = status;
  }
  return result;
}

export function loadProgress(storage: ProgressStorage): {progress: Progress; message?: string} {
  try {
    if (!storage) throw new Error('Storage unavailable');
    const text = storage.getItem(STORAGE_KEY);
    return text === null ? {progress: {}} : {progress: parseProgressFile(text)};
  } catch {
    return {progress: {}, message: 'Saved self-assessment could not be read. Existing browser data has not been changed. You can work in this session and export a file.'};
  }
}

export function saveProgress(storage: ProgressStorage, progress: Progress): StorageResult {
  // Validate before attempting storage so invalid progress is never retained.
  const text = exportProgress(progress);
  try {
    if (!storage) throw new Error('Storage unavailable');
    storage.setItem(STORAGE_KEY, text);
    return {ok: true};
  } catch {
    return {ok: false, message: 'Browser storage is unavailable or full. Your changes remain in this session only. Export a self-assessment file to keep them.'};
  }
}

export function clearProgress(storage: ProgressStorage): StorageResult {
  try {
    if (!storage) throw new Error('Storage unavailable');
    storage.removeItem(STORAGE_KEY);
    return {ok: true};
  } catch {
    return {ok: false, message: 'Progress was cleared in this session, but saved browser data could not be removed. It may return after a reload. Clear this site’s browser data to remove it.'};
  }
}
