import pattern

class Query:
  def __init__(self, pats: list[pattern.Pat]):
    self.pats = pats

  def pvars(self):
    pvs = set()
    for pat in self.pats:
      pvs.update(pat.pvars())
    return pvs

  def __str__(self):
    return "\n".join(str(pat) for pat in self.pats)

  def __repr__(self):
    return repr(self.pats)

  def __iter__(self):
    return iter(self.pats)

def parse(s: str) -> Query:
  ps = []
  for l in s.splitlines():
    l = l.strip()
    if not l:
      continue
    ps.append(pattern.parse(l))
  return Query(ps)
