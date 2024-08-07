import uf
import expr
import table
import query
import subst

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

  def get_expr(self, e):
    match e:
      case expr.Atom(a):
        if a not in self.atom:
          self.atom[a] = self.uf.mkset()
        return self.atom[a]

      case expr.App(op, args):
        if op not in self.atab:
          self.atab[op] = table.AppTab(self.uf)
        ids = tuple(self.get_expr(arg) for arg in args)
        return self.atab[op].get(ids)

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
      case query.AtomPat(a, _):
        # no matches if we do not have this literal
        if a not in self.atom:
          return subst.Set()

        # otherwise check all substitutions for this pattern
        ss = subst.Set()
        id = self.atom[a]
        for s in substs:
          ss.add(pat.match(s, id))
        return ss

      case query.AppPat(op, _, _):
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

  def query(self, q):
    # initially, we only have the empty substitution
    substs = subst.Set()
    substs.add(subst.Subst({}))

    # match all patterns in the query
    for pat in q:
      substs = self.matches(substs, pat)

    # return all substitutions that make all patterns match
    return substs

import unittest

class TestEGraph(unittest.TestCase):
  def setUp(self):
    self.eg = EGraph()

  def test_add_atom(self):
    id = self.eg.get_sexpr('42')
    self.assertEqual(self.eg.atom[42], id)

  def test_add_app(self):
    id = self.eg.get_sexpr('(+ 1 2)')
    self.assertTrue(id in self.eg.atab['+'].tab.values())

  def test_rebuild(self):
    self.eg.get_sexpr('(+ 1 2)')
    self.eg.uf.union(self.eg.atom[1], self.eg.atom[2])
    self.eg.rebuild()
    self.assertEqual(self.eg.uf.find(self.eg.atom[1]), self.eg.uf.find(self.eg.atom[2]))

  def test_query_atom(self):
    self.eg.get_sexpr('42')
    q = query.Query([query.AtomPat(42, 'x')])
    substs = self.eg.query(q)
    expected_subst = subst.Subst({'x': self.eg.atom[42]})
    self.assertIn(expected_subst, substs.substs)

  def test_query_app(self):
    self.eg.get_sexpr('(+ 1 2)')
    q = query.Query([query.AppPat('+', ['x', 'y'], 'z')])
    substs = self.eg.query(q)
    expected_subst = subst.Subst({
      'x': self.eg.atom[1],
      'y': self.eg.atom[2],
      'z': self.eg.atab['+'].get((self.eg.atom[1], self.eg.atom[2]))
    })
    self.assertIn(expected_subst, substs.substs)

if __name__ == '__main__':
  unittest.main()
