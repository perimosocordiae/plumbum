import sys
from pblib import Builtin


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

