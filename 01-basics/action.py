from dataclasses import dataclass

@dataclass(frozen=True)
class ActionExpr:
  """Base class for actions"""
  pass

@dataclass(frozen=True)
class Atom(ActionExpr):
  atom: int | float | str

  def __str__(self) -> str:
    return str(self.atom)

  def pvars(self) -> set[str]:
    return set()

@dataclass(frozen=True)
class PatVar(ActionExpr):
  name: str

  def __str__(self) -> str:
    return self.name

  def pvars(self) -> set[str]:
    return {self.name}

@dataclass(frozen=True)
class App(ActionExpr):
  op: str
  args: list[ActionExpr]

  def __str__(self) -> str:
    args = " ".join(map(str, self.args))
    return f"({self.op} {args})"

  def pvars(self) -> set[str]:
    pvs = set()
    for arg in self.args:
      pvs.update(arg.pvars())
    return pvs

@dataclass(frozen=True)
class Action:
  """Base class for actions"""
  pass

@dataclass(frozen=True)
class Nop(Action):
  def __str__(self) -> str:
    return f"nop"

  def pvars(self) -> set[str]:
    return set()

@dataclass(frozen=True)
class Merge(Action):
  l: ActionExpr
  r: ActionExpr

  def __str__(self) -> str:
    return f"{self.l} = {self.r}"

  def pvars(self) -> set[str]:
    pvs_l = self.l.pvars()
    pvs_r = self.r.pvars()
    return pvs_l.union(pvs_r)

@dataclass(frozen=True)
class Seq(Action):
  a1: Action
  a2: Action

  def __str__(self) -> str:
    return f"{self.a1};\n{self.a2}"

  def pvars(self) -> set[str]:
    pvs_a1 = self.a1.pvars()
    pvs_a2 = self.a2.pvars()
    return pvs_a1.union(pvs_a2)


#
# PARSING
#

import lark

grammar = """
  ?start: action

  ?action: seq
         | nop
         | merge

  seq: action ";" action  -> seq
  nop: "nop"              -> nop
  merge: aexpr "=" aexpr  -> merge

  ?aexpr: atom
        | patvar
        | app

  atom: SIGNED_INT                -> int_lit
      | SIGNED_FLOAT              -> float_lit
      | /[a-zA-Z_][a-zA-Z0-9_-]*/ -> variable

  patvar: /\\?[a-zA-Z0-9_]*/

  app: "(" op aexpr* ")"

  op: /[a-zA-Z_+*\\/-][a-zA-Z0-9_+*\\/-]*/

  %import common.SIGNED_INT
  %import common.SIGNED_FLOAT
  %import common.WS
  %ignore WS
"""

_parser = lark.Lark(grammar, start="start", parser="lalr")

@lark.v_args(inline=True)
class ActionTransformer(lark.Transformer):
  def int_lit(self, value):
    return Atom(int(value))

  def float_lit(self, value):
    return Atom(float(value))

  def str_lit(self, value):
    return Atom(str(value[1:-1]))  # Remove the surrounding quotes

  def variable(self, value):
    return Atom(str(value))

  def op(self, value):
    return str(value)

  def patvar(self, value):
    return PatVar(str(value))

  def app(self, op, *args):
    return App(op, list(args))

  def nop(self):
    return Nop()

  def merge(self, l, r):
    return Merge(l, r)

  def seq(self, a1, a2):
    return Seq(a1, a2)

_transformer = ActionTransformer()

def parse(s: str) -> Action:
  return _transformer.transform(_parser.parse(s))

#
# TESTS
#

import unittest

# TODO test atoms vs patvars explicitly
# TODO maybe a few more tests for edge and corner cases

class TestActions(unittest.TestCase):
  def test_parse_nop(self):
    action = parse("nop")
    self.assertEqual(str(action), "nop")

  def test_parse_merge(self):
    action = parse("?x = x")
    self.assertEqual(str(action), "?x = x")

  def test_parse_app_merge(self):
    action = parse("(+ x 0) = ?z")
    self.assertEqual(str(action), "(+ x 0) = ?z")

  def test_parse_seq(self):
    action = parse("nop; x = ?y")
    self.assertEqual(str(action), "nop;\nx = ?y")

if __name__ == "__main__":
  unittest.main()
