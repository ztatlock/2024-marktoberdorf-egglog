# Union-Find (aka Disjoint Set)

import unittest

class UF:
  def __init__(self):
    self.parent: list[int] = []
    self.dirty: bool = False

  def mkset(self) -> int:
    # allocate a fresh new id (set) at the end
    id = len(self.parent)
    self.parent.append(id)
    return id

  def find(self, id: int) -> int:
    # leaders are the fixed points of the parent function
    if self.parent[id] == id:
      return id

    # for non-leaders, we conceptually just want to recurse on their parent
    #   return self.find(self.parent[id])
    #
    # but we can do better by "path compression" to make future finds faster
    leader = self.find(self.parent[id])
    self.parent[id] = leader
    return leader

  def union(self, id1: int, id2: int) -> int:
    l1 = self.find(id1)
    l2 = self.find(id2)

    # already in the same set
    if l1 == l2:
      return l1

    # during rebuilding we will need to know if anything changed
    self.dirty = True

    # pick the lower id as "winner" -- not optimial, but simple
    # could also use "union by rank" or "union by size"
    if l1 <= l2:
      self.parent[l2] = l1
      return l1
    else:
      self.parent[l1] = l2
      return l2

class TestUF(unittest.TestCase):
  def test_mkset(self):
    uf = UF()
    id0 = uf.mkset()
    id1 = uf.mkset()
    self.assertEqual(id0, 0)
    self.assertEqual(id1, 1)
    self.assertEqual(uf.parent, [0, 1])

  def test_find(self):
    uf = UF()
    id0 = uf.mkset()
    id1 = uf.mkset()
    self.assertEqual(uf.find(id0), id0)
    self.assertEqual(uf.find(id1), id1)

  def test_union(self):
    uf = UF()
    id0 = uf.mkset()
    id1 = uf.mkset()
    uf.union(id0, id1)
    self.assertEqual(uf.find(id0), uf.find(id1))
    self.assertTrue(uf.dirty)

  def test_union_and_find_with_path_compression(self):
    uf = UF()
    id0 = uf.mkset()
    id1 = uf.mkset()
    id2 = uf.mkset()
    uf.union(id0, id1)
    uf.union(id1, id2)
    leader = uf.find(id2)
    # check path compression
    self.assertEqual(uf.parent[id2], leader)
    self.assertEqual(leader, uf.find(id0))
    self.assertEqual(leader, uf.find(id1))
    self.assertEqual(leader, uf.find(id2))

if __name__ == "__main__":

  print("\n# SAMPLE USAGE")

  uf = UF()
  id0 = uf.mkset()
  id1 = uf.mkset()
  id2 = uf.mkset()
  id3 = uf.mkset()

  print(f"\nInitial sets:")
  print(f"  {uf.parent}")

  uf.union(id0, id1)
  print(f"\nAfter union(id0, id1):")
  print(f"  {uf.parent}")

  uf.union(id2, id3)
  print(f"\nAfter union(id2, id3):")
  print(f"  {uf.parent}")

  uf.union(id0, id2)
  print(f"\nAfter union(id0, id2):")
  print(f"  {uf.parent}")

  leader = uf.find(id3)
  print(f"\nLeader of id2: {leader}")

  print(f"\nSets after path compression (side effect of find on id2):")
  print(f"  {uf.parent}")

  print("\n\n# UNIT TESTS")
  unittest.main()
