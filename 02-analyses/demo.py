from egraph import *
import rule

neg_neg = rule.parse('''
  (~ ?a) = ?root
  (~ ?b) = ?a
''', '''
  ?b = ?root
''')

add_neg = rule.parse('''
  (+ ?a ?nb) = ?root
  (~ ?b) = ?nb
''', '''
  (- ?a ?b) = ?root
''')

sub_self = rule.parse('''
  (- ?a ?a) = ?root
''', '''
  0 = ?root
''')

add_comm = rule.parse('''
  (+ ?l ?r) = ?x
''', '''
  (+ ?r ?l) = ?x
''')

mul_comm = rule.parse('''
  (* ?l ?r) = ?x
''', '''
  (* ?r ?l) = ?x
''')

add_assoc_lr = rule.parse('''
  (+ ?a ?r) = ?root
  (+ ?b ?c) = ?r
''', '''
  (+ (+ ?a ?b) ?c) = ?root
''')

mul_assoc_lr = rule.parse('''
  (* ?a ?r) = ?root
  (* ?b ?c) = ?r
''', '''
  (* (* ?a ?b) ?c) = ?root
''')

add_assoc_rl = rule.parse('''
  (+ ?l ?c) = ?root
  (+ ?a ?b) = ?l
''', '''
  (+ ?a (+ ?b ?c)) = ?root
''')

mul_assoc_rl = rule.parse('''
  (* ?l ?c) = ?root
  (* ?a ?b) = ?l
''', '''
  (* ?a (+ ?b ?c)) = ?root
''')

add_zero = rule.parse('''
  0 = ?zero
  (+ ?x ?zero) = ?root
''', '''
  ?x = ?root
''')

sub_zero = rule.parse('''
  0 = ?zero
  (- ?x ?zero) = ?root
''', '''
  ?x = ?root
''')

mul_zero = rule.parse('''
  0 = ?zero
  (* ?x ?zero) = ?root
''', '''
  0 = ?root
''')

mul_one = rule.parse('''
  1 = ?one
  (* ?x ?one) = ?root
''', '''
  ?x = ?root
''')

all_rules = [
  neg_neg,
  add_neg,
  sub_self,
  add_comm,
  mul_comm,
  add_assoc_lr,
  mul_assoc_lr,
  add_assoc_rl,
  mul_assoc_rl,
  add_zero,
  mul_zero,
  mul_one
]

nice_rules = [
  neg_neg,
  add_neg,
  sub_self,
  add_comm,
  mul_comm,
  add_zero,
  mul_zero,
  mul_one
]

print("Fresh egraph:")
eg = EGraph()
print(eg)

eg.get_sexpr('0')
eg.get_sexpr('1')

e = '(* (+ x (~ x)) (+ y z))'
print(f"Adding {e}:")
id = eg.get_sexpr(e)
print(eg)
print(f"{e} ended up in eclass {id}")

print(f"Running rules and rebuilding...")
eg.run_rules(nice_rules); eg.rebuild()
eg.run_rules(all_rules); eg.rebuild()
eg.run_rules(nice_rules); eg.rebuild()
print(eg)
