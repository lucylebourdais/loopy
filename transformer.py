from lark import Transformer, Token
from ast_nodes import (
    Gauge, RepeatMode, Stitch, Group, Row, Note, CastOn, BindOff, LengthBound, CountBound, ForLoop, Pattern,
)

class LoopyTransformer(Transformer):
    """There will be 1 method per named node in the grammar. Lark will walk the tree bottom-up and call each method
    with the node's transformed children as a list."""

    # Top level

    def start(self, items):
        # items = either:
        # [title_str, Gauge, stmt, stmt...] (pattern has a title)
        # [Gauge, stmt, stmt...] (pattern has no title)
        title = None
        if isinstance(items[0], str):
            # title_stmt returns plain str
            # Gauge is not a str, so this checks if there is a title_stmt
            title, items = items[0], items[1:]
        # first item is the gauge, everything else is a statement
        gauge, *statements = items
        return Pattern(title, gauge, statements)

    def title_stmt(self, items):
        # items = [Token('ESCAPED_STRING', '"Simple Dishcloth"')]
        return str(items[0])[1:-1] # [1:-1] slices off quotation marks in token

    def gauge_stmt(self, items):
        length, unit, sts, rows = items
        # float() necessary for later math
        return Gauge(float(length), str(unit), float(sts), float(rows))

    def statement(self, items):
        return items[0]

    # Simple statements
    def cast_on_count(self, items):
        # in "cast_on 40 sts"
        # items = ['40']
        return CastOn(stitches=int(items[0]))

    def cast_on_width(self, items):
        # in "cast_on 16 in"
        # items = ['16','in']
        return CastOn(width=float(items[0]), unit=str(items[1]))

    def bind_off_stmt(self, items):
        return BindOff()

    def note_stmt(self, items):
        return Note(str(items[0])[1:-1])

    # Loops

    def length_bound(self, items):
        # "for 8 in"
        # items = ['8', 'in']
        return LengthBound(float(items[0]), str(items[1]))

    def count_bound(self, items):
        # "for 15 times"
        # items = ['15']
        return CountBound(int(items[0]))

    def loop_item(self, items):
        return items[0]

    def for_stmt(self, items):
        # items = length/count bound, then each row/note in the body
        return ForLoop(bound=items[0], body=list(items[1:]))

    # Repeat modes

    def times_mode(self, items):
        # "5 times"
        # items = ['5']
        return RepeatMode("times", int(items[0]))

    def to_end_mode(self, items):
        # items = []
        return RepeatMode("to_end")

    def to_last_mode(self, items):
        # "to last 2'
        # items = ['2']
        return RepeatMode("to_last", int(items[0]))

    # Stitches and rows

    def group_stitch(self, items):
        # items = [Token STITCH_TYPE] or [Token STITCH_TYPE, Token INT]
        # count checks length since "k" is 1 item, and "k2" is 2 items
        count = int(items[1]) if len(items) > 1 else 1
        return Stitch(str(items[0]).lower(), count)

    def group_repeat(self, items):
        # items = [Stitch,..., RepeatMode]
        # everything but last item is a stitch
        # last item is the mode
        return Group(stitches=list(items[:-1]), mode=items[-1])

    def stitch_repeat(self, items):
        # items = either:
        # [type]
        # [type, count]
        # [type, mode]
        # [type, count, mode]
        kind = str(items[0]).lower()
        count, mode = 1, None
        for x in items[1:]:
            # leftover token must be the count
            if isinstance(x, Token):
                count = int(x)
            else:
                mode = x
        return Stitch(kind, count, mode)

    def stitch_item(self, items):
        return items[0]

    def row_stmt(self, items):
        # optional leading number appears as a Token
        label = None
        # if there's a leading number, it will be first
        if isinstance(items[0], Token):
            label, items = int(items[0]), items[1:]
        return Row(items=list(items), label=label)


