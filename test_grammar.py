from pathlib import Path
import pytest
from lark import Lark
from lark.exceptions import LarkError

ROOT = Path(__file__).parent
GRAMMAR = (ROOT / "grammar" / "loopy.lark").read_text()

def make_parser(start="start", **kwargs):
    return Lark(GRAMMAR, parser="earley", start=start, **kwargs)

VALID = [
    ("title_stmt", 'project: "Simple Dishcloth"'),
    ("gauge_stmt", "gauge: 4 in = 10 sts, 12 rows"),
    ("gauge_stmt", "gauge: 10 cm = 22.5 sts, 30 rows"),
    ("cast_on_stmt", "cast_on 40 sts"),
    ("cast_on_stmt", "cast_on 16 in"),
    ("bind_off_stmt", "bind_off"),
    ("row_stmt", "row: k to end."),
    ("row_stmt", "1 row: k to end."),
    ("row_stmt", "row: k2, p2."),
    ("row_stmt", "row: (k2, p2) to end."),
    ("row_stmt", "row: (k1, p1) to last 2."),
    ("row_stmt", "row: (k2, p2) 5 times."),
    ("row_stmt", "row: (k1, sl1k) to last 1, k1."),
    ("for_stmt", "for 8 in:\n row: k to end.\nend"),
    ("for_stmt", "for 15     times:\n row: k to end.\n row: p to end.\nend"),
    ("note_stmt", 'note: "End on purl row"'),
    ("for_stmt", 'for 8 in:\n note: "Slip first stitch"\n row: k to end.\nend'),
]

INVALID = [
    ("gauge_stmt", "gauge: 4 in = 10 sts"),
    ("gauge_stmt", "gauge: 4 ft = 10 sts, 12 rows"),
    ("cast_on_stmt", "cast_on sts"),
    ("row_stmt", "row: k to end"),
    ("row_stmt", "row: (k2, p2)."),
    ("row_stmt", "row: x2."),
    ("for_stmt", "for 8 in:\n row: k to end."),
    ("note_stmt", 'note: End on purl row'),
    ("row_stmt", "row: sl1x."),
    ("row_stmt", "k to end."),
    ("for_stmt", "for 7 times:\n row: k to end."),
    ("for_stmt", 'for 8 in:\n bind_off\nend'),
]

@pytest.mark.parametrize("rule, text", VALID)
def test_valid_input_parses(rule, text):
    make_parser(start=rule).parse(text)

@pytest.mark.parametrize("rule, text", INVALID)
def test_invalid_input_is_rejected(rule, text):
    with pytest.raises(LarkError):
        make_parser(start=rule).parse(text)

REFERENCE_FILES = sorted((ROOT / "reference_patterns").glob("*.loopy"))

@pytest.mark.parametrize("path", REFERENCE_FILES, ids=lambda p: p.name)
def test_reference_pattern_parses(path):
    tree = make_parser().parse(path.read_text())
    assert tree.data == "start"

@pytest.mark.parametrize("path", REFERENCE_FILES, ids=lambda p: p.name)
def test_reference_pattern_is_unambiguous(path):
    tree = make_parser(ambiguity="explicit").parse(path.read_text())
    assert not list(tree.find_data("_ambig"))