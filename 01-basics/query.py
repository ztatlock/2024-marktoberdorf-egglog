from dataclasses import dataclass

@dataclass(frozen=True)
class Pat:
  '''Base class for patterns.'''
  pass

@dataclass(frozen=True)
class AtomPat(Pat):
  atom: int | float | str
  vres: str

  def __str__(self):
    return f'{self.atom} ∈ {self.vres}'

  def match(self, subst, res: int):
    return subst.bind(self.vres, res)

@dataclass(frozen=True)
class AppPat(Pat):
  op: str
  vargs: list[str]
  vres: str

  def __str__(self):
    args = ' '.join(self.vargs)
    return f'({self.op} {args}) ∈ {self.vres}'

  def match(self, subst, args: list[int], res: int):
    assert len(self.vargs) == len(args)
    for varg, arg in zip(self.vargs, args):
      subst = subst.bind(varg, arg)
    return subst.bind(self.vres, res)

class Query:
  def __init__(self, pats: list[Pat]):
    self.pats = pats

  def __str__(self):
    return "\n".join(str(pat) for pat in self.pats)

  def __repr__(self):
    return repr(self.pats)

  def __iter__(self):
    return iter(self.pats)

import unittest
import subst

class TestPatterns(unittest.TestCase):
  def test_atom_pat_match(self):
    atom_pat = AtomPat(0, 'ec0')
    s0 = subst.Subst({})
    s1 = atom_pat.match(s0, 42)
    expected_subst = subst.Subst({'ec0': 42})
    self.assertEqual(s1, expected_subst)

  def test_atom_pat_mismatch(self):
    atom_pat = AtomPat(0, 'ec0')
    s0 = subst.Subst({})
    s1 = atom_pat.match(s0, 42)
    s2 = atom_pat.match(s1, 43)
    self.assertEqual(s2, subst._bogus)

  def test_app_pat_match(self):
    app_pat = AppPat('+', ['x', 'y'], 'z')
    s0 = subst.Subst({})
    s1 = app_pat.match(s0, [1, 2], 3)
    expected_subst = subst.Subst({'x': 1, 'y': 2, 'z': 3})
    self.assertEqual(s1, expected_subst)

  def test_app_pat_mismatch(self):
    s0 = subst.Subst({'x': 0})
    app_pat = AppPat('+', ['x', 'y'], 'z')
    s1 = app_pat.match(s0, [1, 2], 3)
    self.assertEqual(s1, subst._bogus)

if __name__ == '__main__':
  unittest.main()
