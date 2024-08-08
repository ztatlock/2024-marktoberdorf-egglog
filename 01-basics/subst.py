import unittest

# Substitutions bind query pattern variables (strings) to eclass ids (ints).
#
# In a real implementation, we would also use integers for pattern variables
# because they are small and fast to compare. In this simple demo, we use
# strings for variables to provide nicer printing and debugging.
#
# We do not want extending a substitution to affect other substitiions. Also, we
# do want to deduplicate sets of substitutions. So we use a "functional" design
# where extending a substitutions returns a new substitution. This is slow, but
# it also helps make substitutions hashable and therefore easy to deduplicate.
#
# We want to be able to chain bindings, so we also have a special "bogus" value
# that represents a failed binding.

class Subst:
  def __init__(self, subst: dict[str, int]):
    self.subst = subst
    self._hash = hash(frozenset(subst.items()))

  def bind(self, var, val):
    # if var bound, check for consistency
    if var in self.subst:
      if self.subst[var] == val:
        # consistent, reuse self
        return self
      else:
        # bogus, reuse global singleton instance
        return _bogus

    # otherwise bind var to val in a new substitution (copy on write)
    s = self.subst.copy()
    s[var] = val
    return Subst(s)

  def __str__(self):
    return str(self.subst)

  def __repr__(self):
    return repr(self.subst)

  def __hash__(self):
    return self._hash

  def __eq__(self, other):
    if isinstance(other, Subst):
      return self.subst == other.subst
    return False

class Bogus:
  def __init__(self):
    pass

  def bind(self, var, val):
    return self

  def __str__(self):
    return "bogus"

  def __repr__(self):
    return "bogus"

  def __hash__(self):
    return hash("bogus")

  def __eq__(self, other):
    return isinstance(other, Bogus)

_bogus = Bogus()

# sets of substitutions
# filters out any bogus additions
class Set:
  def __init__(self):
    self.substs = set()

  def add(self, s):
    if isinstance(s, Subst):
      self.substs.add(s)

  def __str__(self):
    return str(self.substs)

  def __repr__(self):
    return repr(self.substs)

  def __iter__(self):
    return iter(self.substs)


class TestSubst(unittest.TestCase):
  def test_empty_subst(self):
    subst = Subst({})
    self.assertEqual(subst.subst, {})
    self.assertTrue(isinstance(subst, Subst))
    self.assertEqual(str(subst), "{}")
    self.assertEqual(repr(subst), "{}")

  def test_bind_new_var(self):
    subst = Subst({})
    new_subst = subst.bind("x", 1)
    self.assertEqual(new_subst.subst, {"x": 1})
    self.assertTrue(isinstance(new_subst, Subst))
    self.assertNotEqual(subst, new_subst)

  def test_bind_existing_var_same_value(self):
    subst = Subst({"x": 1})
    new_subst = subst.bind("x", 1)
    self.assertEqual(new_subst.subst, {"x": 1})
    self.assertTrue(isinstance(new_subst, Subst))
    self.assertEqual(subst, new_subst)

  def test_bind_existing_var_different_value(self):
    subst = Subst({"x": 1})
    new_subst = subst.bind("x", 2)
    self.assertEqual(new_subst, _bogus)
    self.assertFalse(isinstance(new_subst, Subst))

  def test_bogus_subst(self):
    self.assertEqual(str(_bogus), "bogus")
    self.assertEqual(repr(_bogus), "bogus")
    self.assertFalse(isinstance(_bogus, Subst))

  def test_bogus_bind(self):
    new_bogus = _bogus.bind("x", 1)
    self.assertEqual(new_bogus, _bogus)
    self.assertFalse(isinstance(new_bogus, Subst))

  def test_hashable_subst(self):
    subst1 = Subst({"x": 1})
    subst2 = Subst({"x": 1})
    self.assertEqual(hash(subst1), hash(subst2))
    self.assertEqual(subst1, subst2)

  def test_hashable_bogus(self):
    bogus1 = _bogus
    bogus2 = Bogus()
    self.assertEqual(hash(bogus1), hash(bogus2))
    self.assertEqual(bogus1, bogus2)

class TestSet(unittest.TestCase):
  def test_add_valid_subst(self):
    ss = Set()
    subst = Subst({"x": 1})
    ss.add(subst)
    self.assertEqual(len(ss.substs), 1)
    self.assertIn(subst, ss.substs)

  def test_add_bogus_subst(self):
    ss = Set()
    ss.add(_bogus)
    self.assertEqual(len(ss.substs), 0)
    self.assertNotIn(_bogus, ss.substs)

  def test_add_duplicate_subst(self):
    ss = Set()
    subst1 = Subst({"x": 1})
    subst2 = Subst({"x": 1})
    ss.add(subst1)
    ss.add(subst2)
    self.assertEqual(len(ss.substs), 1)

  def test_add_multiple_subst(self):
    ss = Set()
    subst1 = Subst({"x": 1})
    subst2 = Subst({"y": 2})
    ss.add(subst1)
    ss.add(subst2)
    self.assertEqual(len(ss.substs), 2)

if __name__ == "__main__":
  unittest.main()
