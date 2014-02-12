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
      prog.append(token)
      prog.append(state['regex'])
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
        raise Exception('Undefined identifier: %r' % token)
  return pblib.Pipe('main', prog)


def listify(x):
  '''Turn all nested generators and such into lists of concrete values'''
  if hasattr(x,'__iter__'):
    return map(listify,x)
  return x


def evaluate(tokens, state, repl_mode=False):
  leftovers = None
  try:
    program = parse(tokens, state)
    leftovers = program([])
  except Exception as e:
    print >>sys.stderr, e
  if leftovers:
    if repl_mode:
      print 'out:', ', '.join(str(listify(l)) for l in leftovers)
    else:
      print >>sys.stderr, "Warning: final stack had length %d" % len(leftovers)


def tokenize(code):
  token = ''
  token_type = None  # one of ('str','list','regex','ident')
  escape = False
  comment = False
  match_depth = 0
  flip = lambda c: c if c != '<' else '>'
  WHITESPACE = ' \t\n\r'
  for char in code:
    if comment:
      if char == '\n':
        comment = False
      continue
    if char == '#':
      comment = True
      continue
    token += char
    if token_type is None:
      if char in WHITESPACE:
        token = token[:-1]
      elif char in '"\'`<':
        token_type = 'str'
      elif char in '[':
        token_type = 'list'
        match_depth = 1
      elif char == '/':
        token_type = 'regex'
      else:
        token_type = 'ident'
    elif char == '\\' and not escape:
      escape = True
    elif escape:
      escape = False
    elif token_type == 'str' and char == flip(token[0]):
      yield token
      token = ''
      token_type = None
    elif token_type == 'list' and char in "[]":
      if char == '[':
        match_depth += 1
      else:
        match_depth -= 1
        if match_depth == 0:
          yield token
          token_type = None
    elif token_type == 'regex' and char == '/':
      token_type = 'ident'  # hack
    elif token_type == 'ident' and char in WHITESPACE:
      yield token[:-1]
      token = ''
      token_type = None

