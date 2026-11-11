# interpreter will walk the AST, handle the gauge math and track the state

import math
from fractions import Fraction

from ast_nodes import Group, Stitch, Row, Note, CastOn, BindOff, CountBound, ForLoop
from results import CastOnStep, RowStep, NoteStep, BindOffStep, RunResult

class LoopyError(Exception):
    """Raised when a Loopy pattern cannot be worked at all."""

# everything will be converted from mm
# this allows a pattern with the gauge declared in cm to run a length in inches
MM_PER_UNIT = {
    'in': Fraction(254,10),
    'cm': Fraction(10),
    'mm': Fraction(1),
}

def _frac(value):
    return Fraction(str(value))

def half_up(x):
    return math.floor(x + Fraction(1,2))

class Interpreter:
    def __init__(self, pattern):
        self.pattern = pattern
        g = pattern.gauge
        if g.length <= 0 or g.stitches <= 0 or g.rows <= 0:
            raise LoopyError("Gauge number must all be greater than zero")

        # gauge swatch is g.length wide, measured in g.unit
        # convert to mm, then work out sts and rows per mm
        # the per-mm value will work for ANY unit later
        swatch_mm = _frac(g.length) * MM_PER_UNIT[g.unit]
        self.sts_per_mm = _frac(g.stitches) / swatch_mm
        self.rows_per_mm = _frac(g.rows) / swatch_mm

        # running state (starts empty)
        self.stitches = None
        self.rows_done = 0
        self.steps = []
        self.messages = []

    # _rows_in, _stitches_in, _length_of_rows
    # These class functions will handle gauge conversions
    def _rows_in(self, length, unit):
        # how many rows fit in 'length' 'unit's
        return _frac(length) * MM_PER_UNIT[unit] * self.rows_per_mm

    def _stitches_in(self, length, unit):
        return _frac(length) * MM_PER_UNIT[unit] * self.sts_per_mm

    def _length_of_rows(self, rows, unit):
        # the length of an n rows piece is in 'unit'
        return Fraction(rows) / (MM_PER_UNIT[unit] * self.rows_per_mm)

    # run, _exec
    # These class functions will handle the main entry point of a loopy program
    def run(self):
        for stmt in self.pattern.statements:
            self._exec(stmt, first_pass=True)
        unit = self.pattern.gauge.unit
        return RunResult(
            title = self.pattern.title,
            steps = self.steps,
            messages = self.messages,
            total_rows = self.rows_done,
            final_stitches = self.stitches or 0,
            total_length = float(self._length_of_rows(self.rows_done, unit)),
            unit = unit,
            stitches_per_unit = float(self.sts_per_mm * MM_PER_UNIT[unit]),
            rows_per_unit = float(self.rows_per_mm * MM_PER_UNIT[unit]),
        )

    def _exec(self, node, first_pass):
        if isinstance(node, CastOn):
            self._cast_on(node)
        elif isinstance(node, BindOff):
            self._bind_off()
        elif isinstance(node, Note):
            if first_pass: # first_pass is only True on first pass of a loop, which is how notes will only print once
                self.steps.append(NoteStep(node.text))
        elif isinstance(node, Row):
            self._row(node)
        elif isinstance(node, ForLoop):
            self._loop(node)
        else:
            raise LoopyError(f"Don't know how to work {node!r}")

    # _cast_on, _bind_off
    # These class functions will handle how casting of and binding off affects the stitch count
    def _cast_on(self, node):
        if node.stitches is not None:
            # "cast_on 40 sts" -> 40 sts on needle (no math needed)
            self.stitches = node.stitches
        else:
            exact = self._stitches_in(node.width, node.unit)
            self.stitches = half_up(exact)
            if exact != self.stitches:
                self.messages.append(
                    f"Adjusted 'cast_on {node.width:g} {node.unit}' to "
                    f"{self.stitches} stitches (the gauge gives {float(exact):.2f})."
                )
        self.steps.append(CastOnStep(self.stitches))

    def _bind_off(self):
        if self.stitches is None:
            raise LoopyError("bind_off before cast_on: there are no stitches to bind off.")
        self.steps.append(BindOffStep(self.stitches))

    # _loop, _repeats_for_length
    # These class functions will handle how loops are calculated into the total length of a design
    def _loop(self, loop):
        # a note should not count as a row, so only count the row objects in the body
        body_rows = sum(1 for item in loop.body if isinstance(item, Row))
        if body_rows == 0:
            raise LoopyError("A loop needs at least 1 row in its body")
        if isinstance(loop.bound, CountBound):
            repeats = loop.bound.times
        else:
            repeats = self._repeats_for_length(loop.bound, body_rows)
        for i in range(repeats):
            for item in loop.body:
                self._exec(item, first_pass=(i == 0)) # indicates whether interpreter is on the first iteration

    def _repeats_for_length(self, bound, body_rows):
        target_rows = self._rows_in(bound.length, bound.unit)   # how many rows does a length need
        repeats = max(1, half_up(target_rows / body_rows))      # how many loop repeats to satisfy target_rows
        actual_rows = repeats * body_rows                       # how many rows will actually be worked
        if actual_rows != target_rows:
            actual_len = self._length_of_rows(actual_rows, bound.unit)
            self.messages.append(
                f"Adjusted 'for {bound.length:g} {bound.unit}' to {repeats} repeats "
                f"({actual_rows} rows, {float(actual_len):.2f} {bound.unit} "
                f"so the loop ends on a full repeat."
            )
        return repeats

    # _row, _work, run_pattern
    # These class functions will handle how an amount of rows is calculated for count bound and length bound loops
    def _row(self, row):
        if self.stitches is None:
            raise LoopyError("A row is worked before cast_on: there are no stitches yet.")

        self.rows_done += 1

        remaining = self.stitches
        for item in row.items:
            remaining = self._work(item, remaining)

        self.steps.append(RowStep(
            number = self.rows_done,
            label = row.label,
            items = row.items,
            # stitch count doesn't change, self.stitches stays the same
            # adding shaping feature would change stitches here
            stitches_before = self.stitches,
            worked = self.stitches - remaining,
            unworked = remaining,
        ))
    # work 1 stitch or group, return the remaining stitches in the row
    def _work(self, item, remaining):
        if isinstance(item, Group):
            width = sum(s.count for s in item.stitches) # (k2, p2) is 4 stitches wide
            mode = item.mode
        elif isinstance(item, Stitch):
            if item.mode is None:
                return remaining - item.count # k2 is 2 stitches wide
            width = item.count
            mode = item.mode
        else:
            raise LoopyError(f"Unexpected row item {item!r}")
        if width <= 0:
            raise LoopyError("A stitch group must use at least 1 stitch")
        if mode.kind == "times":
            repeats = mode.value
        elif mode.kind == "to_end":
            repeats = max(0, remaining // width)
        elif mode.kind == "to_last":
            repeats = max(0, (remaining - mode.value) // width)
        else:
            raise LoopyError(f"Unknown repeat mode {mode.kind!r}")

        return remaining - (repeats * width)

def run_pattern(pattern):
    return Interpreter(pattern).run()