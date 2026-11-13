import React, {useState} from 'react';
import type {PracticeExercise} from './practice';

/** Reveal state is ephemeral and this component is remounted for each selected node. */
export function GuidedPractice({exercise}: {exercise: PracticeExercise}) {
  const [hintCount, setHintCount] = useState(0);
  return <section className="guided-practice" aria-labelledby="guided-practice-title">
    <div className="practice-kicker">Original Chemistree exercise · SL / HL</div>
    <h3 id="guided-practice-title">Guided practice</h3>
    <h4>{exercise.title}</h4>
    <p className="practice-question">{exercise.question}</p>
    <p className="muted">Try on paper or in your head. This is an editorial exercise, not an official IB question. No answers or attempts are recorded.</p>
    <button className="hint-button" disabled={hintCount === exercise.hints.length} onClick={() => setHintCount(count => count + 1)}>
      {hintCount === 0 ? 'Show a hint' : hintCount < exercise.hints.length ? 'Show next hint' : 'All hints shown'}
    </button>
    <div className="practice-hints" aria-live="polite">{hintCount > 0 && <ol aria-label="Practice hints">{exercise.hints.slice(0, hintCount).map((hint, i) => <li key={i}>{hint}</li>)}</ol>}</div>
    <details className="practice-solution"><summary>Show worked explanation</summary>
      <ol>{exercise.workedExplanation.map((step, i) => <li key={i}>{step}</li>)}</ol>
      <h4>Compare your reasoning</h4><ul>{exercise.selfCheck.map((check, i) => <li key={i}>{check}</li>)}</ul>
    </details>
    <div className="practice-transfer"><h4>Try another example</h4><p>{exercise.transferQuestion}</p>
      <details><summary>Show another explanation</summary>{exercise.transferExplanation.map((step, i) => <p key={i}>{step}</p>)}</details>
    </div>
    <p className="muted">Use the explanations to reflect on your understanding. Opening a hint or explanation does not change your self-assessment.</p>
    <button className="reflect-button" onClick={() => {const control = document.getElementById('self-assessment'); control?.scrollIntoView({block: 'center'}); control?.focus({preventScroll: true});}}>Reflect on this statement</button>
  </section>;
}
