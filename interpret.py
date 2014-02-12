import ast
import sys

import pblib


def parse(tokens, state):
  # The best/worst kind of parser: hand-rolled!
  prog = []
  assign = False
  for token in tokens:
    c = token[0]
    if c == '#':
      break
    elif c in '1234567890-\'"':
      prog.append(ast.literal_eval(token))
    elif token == '=':
      assign = True
    elif c == '<':
      prog.append(token[1:-1])
      prog.append(state['slurp'])
    elif c == '`':
      prog.append(token[1:-1])
      prog.append(state['shell'])
    elif c == '/':
      prog.append(token)  # TODO: parse it a bit
      prog.append(['regex'])
    elif c == '[':
      # TODO: support .. ranges, regex literals in lists
      prog.append(ast.literal_eval(token))
    else:
      exists = token in state
      if assign:
        state[token] = pblib.Pipe(token, prog)
        prog = []
        assign = False
        if exists:
          print >>sys.stderr, 'Warning: overwriting definition of', token
      elif exists:
        prog.append(state[token])
      else:
        raise Exception('Undefined identifier: %s' % token)
  return pblib.Pipe('main', prog)


def evaluate(tokens, state, repl_mode=False):
  try:
    program = parse(tokens, state)
    leftovers = program([])
  except Exception as e:
    print >>sys.stderr, e
  if leftovers:
    if repl_mode:
      print 'out:', ', '.join(str(list(l)) if hasattr(l,'__iter__') else l for l in leftovers)
    else:
      print >>sys.stderr, "Warning: final stack had length %d" % len(leftovers)


def tokenize(code):
  # TODO: handle spaces in strings, list literals, regexes
  return code.split()

