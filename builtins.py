import re
import string
import sys
from collections import deque
from itertools import cycle, repeat, chain, count, izip
from subprocess import Popen, PIPE
from urllib2 import urlopen

from pblib import Builtin

RE_FLAGS = {'i': re.I, 'l': re.L, 'm': re.M, 's': re.S, 'u': re.U, 'x': re.X}


def mapped_func(name, func):
  '''Makes a builtin from a python function by mapping it.'''
  return Builtin(name=name, arity=1)(lambda pipe: (func(p) for p in pipe))


@Builtin()
def cat(pipe):
  return ''.join(str(p) for p in pipe)


@Builtin(name='map')
def _map(pipe, quoted):
  for p in pipe:
    for x in quoted.func.run([p], {}):
      yield x
      break


@Builtin()
def split(pipe, sep):
  # empty sep splits characters
  if not sep:
    for p in pipe:
      yield list(p)
  elif hasattr(sep, 'search'):  # regex sep
    for p in pipe:
      yield sep.split(p)
  else: # string sep
    for p in pipe:
      yield p.split(sep)


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


@Builtin(name='count')
def _count(pipe):
  if hasattr(pipe, '__len__'):
    return len(pipe)
  return sum(1 for _ in pipe)


@Builtin()
def luniq(pipe):
  last = Ellipsis  # won't match anything in a pipe
  for p in pipe:
    if p != last:
      yield p
      last = p


mapped_func('strip', string.strip)
mapped_func('chr', chr)
mapped_func('ord', ord)
mapped_func('string', str)
mapped_func('int', int)

Builtin(name='flatten',arity=1)(chain.from_iterable)
Builtin(name='repeat',arity=1)(repeat)
Builtin(name='uniq',arity=1)(set)
Builtin(name='sort',arity=1)(sorted)
Builtin(name='sum',arity=1)(sum)
Builtin(name='zip',arity=2)(izip)


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
  proc = Popen(cmd, shell=True, stdout=PIPE, bufsize=1)
  for line in iter(proc.stdout.readline, ''):
    yield line
  proc.stdout.close()
  proc.wait()


@Builtin()
def regex(literal):
  end_idx = literal.rfind('/')
  flags = literal[end_idx+1:]
  opts = [RE_FLAGS[f] for f in flags if f != 'g']
  assert 'g' not in flags, 'TODO: implement //g regexen.'
  return re.compile(literal[1:end_idx], *opts)



@Builtin(name='range')
def _range(literal):
  inner = literal
  lhs,rhs = inner.split('..', 1)
  if not lhs:
    start, step = 0,1
  else:
    ss = map(int, lhs.split(','))
    start = int(ss.pop(0))
    step = 1 if not ss else int(ss.pop(0)) - start
    assert not ss, 'Extra values before .. not allowed'
  if not rhs:
    return count(start, step)
  stop = int(rhs)
  return xrange(start, stop, step)


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

