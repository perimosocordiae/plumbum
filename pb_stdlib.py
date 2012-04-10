import sys, re, signal
from subprocess import check_output, Popen, PIPE
from select import select
from itertools import izip, chain
from collections import deque
from urllib2 import urlopen
from pb_type import UnitType, ArbType, FuncType

def stdlib_literal(_,args):
  return args[0]

def stdlib_slurp(_, args):
  try:
    fh = sys.stdin if args[0] == '' else open(args[0])
  except IOError as e:
    if e.errno == 2:  # no such file
      fh = urlopen(args[0])
    else:
      raise e
  for line in fh:
    yield line

def stdlib_grep(inpipe, args):
  for s in inpipe:
    if re.search(args[0], s):
      yield s

def stdlib_print(x, args):
  end = args[0]
  #TODO: fix stupid \\n and \\t issue
  if end == '\\n': end = '\n'
  elif end == '\\t': end = '\t'
  #TODO: put this into a Pipe object, so it can see its type sig
  if hasattr(x,'__iter__'):
    sys.stdout.write(str(list(x)))
  else:
    sys.stdout.write(str(x))
  sys.stdout.write(end)

def stdlib_head(inpipe,args):
  it = iter(inpipe)
  for _ in xrange(args[0]):
    try:
      yield next(it)
    except StopIteration:
      break

def stdlib_tail(inpipe,args):
  return deque(inpipe,maxlen=args[0])

def stdlib_shell_naive(_,args):
  assert args[0], 'Empty shell command is invalid'
  result = check_output(args[0],shell=True)
  for line in res.splitlines():
    yield line

# suppress 'broken pipe' error messages
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
def stdlib_shell(_,args):
  assert args[0], 'Empty shell command is invalid'
  proc = Popen(args[0],shell=True,stdout=PIPE)
  line = ''
  while True:
      data = select([proc.stdout],[],[])[0][0]
      c = data.read(1).decode('utf-8')
      if len(c) == 0: return
      elif c == "\n":
          yield line+c
          line = ''
      else: line += c

def stdlib_count(inpipe,_):
  return sum(1 for _ in inpipe)

def stdlib_strip(s,args):
  return s.strip(args[0])

def stdlib_split(s,args):
  sep = args[0]
  if not sep or type(sep) is str:
    if sep is '': return list(s)  # can't split on an empty string
    return s.split(sep)
  return sep.split(s)  # regex split

def stdlib_sort(inpipe,_):
  return sorted(inpipe)

def stdlib_uniq(inpipe,_):
  last = None
  for x in inpipe:
    if x != last:
      yield x
      last = x

def stdlib_zip(inpipe,args):
  return izip(inpipe,args[0])

def stdlib_concat(inpipe,args):
  return chain(inpipe,args[0])

def stdlib_join(inpipe,args):
  return args[0].join(inpipe)

def stdlib_flatten(inpipe,_):
  return chain.from_iterable(inpipe)

def stdlib_compact(inpipe,_):
  return (x for x in inpipe if x)

def stdlib_func(func):
  return lambda x,_: func(x)

nil0 = UnitType('nil')
int0 = UnitType('int')
int1 = UnitType('int',1)
str0 = UnitType('str')
str1 = UnitType('str',1)
rgx0 = UnitType('regex')
rgx1 = UnitType('regex',1)
a = ArbType
f = FuncType
def farb(d):
  arb = a(d)
  return f(arb,arb)

def farbd(d1,d2):
  a1 = a(d1)
  a2 = a1.deepen(d2-d1)
  return f(a1,a2)

#
# TODO: make the Pipe objects here directly!
#  - auto-gen pipes for nested lists, different types of lists
#    - give auto-gen'd pipes the right type sigs
#  - specify argument type constraints
#  - specify additional attributes, like infinite-size, lazyness, etc
#


stdlib = (
#  name      f( in ,out )  function      n_args defaults
  ('slurp',  f(nil0,str1), stdlib_slurp,     1, ['']  ),
  ('shell',  f(nil0,str1), stdlib_shell,     1, []    ),
  ('grep',   f(str1,str1), stdlib_grep,      1, []    ),
  ('head',   farb(1)     , stdlib_head,      1, [10]  ),
  ('tail',   farb(1)     , stdlib_tail,      1, [10]  ),
  ('sort',   farb(1)     , stdlib_sort,      0, []    ),
  ('uniq',   farb(1)     , stdlib_uniq,      0, []    ),
  ('count',  f(a(1),int0), stdlib_count,     0, []    ),
  ('print',  f(a(0),nil0), stdlib_print,     1, ['\n']),
  ('strip',  f(str0,str0), stdlib_strip,     1, [None]),
  ('split',  f(str0,str1), stdlib_split,     1, [None]),
  ('int',    f(a(0),int0), stdlib_func(int), 0, []    ),
  ('string', f(a(0),str0), stdlib_func(str), 0, []    ),
  ('ord',    f(str0,int0), stdlib_func(ord), 0, []    ),
  ('chr',    f(int0,str0), stdlib_func(chr), 0, []    ),
  ('sum',    f(int1,int0), stdlib_func(sum), 0, []    ),
  ('zip',    farbd(1,2),   stdlib_zip,       1, []    ),
  ('concat', farb(1),      stdlib_concat,    1, []    ),
  ('flatten',farbd(2,1),   stdlib_flatten,   0, []    ),
  ('compact',farb(1),      stdlib_compact,   0, []    ),
  ('join',   f(str1,str0), stdlib_join,      1, ['']  ),
)

