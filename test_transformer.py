# inspects AST objects generically
from dataclasses import fields, is_dataclass
from pathlib import Path

import pytest
from lark import Tree, Token

from ast_nodes import *
from loopy_parser import parse_pattern, parse_file

ROOT = Path(__file__).parent
REFERENCE_FILES = sorted((ROOT / "reference_patterns").glob("*.loopy"))


def assert_pure(node):
    # Walks the whole AST and fails if any Lark Tree or Token is left inside.
    # A leftover means a transformer method is missing or misnamed, which would
    # break the Week 4 interpreter later.
    assert not isinstance(node, (Tree, Token)), f"Lark object leaked: {node!r}"
    if is_dataclass(node):
        # look at every field of the object
        for f in fields(node):
            # and check what's inside it
            assert_pure(getattr(node, f.name))
    elif isinstance(node, list):
        for item in node:
            assert_pure(item)


# the dishcloth, checked field by field
def test_dishcloth_ast():
    p = parse_file(ROOT / "reference_patterns" / "dishcloth.loopy")
    assert p.title == "Simple Dishcloth"
    assert p.gauge == Gauge(4.0, "in", 10.0, 12.0)
    assert p.statements[0] == CastOn(stitches=40)
    loop = p.statements[1]
    assert loop.bound == LengthBound(8.0, "in")
    # Row -> first item -> a "k to end" stitch
    assert loop.body[0].items[0] == Stitch("k", 1, RepeatMode("to_end"))
    assert isinstance(p.statements[2], BindOff)


# small inline patterns, one feature each
# Every inline test needs a gauge because the grammar requires one, so this
# string is glued onto the front of each snippet.
GAUGE = "gauge: 4 in = 10 sts, 12 rows\n"


def test_no_title_gives_none():
    assert parse_pattern(GAUGE + "bind_off").title is None


def test_cast_on_width():
    p = parse_pattern(GAUGE + "cast_on 16 in\nbind_off")
    assert p.statements[0] == CastOn(width=16.0, unit="in")


def test_decimal_loop_length():
    p = parse_pattern(GAUGE + "for 8.5 in:\n row: k to end.\nend")
    assert p.statements[0].bound == LengthBound(8.5, "in")


def test_count_loop_with_note_label_and_group():
    # Exercises four features at once: a count-bound loop, a note inside it,
    # a row label, and a stitch group.
    src = GAUGE + (
        'for 15 times:\n'
        ' note: "Slip first stitch"\n'
        ' 1 row: (k2, p2) to end.\n'
        'end'
    )
    loop = parse_pattern(src).statements[0]
    assert loop.bound == CountBound(15)
    assert loop.body[0] == Note("Slip first stitch")
    assert loop.body[1] == Row(
        items=[Group([Stitch("k", 2), Stitch("p", 2)], RepeatMode("to_end"))],
        label=1,
    )


def test_to_last_and_uppercase_stitches():
    # Uppercase K/P should come out lowercase, and "to last 2" keeps its number.
    p = parse_pattern(GAUGE + "row: (K1, P1) to last 2, K2.")
    row = p.statements[0]
    assert row.items[0] == Group([Stitch("k"), Stitch("p")], RepeatMode("to_last", 2))
    assert row.items[1] == Stitch("k", 2)


def test_times_repeat_on_group():
    p = parse_pattern(GAUGE + "row: (k2, p2) 5 times.")
    assert p.statements[0].items[0].mode == RepeatMode("times", 5)


# parametrize runs this one function once per file in reference_patterns/,
# so a new .loopy file is tested automatically.
@pytest.mark.parametrize("path", REFERENCE_FILES, ids=lambda p: p.name)
def test_reference_pattern_transforms(path):
    p = parse_file(path)
    assert isinstance(p, Pattern)
    assert isinstance(p.gauge, Gauge)
    assert_pure(p)