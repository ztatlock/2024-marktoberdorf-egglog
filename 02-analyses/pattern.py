from dataclasses import dataclass

@dataclass(frozen=True)
class Pat:
  """Base class for patterns."""
  pass

@dataclass(frozen=True)
class AtomPat(Pat):
  atom: int | float | str
  vres: str

  def __str__(self):
    # maybe using "∈" would be more clear than = 🤷
    return f"{self.atom} = {self.vres}"

  def match(self, subst, res: int):
    return subst.bind(self.vres, res)

  def pvars(self):
    return {self.vres}

@dataclass(frozen=True)
class AppPat(Pat):
  op: str
  vargs: list[str]
  vres: str

  def __str__(self):
    args = " ".join(self.vargs)
    return f"({self.op} {args}) = {self.vres}"

  def match(self, subst, args: list[int], res: int):
    assert len(self.vargs) == len(args)
    for varg, arg in zip(self.vargs, args):
      subst = subst.bind(varg, arg)
    return subst.bind(self.vres, res)

  def pvars(self):
    return set(self.vargs).union({self.vres})


#
# PARSING
#

import lark

grammar = """
  ?start: pattern

  ?pattern: atom_pattern
          | app_pattern

  atom_pattern: atom "=" patvar -> atom_pat

  app_pattern: "(" op patvar* ")" "=" patvar -> app_pat

  op : /[a-zA-Z_+*\\/\\-~][a-zA-Z0-9_+*\\/\\-~]*/

  atom : SIGNED_INT                -> int_lit
       | SIGNED_FLOAT              -> float_lit
       | /[a-zA-Z_][a-zA-Z0-9_-]*/ -> variable

  patvar: /\\?[a-zA-Z0-9_]*/

  %import common.SIGNED_INT
  %import common.SIGNED_FLOAT
  %import common.WS
  %ignore WS
"""

_parser = lark.Lark(grammar, start="start", parser="lalr")

@lark.v_args(inline=True)
class PatternTransformer(lark.Transformer):
  def int_lit(self, value):
    return int(value)

  def float_lit(self, value):
    return float(value)

  def variable(self, value):
    return str(value)

  def op(self, value):
    return str(value)

  def patvar(self, value):
    return str(value)

  def atom_pat(self, atom, patvar):
    return AtomPat(atom, patvar)

  def app_pat(self, op, *patvars):
    return AppPat(op, patvars[:-1], patvars[-1])

_transformer = PatternTransformer()

def parse(s: str) -> Pat:
  return _transformer.transform(_parser.parse(s))


#
# TESTS
#

import unittest
import subst

class TestPatterns(unittest.TestCase):
  def test_atom_pat_match(self):
    atom_pat = AtomPat(0, "?0")
    s0 = subst.Subst({})
    s1 = atom_pat.match(s0, 42)
    expected_subst = subst.Subst({"?0": 42})
    self.assertEqual(s1, expected_subst)

  def test_atom_pat_mismatch(self):
    atom_pat = AtomPat(0, "?0")
    s0 = subst.Subst({})
    s1 = atom_pat.match(s0, 42)
    s2 = atom_pat.match(s1, 43)
    self.assertEqual(s2, subst._bogus)

  def test_app_pat_match(self):
    app_pat = AppPat("+", ["?x", "?y"], "?z")
    s0 = subst.Subst({})
    s1 = app_pat.match(s0, [1, 2], 3)
    expected_subst = subst.Subst({"?x": 1, "?y": 2, "?z": 3})
    self.assertEqual(s1, expected_subst)

  def test_app_pat_mismatch(self):
    s0 = subst.Subst({"?x": 0})
    app_pat = AppPat("+", ["?x", "?y"], "?z")
    s1 = app_pat.match(s0, [1, 2], 3)
    self.assertEqual(s1, subst._bogus)

  def test_parse_atom_pat(self):
    pat = parse("42 = ?42")
    self.assertEqual(str(pat), "42 = ?42")

  def test_parse_app_pat(self):
    pat = parse("(+ ?l ?r) = ?x")
    self.assertEqual(str(pat), "(+ ?l ?r) = ?x")

if __name__ == "__main__":
  unittest.main()
