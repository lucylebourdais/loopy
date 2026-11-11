from pathlib import Path
from lark import Lark
from transformer import LoopyTransformer

ROOT = Path(__file__).parent

_PARSER = Lark((ROOT/"grammar"/"loopy.lark").read_text(), parser="earley")

def parse_pattern(text):
    # Loopy source text -> Pattern (AST)
    tree = _PARSER.parse(text)
    return LoopyTransformer().transform(tree)


def parse_file(path):
    # Convenience wrapper: read a file, then parse its contents.
    return parse_pattern(Path(path).read_text())