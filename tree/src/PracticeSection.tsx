import React from 'react';
import data from './data/practice.json';
import {GuidedPractice} from './GuidedPractice';
export default function PracticeSection({nodeId}: {nodeId: string}) {
  const exercise = data.find(exercise => exercise.nodeId === nodeId);
  return exercise ? <GuidedPractice key={nodeId} exercise={exercise}/> : null;
}
