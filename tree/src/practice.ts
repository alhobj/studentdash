import nodeIds from './generated/practice-index.json';

/** Original teaching exercises. Official statements remain in map.json. */
export type PracticeExercise = {
  id: string;
  nodeId: string;
  title: string;
  question: string;
  hints: string[];
  workedExplanation: string[];
  selfCheck: string[];
  transferQuestion: string;
  transferExplanation: string[];
};
export const practiceNodeIds = new Set(nodeIds);
export const practiceCount = nodeIds.length;
