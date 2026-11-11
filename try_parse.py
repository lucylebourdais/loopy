
from pathlib import Path
from lark import Lark

ROOT = Path(__file__).parent
grammar = (ROOT / "grammar" / "loopy.lark").read_text()
parser = Lark(grammar, parser="earley")

path = ROOT / "grammar" / "loopy.lark"

source = (ROOT / "reference_patterns" / "scarf.loopy").read_text()
print(parser.parse(source).pretty())




