# Loopy design decisions

- "for n times" will repeat the loops exactly n times, rather than n rows.
- "for x unit" converts x to rows using gauge, divides by the body's row count, then rounds up to a whole number of 
  repeats.
  - When these rounding changes happen, the interpreter records an "Adjusted..." message.
  - Rounding is half up (12.5 -> 13).
- Notes inside of a loop will only print once, on only the first repetition.
- Notes do not count as rows.
- Gauge math uses exact fractions so that floats never drift.
- Lengths of any unit (in, cm, mm) work with a gauge in any unit.
- k, p, sl1k, and sl1p never change the stitch count
- A row that does not use up the exact current stitch count is recorded