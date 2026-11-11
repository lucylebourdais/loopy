import sys
from loopy_parser import parse_file
from interpreter import run_pattern
from results import CastOnStep, RowStep, NoteStep, BindOffStep

path = sys.argv[1] if len(sys.argv) > 1 else "reference_patterns/dishcloth.loopy"
result = run_pattern(parse_file(path))

print(f"== {result.title or 'Untitled'} ==")
print(f"Gauge: {result.stitches_per_unit:g} sts/{result.unit}, "
      f"{result.rows_per_unit:g} rows/{result.unit}")

for step in result.steps:
    if isinstance(step, CastOnStep):
        print(f"cast on {step.stitches}")
    elif isinstance(step, RowStep):
        print(f"row {step.number}: worked {step.worked}, unworked {step.unworked}")
    elif isinstance(step, NoteStep):
        print(f"note: {step.text}")
    elif isinstance(step, BindOffStep):
        print(f"bind off {step.stitches}")

print(f"\nTotals: {result.total_rows} rows, {result.final_stitches} stitches, "
      f"{result.total_length:.2f} {result.unit}")
for message in result.messages:
    print("NOTE:", message)