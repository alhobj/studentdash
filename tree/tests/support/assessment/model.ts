// Development-only assessment contract. Never import from the student application.
import {z} from 'zod';
import map from '../../../src/data/map.json';
import rules from './rules.json';

export {map, rules};
export const STORAGE_KEY = 'chemistree-v2';
const ids = new Set(map.nodes.map(n => n.id));
const nodeId = z.string().refine(id => ids.has(id), 'Unknown Chemistree node ID');

const evidenceSchema = z.object({
  id: z.string().min(1),
  assessmentId: z.string().min(1),
  questionId: z.string().min(1),
  externalSyllabusIds: z.array(z.string()),
  nodeIds: z.array(nodeId).min(1),
  scope: z.enum(['direct', 'thematic']),
  status: z.enum(['graded', 'missing', 'absent', 'exempt', 'pending']),
  score: z.number().finite().nonnegative().optional(),
  maxScore: z.number().finite().positive().optional(),
  date: z.iso.date(),
  label: z.string(),
}).strict().superRefine((e, c) => {
  if (e.scope === 'direct' && e.nodeIds.length !== 1) {
    c.addIssue({code: 'custom', message: 'Direct evidence must identify exactly one rubric-assessed node; use thematic for broad tags'});
  }
  if (e.status === 'graded' && (e.score === undefined || e.maxScore === undefined || e.score > e.maxScore)) {
    c.addIssue({code: 'custom', message: 'Graded evidence needs 0 ≤ score ≤ maxScore'});
  }
});

export const learnerSchema = z.object({
  schemaVersion: z.literal('1.0'),
  mapVersion: z.literal('2.0'),
  student: z.object({
    id: z.string().min(1), externalId: z.string().min(1), label: z.string().min(1), level: z.enum(['SL', 'HL']),
  }).strict(),
  covered: z.array(nodeId),
  selfAssessments: z.record(nodeId, z.enum(['not-yet', 'developing', 'confident'])),
  teacherJudgments: z.array(z.object({
    nodeId, judgment: z.enum(['secure', 'developing', 'revisit']), date: z.iso.date(), note: z.string(),
  }).strict()),
  evidence: z.array(evidenceSchema),
}).strict().superRefine((d, c) => {
  if (new Set(d.evidence.map(e => e.id)).size !== d.evidence.length) {
    c.addIssue({code: 'custom', message: 'Evidence IDs must be unique'});
  }
});

export type Learner = z.infer<typeof learnerSchema>;

export function parseImport(raw: unknown): Learner {
  if (raw && typeof raw === 'object' && 'mapVersion' in raw && raw.mapVersion === '1.0') {
    throw new Error('Map 1.0 uses retired prototype objectives. A teacher-reviewed migration to map 2.0 is required; no learning signals have been transferred.');
  }
  return learnerSchema.parse(raw);
}

export function evidenceFor(d: Learner, id: string) {
  return d.evidence.filter(e => e.nodeIds.includes(id));
}

export function status(d: Learner, id: string) {
  const evidence = evidenceFor(d, id).filter(e => e.scope === 'direct' && e.status === 'graded');
  if (!evidence.length) return 'Not assessed';
  if (evidence.length < rules.minEvidence) return 'Limited evidence';
  const ratio = evidence.reduce((total, e) => total + e.score! / e.maxScore!, 0) / evidence.length;
  return ratio >= rules.secureThreshold ? 'Evidence: secure' : ratio >= rules.developingThreshold ? 'Evidence: developing' : 'Evidence: revisit';
}
