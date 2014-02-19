import ast
import sys

import pblib
from lexer import tokenize

__all__ = ['evaluate']


def evaluate(code, state, return_leftovers=False):
  '''Parses and runs a statement, modifying the program state.'''
  tokens = tokenize(code)
  program = parse(tokens, state)
  if not program:
    return
  leftovers = program.run([], state)
  if return_leftovers:
    return map(listify, leftovers)
  if leftovers:
    print >>sys.stderr, "Warning: final stack had length %d" % len(leftovers)


def parse(tokens, state):
  # The best/worst kind of parser: hand-rolled!
  prog = []
  assign = None
  pipe_start = 0
  for token in tokens:
    c = token[0]
    if c == '#':
      break
    elif c == '|':
      # move the first expr in the pipe to the end
      prog.append(prog.pop(pipe_start))
      pipe_start = len(prog)
    elif c in '1234567890-\'"':
      prog.append(ast.literal_eval(token))
    elif token == '=':
      assert len(prog) == 1, 'Assigning to >1 name'
      assign = prog.pop()
    elif c == '<':
      prog.append(state['slurp'])
      prog.append(token[1:-1])
    elif c == '`':
      prog.append(state['shell'])
      prog.append(token[1:-1])
    elif c == '/':
      prog.append(token)
      prog.append(state['regex'])
    elif c == '[':
      # TODO: support .. ranges, regex literals in lists
      prog.append(ast.literal_eval(token))
    else:
      prog.append(token)
  # move the first expr in the last pipe to the end
  if pipe_start < len(prog) - 1:
    prog.append(prog.pop(pipe_start))
  if assign is not None:
    state[assign] = pblib.Pipe(assign, prog)
  else:
    return pblib.Pipe('main', prog)


def listify(x):
  '''Turn all nested generators and such into lists of concrete values'''
  if hasattr(x,'__iter__'):
    return map(listify,x)
  return x
