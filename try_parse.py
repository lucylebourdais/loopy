
from pathlib import Path
from lark import Lark

ROOT = Path(__file__).parent
grammar = (ROOT / "grammar" / "loopy.lark").read_text()
parser = Lark(grammar, parser="earley")

path = ROOT / "grammar" / "loopy.lark"
print("Reading:", path)
print("Length:", len(path.read_text()), "characters")
print(path.read_text()[:200])

source = (ROOT / "reference_patterns" / "scarf.loopy").read_text()
print(parser.parse(source).pretty())




