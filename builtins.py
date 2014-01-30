import sys
from itertools import cycle, repeat
from pblib import Builtin


@Builtin()
def cat(pipe):
  return ''.join(str(p) for p in pipe)


Builtin(name='repeat',arity=1)(repeat)
Builtin(name='uniq',arity=1)(set)

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
  print 'got regex', literal


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

