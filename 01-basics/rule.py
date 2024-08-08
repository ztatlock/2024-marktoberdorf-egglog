import query
import action

class Rule:
  def __init__(self, query, action):
    assert query.pvars().issuperset(action.pvars())
    self.query = query
    self.action = action

def parse(sq: str, sa: str) -> Rule:
  q = query.parse(sq)
  a = action.parse(sa)
  return Rule(q, a)
