import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    workbook: Path
    output: Path

    @classmethod
    def from_env(cls):
        preferred = ROOT / 'data' / 'master.xlsx'
        fallback = ROOT / 'Studentdashtest.xlsx'
        workbook = os.environ.get('STUDENTDASH_WORKBOOK')
        output = os.environ.get('STUDENTDASH_OUTPUT', 'output')
        path = Path(workbook) if workbook else (preferred if preferred.exists() else fallback)
        return cls((ROOT / path).resolve(), (ROOT / output).resolve())
