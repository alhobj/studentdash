"""Small authoring helpers; subject content lives in separate profile modules."""
import math


def number(value):
    if not math.isfinite(value):
        raise ValueError('Non-finite answer')
    return f'{value:.8g}'


class Bank:
    def __init__(self):
        self.sections = {}

    def text(self, code, prompt, correct, wrong, explanation):
        options = [str(correct), *map(str, wrong)]
        if len(options) != 4 or len(set(options)) != 4 or not explanation:
            raise ValueError(f'{code}: ambiguous options: {options}')
        self.sections.setdefault(code, []).append(dict(prompt=prompt, correct=options[0], wrong=options[1:], explanation=explanation))

    def numeric(self, code, prompt, answer, explanation, wrong=()):
        correct = number(answer)
        alternatives = []
        delta = max(abs(answer) * .2, .01) if 0 < abs(answer) < 1 else max(abs(answer) * .2, 1)
        for candidate in [*wrong, answer + delta, answer - delta, answer + 2 * delta, answer + 3 * delta]:
            value = number(candidate)
            if value != correct and value not in alternatives:
                alternatives.append(value)
            if len(alternatives) == 3:
                break
        self.text(code, prompt + ' Choose the closest value.', correct, alternatives,
                  explanation + f' The result is {correct}.')

    def finish(self, expected):
        if set(self.sections) != set(expected):
            raise ValueError('Section coverage mismatch')
        for code, rows in self.sections.items():
            if len(rows) != 20 or len({r['prompt'] for r in rows}) != 20:
                raise ValueError(f'{code}: expected 20 distinct prompts, got {len(rows)}')
        return self.sections
