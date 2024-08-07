# ENode Tables
#
# These tables represent how an operator maps classes of arguments to a class of
# results. They maintain functional dependency by merging classes whenever the
# same arguments would map to different results. This essentially provides
# congruence closure. However, merges from other tables may implicitly
# invalidate the functional dependency, so we need to periodically rebuild the
# table by canonicallizing all eclass ids and adding everything back.

class AppTab:
  def __init__(self, uf):
    self.uf = uf
    self.tab: dict[tuple[int, ...], int] = {}

  def __str__(self):
    res = ""
    for ids, id in sorted(self.tab.items()):
      sids = "\t".join(str(i) for i in ids)
      res += f"{sids}\t->\t{id}\n"
    return res

  def get(self, ids: tuple[int, ...]) -> int:
    # if necessary, add a new enode
    if ids not in self.tab:
      self.tab[ids] = self.uf.mkset()
    return self.tab[ids]

  def set(self, ids: tuple[int, ...], id: int) -> int:
    if ids in self.tab:
      # restore functional dependency by merging
      # NOTE: uf tracks dirty flag if anything changes
      id = self.uf.union(self.tab[ids], id)
    self.tab[ids] = id
    return id

  # one iteration of rebuilding
  # the egraph will repeat this until nothing changes
  def rebuild(self):
    # save and reset
    old = self.tab
    self.tab = {}

    # add canonicalized enodes back to the table
    for ids, id in old.items():
      ids = tuple(self.uf.find(i) for i in ids)
      id = self.uf.find(id)
      self.set(ids, id)

import unittest
import uf

class TestAppTab(unittest.TestCase):

  def test_get_new_enode(self):
    # setup
    t = AppTab(uf.UF())
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    ids = (0, 1, 2)
    ec = t.get(ids)
    self.assertEqual(ec, 3)
    self.assertEqual(t.tab[ids], 3)

  def test_get_existing_enode(self):
    t = AppTab(uf.UF())
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    ids0 = (0, 1, 2)
    ids1 = (3, 4, 5)
    ec0 = t.get(ids0)
    ec1 = t.get(ids1)
    ec2 = t.get(ids0) # should return the same as the first
    self.assertEqual(ec0, 6)
    self.assertEqual(ec1, 7)
    self.assertEqual(ec2, 6)
    self.assertEqual(t.tab[ids0], 6)
    self.assertEqual(t.tab[ids1], 7)

  def test_set_enode(self):
    t = AppTab(uf.UF())
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    ids0 = (0, 1, 2)
    ids1 = (3, 4, 5)
    ec0 = t.get(ids0)
    ec1 = t.get(ids1)
    t.set(ids0, ec1) # should merge ec0 and ec1 (congruence since ids0 in ec0 and ec1)
    self.assertEqual(t.uf.find(ec0), t.uf.find(ec1))

  def test_rebuild(self):
    t = AppTab(uf.UF())
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    t.uf.mkset()
    ids0 = (0, 1, 2)
    ids1 = (0, 1, 3)
    ec0 = t.get(ids0)
    ec1 = t.get(ids1)
    self.assertNotEqual(ec0, ec1)
    self.assertNotEqual(t.uf.find(ec0), t.uf.find(ec1))
    t.uf.union(2, 3) # functional dependency violated by merge outside this table
    t.rebuild()
    self.assertEqual(t.uf.find(ec0), t.uf.find(ec1)) # check congruence closure

if __name__ == "__main__":
  unittest.main()

