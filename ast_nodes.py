from dataclasses import dataclass

# Optional[int] means "an int, or None". It documents which fields may be empty.
from typing import Optional

# each class will represent 1 knitting concept, separate from Lark.

@dataclass
class Gauge:
    # Ex: "4 in = 10 sts, 12 rows"
    length: float   # 4.0
    unit: str       # "in", "cm", "mm"
    stitches: float # 10.0
    rows: float     # 12.0

@dataclass
class RepeatMode:
    # how a stitch/group will repeat
    # Ex: "k to last 2"
    kind: str                       # "to_last"
    # None for "to_end" since there's no number associated
    # "= None" gives it a default, RepeatMode("to_end") works without a value
    value: Optional[int] = None     # 2

@dataclass
class Stitch:
    # Ex: "k2"
    kind: str                           # "k"
    count: int = 1                      # 2
    mode: Optional[RepeatMode] = None   # "k to end" -> RepeatMode
                                        # "k2" -> None

@dataclass
class Group:
    # Ex: "(k2, p2) to end"
    stitches: list      # list of stitch objects [Stitch("k",2), Stitch("p",2)]
    mode: RepeatMode    # RepeatMode required when expressing a group of stitches

@dataclass
class Row:
    items: list                     # a mix of Stitch and Group
    label: Optional[int] = None     # an optional leading counter number "1 row:"

@dataclass
class Note:
    text: str

@dataclass
class CastOn:
    # "cast_on 40 sts" fills 'stitches'
    # "cast_on 16 in" fills 'width' and 'unit'
    stitches: Optional[int] = None # cast_on 40 sts
    width: Optional[float] = None # cast_on 16 in
    unit: Optional[str] = None

@dataclass
class BindOff:
    pass

@dataclass
class LengthBound:
    # Ex: "for 8 in:"
    length: float   # 8.0
    unit: str       # "in"

@dataclass
class CountBound:
    # Ex: "for 15 times:"
    times: int   # 15

@dataclass
class ForLoop:
    bound: object   # either LengthBound or CountBound
    body: list      # list of Row and Note objects

@dataclass
class Pattern:
    # The root: a whole .loopy file
    title: Optional[str]    # None if the file has no "project:" line
    gauge: Gauge
    statements: list        # CastOn, ForLoop, Row, Note, BindOff