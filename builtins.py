import re
import sys
from itertools import cycle, repeat
from pblib import Builtin


@Builtin()
def cat(pipe):
  return ''.join(str(p) for p in pipe)


@Builtin()
def grep(pipe, regex):
  for p in pipe:
    if regex.search(p):
      yield p


Builtin(name='repeat',arity=1)(repeat)
Builtin(name='uniq',arity=1)(set)
Builtin(name='sort',arity=1)(sorted)

@Builtin()
def interleave(p1, p2):
  nexts = (iter(p1).next, iter(p2).next)
  for n in cycle(nexts):
    yield n()


@Builtin()
def slurp(path):
  return open(path)


@Builtin()
def shell(cmd):
  print 'got shell', cmd


@Builtin()
def regex(literal):
  # TODO: actually parse the regex
  assert literal[0] == '/' and literal[-1] == '/', 'TODO: parse literal'
  return re.compile(literal[1:-1])


@Builtin(name='print')
def _print(pipe):
  for line in pipe:
    sys.stdout.write(str(line))

@Builtin()
def head(pipe, n):
  for i,line in enumerate(pipe):
    if i >= n:
      break
    yield line

