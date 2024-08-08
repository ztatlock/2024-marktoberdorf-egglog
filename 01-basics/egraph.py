import uf
import expr
import subst
import pattern
import query
import action
import rule
import table

class EGraph:
  def __init__(self):
    self.uf = uf.UF() # union-find
    self.atab = {} # app tables

    # We do not use tables to store atoms (i.e., enodes without any eclass
    # children). Since they do not have arguments, atoms can never violate
    # functional dependency. Instead we'll use a single dictionary to store all
    # atoms. We will still need to make sure to canonicalize their ids during
    # rebuilding though! Otherwise ematching will not work correctly.
    self.atom = {}

  def __str__(self):
    res = "Atoms:\n"
    for a, id in sorted(self.atom.items()):
      res += f"{a}\t->\t{id}\n"
    res += "\n\n"
    res += "App Tables:\n"
    for op, tab in self.atab.items():
      res += f"{op}:\n{tab}"
    return res

  def get_enode(self, op, ids):
    if op not in self.atab:
      self.atab[op] = table.AppTab(self.uf)
    return self.atab[op].get(ids)

  def get_expr(self, e):
    match e:
      case expr.Atom(a):
        if a not in self.atom:
          self.atom[a] = self.uf.mkset()
        return self.atom[a]

      case expr.App(op, args):
        ids = tuple(self.get_expr(arg) for arg in args)
        return self.get_enode(op, ids)

      case _:
        raise ValueError(f"invalid expression {e}")

  def get_sexpr(self, se):
    return self.get_expr(expr.parse(se))

  def rebuild(self):
    # clear the dirty flag so we can detect changes
    self.uf.dirty = False

    # canonicalize all atoms
    for a, id in list(self.atom.items()):
      self.atom[a] = self.uf.find(id)

    # rebuild all app tables
    for tab in self.atab.values():
      tab.rebuild()

    # if anything changed, we need to keep rebuilding
    if self.uf.dirty:
      self.rebuild()

  def matches(self, substs, pat):
    match pat:
      case pattern.AtomPat(a, _):
        # no matches if we do not have this literal
        if a not in self.atom:
          return subst.Set()

        # otherwise check all substitutions for this pattern
        ss = subst.Set()
        id = self.atom[a]
        for s in substs:
          ss.add(pat.match(s, id))
        return ss

      case pattern.AppPat(op, _, _):
        # no matches if we do not have this operator
        if op not in self.atab:
          return subst.Set()

        # otherwise check all tuples under all substitutions for this pattern
        # database techniques can be EXTREMELY helpful here!
        ss = subst.Set()
        for s in substs:
          for ids, id in self.atab[op].tab.items():
            ss.add(pat.match(s, ids, id))
        return ss

  def query(self, q: query.Query) -> subst.Set:
    # initially, we only have the empty substitution
    substs = subst.Set()
    substs.add(subst.Subst({}))

    # match all patterns in the query
    for pat in q:
      substs = self.matches(substs, pat)

    # return all substitutions that make all patterns match
    return substs

  def squery(self, s: str) -> subst.Set:
    return self.query(query.parse(s))

  def do_action(self, a: action.Action, s: subst.Subst):
    match a:
      case action.Nop():
        pass

      case action.Seq(a1, a2):
        self.do_action(a1, s)
        self.do_action(a2, s)

      case action.Merge(l, r):
        lid = self.get_aexpr(l, s)
        rid = self.get_aexpr(r, s)
        self.uf.union(lid, rid)

      case _:
        raise ValueError(f"invalid action {a}")

  def get_aexpr(self, ae: action.ActionExpr, s: subst.Subst) -> int:
    match ae:
      case action.Atom(a):
        return self.get_expr(expr.Atom(a))

      case action.PatVar(v):
        # raise KeyError if not found
        return s.subst[v]

      case action.App(op, args):
        ids = tuple(self.get_aexpr(arg, s) for arg in args)
        return self.get_enode(op, ids)

      case _:
        raise ValueError(f"invalid action expression {ae}")

  def run_rule(self, r: rule.Rule):
    substs = self.query(r.query)
    for s in substs:
      self.do_action(r.action, s)

  def run_srule(self, sq: str, sa: str):
    r = rule.parse(sq, sa)
    self.run_rule(r)


#
# TESTS
#

import unittest

class TestEGraph(unittest.TestCase):
  def setUp(self):
    self.eg = EGraph()

  def test_add_atom(self):
    id = self.eg.get_sexpr("42")
    self.assertEqual(self.eg.atom[42], id)

  def test_add_app(self):
    id = self.eg.get_sexpr("(+ 1 2)")
    self.assertTrue(id in self.eg.atab["+"].tab.values())

  def test_rebuild(self):
    self.eg.get_sexpr("(+ 1 2)")
    self.eg.uf.union(self.eg.atom[1], self.eg.atom[2])
    self.eg.rebuild()
    self.assertEqual(self.eg.uf.find(self.eg.atom[1]), self.eg.uf.find(self.eg.atom[2]))

  def test_query_atom(self):
    self.eg.get_sexpr("42")
    q = query.parse("42 = ?x")
    substs = self.eg.query(q)
    expected_subst = subst.Subst({"?x": self.eg.atom[42]})
    self.assertIn(expected_subst, substs.substs)

  def test_query_app(self):
    self.eg.get_sexpr("(+ 1 2)")
    q = query.parse("(+ ?x ?y) = ?z")
    substs = self.eg.query(q)
    expected_subst = subst.Subst({
      "?x": self.eg.atom[1],
      "?y": self.eg.atom[2],
      "?z": self.eg.atab["+"].get((self.eg.atom[1], self.eg.atom[2]))
    })
    self.assertIn(expected_subst, substs.substs)

  def test_query_assoc(self):
    self.eg.get_sexpr("(+ 1 (+ 2 3))")
    q = query.parse("""
      (+ ?a ?r) = ?root
      (+ ?b ?c) = ?r
    """)
    substs = self.eg.query(q)
    expected_subst = subst.Subst({
      "?a": self.eg.atom[1],
      "?b": self.eg.atom[2],
      "?c": self.eg.atom[3],
      "?r": self.eg.atab["+"].get((
              self.eg.atom[2],
              self.eg.atom[3])),
      "?root": self.eg.atab["+"].get((
                self.eg.atom[1],
                self.eg.atab["+"].get((
                  self.eg.atom[2],
                  self.eg.atom[3]))))
    })
    self.assertIn(expected_subst, substs.substs)

if __name__ == "__main__":
  unittest.main()
