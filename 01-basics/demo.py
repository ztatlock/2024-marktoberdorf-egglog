from egraph import *

print("Fresh egraph:")
eg = EGraph()
print(eg)

print("Adding (+ 0 (+ 1 2)):")
eg.get_sexpr("(+ 0 (+ 1 2))")
print(eg)

print("Running rule (+ a (+ b c)) -> (+ (+ a b) c):")
eg.run_srule('''
  (+ ?a ?r) = ?root
  (+ ?b ?c) = ?r
''', '''
  ?root = (+ (+ ?a ?b) ?c)
''')
print(eg)

print("Rebuilding:")
eg.rebuild()
print(eg)
