# Term S-expressions

from dataclasses import dataclass
import lark
import unittest

@dataclass(frozen=True)
class Expr:
  """Base class for expressions."""
  pass

@dataclass(frozen=True)
class Atom(Expr):
  atom: int | float | str

  def __str__(self) -> str:
    return str(self.atom)

@dataclass(frozen=True)
class App(Expr):
  op: str
  args: list[Expr]

  def __str__(self) -> str:
    args = " ".join(map(str, self.args))
    return f"({self.op} {args})"

grammar = """
  ?start : expr

  ?expr : app
        | atom

  app : "(" op expr* ")"

  op : /[a-zA-Z_+*\\/-][a-zA-Z0-9_+*\\/-]*/

  atom : SIGNED_INT                -> int_lit
       | SIGNED_FLOAT              -> float_lit
       | /[a-zA-Z_][a-zA-Z0-9_-]*/ -> variable

  %import common.SIGNED_INT
  %import common.SIGNED_FLOAT
  %import common.WS
  %ignore WS
"""

_parser = lark.Lark(grammar, start="start", parser="lalr")

class ExprTransformer(lark.Transformer):
  def int_lit(self, items):
    return Atom(int(items[0]))

  def float_lit(self, items):
    return Atom(float(items[0]))

  def variable(self, items):
    return Atom(str(items[0]))

  def op(self, items):
    return str(items[0])

  def app(self, items):
    op = items[0]
    args = items[1:]
    return App(op, args)

  def expr(self, items):
    return items[0]

  def start(self, items):
    return items[0]

_transformer = ExprTransformer()

def parse(s):
  return _transformer.transform(_parser.parse(s))

class TestExprParser(unittest.TestCase):
  def test_int_lit(self):
    expr = parse("42")
    self.assertEqual(str(expr), "42")
    self.assertIsInstance(expr, Atom)
    self.assertEqual(expr.atom, 42)

  def test_float_lit(self):
    expr = parse("3.14")
    self.assertEqual(str(expr), "3.14")
    self.assertIsInstance(expr, Atom)
    self.assertEqual(expr.atom, 3.14)

  def test_variable(self):
    expr = parse("x")
    self.assertEqual(str(expr), "x")
    self.assertIsInstance(expr, Atom)
    self.assertEqual(expr.atom, "x")

  def test_simple_app(self):
    expr = parse("(+ x 0)")
    self.assertEqual(str(expr), "(+ x 0)")
    self.assertIsInstance(expr, App)
    self.assertEqual(expr.op, "+")
    self.assertEqual(len(expr.args), 2)
    self.assertEqual(str(expr.args[0]), "x")
    self.assertEqual(str(expr.args[1]), "0")

  def test_nested_app(self):
    expr = parse("(- (+ x y) x)")
    self.assertEqual(str(expr), "(- (+ x y) x)")
    self.assertIsInstance(expr, App)
    self.assertEqual(expr.op, "-")
    self.assertEqual(len(expr.args), 2)
    self.assertIsInstance(expr.args[0], App)
    self.assertEqual(expr.args[0].op, "+")
    self.assertEqual(len(expr.args[0].args), 2)
    self.assertEqual(str(expr.args[0].args[0]), "x")
    self.assertEqual(str(expr.args[0].args[1]), "y")
    self.assertEqual(str(expr.args[1]), "x")

if __name__ == "__main__":
  unittest.main()
