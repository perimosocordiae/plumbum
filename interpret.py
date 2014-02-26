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
      pipe_start = reorder_pipe(prog, pipe_start)
    elif c in '1234567890-\'"':
      prog.append(ast.literal_eval(token))
    elif token == '=':
      assert len(prog) == 1, 'Assigning to >1 name'
      assert type(prog[0]) is pblib.Ident, 'Assigning to non-identifier'
      assign = prog.pop().name
    elif c == '<':
      prog.append(pblib.Ident('slurp'))
      prog.append(token[1:-1])
    elif c == '`':
      prog.append(pblib.Ident('shell'))
      prog.append(token[1:-1])
    elif c == '/':
      prog.append(token)
      prog.append(pblib.Ident('regex'))
    elif c == '[':
      prog.append(parse_list(token))
    elif c == '@':
      prog.append(pblib.QuotedIdent(token[1:]))
    else:
      # Must be a bareword. Assume it's an identifier.
      prog.append(pblib.Ident(token))
  # move the first expr in the last pipe to the end
  reorder_pipe(prog, pipe_start)
  # handle assignment, or assign to the 'main' special name
  if assign is not None:
    state[assign] = pblib.Pipe(assign, prog)
  else:
    return pblib.Pipe('main', prog)


def parse_list(list_str):
  # TODO: support .. ranges, regex literals in lists
  return ast.literal_eval(list_str)


def reorder_pipe(prog, pipe_start):
  if pipe_start < len(prog) - 1:
    assert type(prog[pipe_start]) is pblib.Ident, 'Pipe must start with an identifier'
    prog.append(prog.pop(pipe_start))
  return len(prog)


def listify(x):
  '''Turn all nested generators and such into lists of concrete values'''
  if hasattr(x,'__iter__'):
    return map(listify,x)
  return x
