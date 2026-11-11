from pathlib import Path

import pytest

from interpreter import run_pattern, LoopyError
from loopy_parser import parse_pattern, parse_file
from results import CastOnStep, RowStep, NoteStep, BindOffStep

ROOT = Path(__file__).parent
REFERENCE_FILES = sorted((ROOT / "reference_patterns").glob("*.loopy"))

# 4 in = 10 sts, 12 rows  ->  2.5 sts/in and 3 rows/in
GAUGE = "gauge: 4 in = 10 sts, 12 rows\n"


def run(src):
    return run_pattern(parse_pattern(src))


def rows(result):
    return [s for s in result.steps if isinstance(s, RowStep)]


# ---- the dishcloth: 8 in * 3 rows/in = 24 rows, body is 1 row, so 24 repeats ----
def test_dishcloth_numbers():
    r = run_pattern(parse_file(ROOT / "reference_patterns" / "dishcloth.loopy"))
    assert r.total_rows == 24
    assert r.final_stitches == 40
    assert r.total_length == pytest.approx(8.0)
    assert r.messages == []


# ---- gauge math ----
def test_gauge_per_unit():
    r = run(GAUGE + "cast_on 10 sts\nbind_off")
    assert r.stitches_per_unit == pytest.approx(2.5)
    assert r.rows_per_unit == pytest.approx(3.0)


def test_two_row_body_divides_evenly():
    # 10 in * 3 = 30 rows, 2-row body -> 15 repeats, no adjustment
    r = run(GAUGE + "cast_on 36 sts\nfor 10 in:\n row: k to end.\n row: p to end.\nend\nbind_off")
    assert r.total_rows == 30
    assert r.messages == []


def test_rounding_is_half_up_and_reported():
    # 4 in = 10 sts, 10 rows -> 2.5 rows/in. 10 in = 25 rows. 25/2 = 12.5 repeats.
    # Half-up gives 13 repeats = 26 rows = 10.4 in. (round() would give 12.)
    src = ("gauge: 4 in = 10 sts, 10 rows\n"
           "cast_on 40 sts\nfor 10 in:\n row: k to end.\n row: p to end.\nend")
    r = run(src)
    assert r.total_rows == 26
    assert r.total_length == pytest.approx(10.4)
    assert len(r.messages) == 1 and "Adjusted" in r.messages[0]


def test_short_length_still_gives_one_repeat():
    # 0.1 in = 0.3 rows. Rounds to 0, but the minimum is 1.
    r = run(GAUGE + "cast_on 10 sts\nfor 0.1 in:\n row: k to end.\nend")
    assert r.total_rows == 1
    assert len(r.messages) == 1


def test_mixed_units():
    # 10.16 cm is exactly 4 in, so 12 rows
    r = run(GAUGE + "cast_on 10 sts\nfor 10.16 cm:\n row: k to end.\nend")
    assert r.total_rows == 12


def test_metric_gauge():
    # 10 cm = 20 sts, 30 rows -> 20 cm = 60 rows
    r = run("gauge: 10 cm = 20 sts, 30 rows\ncast_on 10 sts\nfor 20 cm:\n row: k to end.\nend")
    assert r.total_rows == 60
    assert r.unit == "cm"


def test_count_loop_is_repeats_not_rows():
    # 15 repeats of a 2-row body = 30 rows
    r = run(GAUGE + "cast_on 10 sts\nfor 15 times:\n row: k to end.\n row: p to end.\nend")
    assert r.total_rows == 30
    assert r.messages == []


# ---- cast on ----
def test_cast_on_by_width():
    # 16 in * 2.5 sts/in = 40
    r = run(GAUGE + "cast_on 16 in\nbind_off")
    assert r.steps == [CastOnStep(40), BindOffStep(40)]


def test_cast_on_width_rounds_and_reports():
    # 5 in * 2.5 = 12.5 -> 13
    r = run(GAUGE + "cast_on 5 in\nbind_off")
    assert r.final_stitches == 13
    assert len(r.messages) == 1


# ---- row and group math ----
def first_row(src):
    return rows(run(src))[0]


def test_rib_fits_evenly():
    s = first_row(GAUGE + "cast_on 40 sts\nrow: (k2, p2) to end.")
    assert (s.worked, s.unworked) == (40, 0)


def test_rib_leaves_one_stitch_over():
    s = first_row(GAUGE + "cast_on 41 sts\nrow: (k2, p2) to end.")
    assert (s.worked, s.unworked) == (40, 1)


def test_to_last_then_finish():
    # width 2, usable 38 -> 19 repeats, then k2 uses the last 2
    s = first_row(GAUGE + "cast_on 40 sts\nrow: (k1, p1) to last 2, k2.")
    assert s.unworked == 0


def test_times_repeat_leaves_stitches():
    s = first_row(GAUGE + "cast_on 40 sts\nrow: (k2, p2) 5 times.")
    assert (s.worked, s.unworked) == (20, 20)


def test_plain_stitches_on_longer_row():
    s = first_row(GAUGE + "cast_on 40 sts\nrow: k2, p2.")
    assert s.unworked == 36


def test_row_asking_for_too_many_stitches():
    s = first_row(GAUGE + "cast_on 3 sts\nrow: k5.")
    assert s.unworked == -2


def test_row_numbers_run_across_the_pattern():
    r = run(GAUGE + "cast_on 10 sts\nrow: k to end.\nfor 3 times:\n row: p to end.\nend")
    assert [s.number for s in rows(r)] == [1, 2, 3, 4]


# ---- notes ----
def test_note_in_loop_prints_once():
    src = GAUGE + ('cast_on 10 sts\nfor 3 times:\n'
                   ' note: "Slip first stitch"\n row: k to end.\nend')
    r = run(src)
    assert [s for s in r.steps if isinstance(s, NoteStep)] == [NoteStep("Slip first stitch")]
    assert len(rows(r)) == 3
    assert r.steps[1] == NoteStep("Slip first stitch")   # sits before the first row


# ---- errors ----
def test_row_before_cast_on_raises():
    with pytest.raises(LoopyError):
        run(GAUGE + "row: k to end.")


# ---- every reference pattern must run ----
@pytest.mark.parametrize("path", REFERENCE_FILES, ids=lambda p: p.name)
def test_reference_pattern_runs(path):
    r = run_pattern(parse_file(path))
    assert r.total_rows > 0
    assert r.final_stitches > 0