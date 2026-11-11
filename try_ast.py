import sys
from pprint import pprint
from loopy_parser import parse_file

# sys.argv is the list of words typed on the command line
# python try_ast.py -> ["try_ast.py"]
# python try_ast.py reference_patterns/scarf.loopy -> ["try_ast.py", "reference_patterns/scarf.loopy"]
# ^ otherwise defaults to dishcloth.loopy
path = sys.argv[1] if len(sys.argv) > 1 else "reference_patterns/dishcloth.loopy"

pprint(parse_file(path))