import re
import string
import sys
from collections import deque
from itertools import cycle, repeat, chain
from select import select
from subprocess import Popen, PIPE
from urllib2 import urlopen

from pblib import Builtin


def mapped_func(name, func):
  '''Makes a builtin from a python function by mapping it.'''
  return Builtin(name=name, arity=1)(lambda pipe: (func(p) for p in pipe))


@Builtin()
def cat(pipe):
  return ''.join(str(p) for p in pipe)


@Builtin()
def grep(pipe, regex):
  assert hasattr(regex, 'search'), 'Invalid arg: regex required'
  for p in pipe:
    if regex.search(p):
      yield p


@Builtin()
def compact(pipe):
  for p in pipe:
    if p:
      yield p


@Builtin()
def count(pipe):
  if hasattr(pipe, '__len__'):
    return len(pipe)
  return sum(1 for _ in pipe)


mapped_func('strip', string.strip)
mapped_func('chr', chr)
mapped_func('ord', ord)
mapped_func('string', str)
mapped_func('int', int)

Builtin(name='flatten',arity=1)(chain.from_iterable)
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
  if path == '':
    return sys.stdin
  try:
    return open(path)
  except IOError as e:
    if e.errno == 2:  # no such file, try opening as a URL
      return urlopen(path)
    raise e


@Builtin()
def shell(cmd):
  proc = Popen(cmd, shell=True, stdout=PIPE)
  line = ''
  while True:
   data = select([proc.stdout],[],[])[0][0]
   c = data.read(1).decode('utf-8')
   if not c:
     return
   line += c
   if c == '\n':
     yield line
     line = ''


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


@Builtin()
def tail(pipe, n):
  return deque(pipe, maxlen=n)

