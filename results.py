# This file represents the interpreter's output

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CastOnStep:
    stitches: int   # how many stitches are on the needle

@dataclass
class RowStep:
    number: int             # running row count across pattern
    label: Optional[int]    # the optional leading row number "1 row: ..."
    items: list             # stitch/group objects
    stitches_before: int    # stitch count when the row started
    worked: int             # how many stitches the pattern has worked
    unworked: int           # how many stitches unworked by the pattern

@dataclass
class NoteStep:
    text: str

@dataclass
class BindOffStep:
    stitches: int   # how many stitches were bound off, matching the amount on the CastOnStep

@dataclass
class RunResult:
    title: Optional[str]
    steps: list                 # in order: CastOnStep, RowStep, NoteStep, BindOffStep
    messages: list              # human-readable notices ("Adjusted...")
    total_rows: int
    final_stitches: int
    total_length: float         # in unit (in, cm, mm)
    unit: str
    stitches_per_unit: float    # ex: 2.5 sts per inch
    rows_per_unit: float        # ex: 4.0 rows per inch



