import sys, re, signal
from subprocess import check_output, Popen, PIPE
from select import select
from itertools import izip, chain
from collections import deque
from urllib2 import urlopen
from pb_type import UnitType, ArbType, FuncType
from pb_pipe import Pipe

# suppress 'broken pipe' error messages
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

nil0 = UnitType('nil')
int0 = UnitType('int')
int1 = UnitType('int',1)
str0 = UnitType('str')
str1 = UnitType('str',1)
rgx0 = UnitType('regex')
rgx1 = UnitType('regex',1)

#
# TODO: make the Pipe objects here directly!
#  - auto-gen pipes for nested lists, different types of lists
#    - give auto-gen'd pipes the right type sigs
#  - specify argument type constraints
#  - specify additional attributes, like infinite-size, lazyness, purity etc
#
# TODO: builtins to add
#  - 'group', for group-by semantics
#  - 'drop' (like reverse head)
#  - math operations?

class Slurp(Pipe):
  name = 'slurp'
  def __init__(self):
    Pipe.__init__(self, nil0, str1, num_required_args=1, default_args=[''])
  def func(self, _, args):
    try:
      fh = sys.stdin if args[0] == '' else open(args[0])
    except IOError as e:
      if e.errno == 2:  # no such file
        fh = urlopen(args[0])
      else:
        raise e
    for line in fh:
      yield line

class Shell(Pipe):
  name = 'shell'
  def __init__(self):
    #TODO: allow input, i.e.: [3,5,4] | `sort -n` | int ==> [3,4,5]
    Pipe.__init__(self, nil0, str1, num_required_args=1)
  def func(self,_,args):
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

class Grep(Pipe):
  name = 'grep'
  def __init__(self):
    Pipe.__init__(self, str1, num_required_args=1)
  def func(self, inpipe, args):
    patt = args[0]
    for s in inpipe:
      if re.search(patt, s):
        yield s

class Head(Pipe):
  name = 'head'
  def __init__(self):
    Pipe.__init__(self, ArbType(1), num_required_args=1, default_args=[10])
  def func(self,inpipe,args):
    it = iter(inpipe)
    for _ in xrange(args[0]):
      try:
        yield next(it)
      except StopIteration:
        break

class Tail(Pipe):
  name = 'tail'
  def __init__(self):
    Pipe.__init__(self, ArbType(1), num_required_args=1, default_args=[10])
  def func(self,inpipe,args):
    return deque(inpipe,maxlen=args[0])

class Sort(Pipe):
  name = 'sort'
  def __init__(self):
    Pipe.__init__(self, ArbType(1))
  def func(self,inpipe,_):
    return sorted(inpipe)

class Uniq(Pipe):
  name = 'uniq'
  def __init__(self):
    Pipe.__init__(self, ArbType(1))
  def func(self,inpipe,_):
    last = None
    for x in inpipe:
      if x != last:
        yield x
        last = x

class Count(Pipe):
  name = 'count'
  def __init__(self):
    Pipe.__init__(self, ArbType(1), int0)
  def func(self,inpipe,_):
    return sum(1 for _ in inpipe)

class Print(Pipe):
  name = 'print'
  def __init__(self):
    Pipe.__init__(self, ArbType(0), nil0, 1, ['\n'])
  def func(self,x,args):
    if self.type.input.depth > 0:
      sys.stdout.write(str(list(x)))
    else:
      sys.stdout.write(str(x))
    # TODO: fix stupid \\n and \\t issue
    sys.stdout.write(args[0])

class Strip(Pipe):
  name = 'strip'
  def __init__(self):
    Pipe.__init__(self, str0, num_required_args=1, default_args=[None])
  def func(self,s,args):
    return s.strip(args[0])

class Split(Pipe):
  name = 'split'
  def __init__(self):
    Pipe.__init__(self, str0, str1, 1, [None])
  def func(self,s,args):
    sep = args[0]
    if not sep or type(sep) is str:
      if sep is '': return list(s)  # can't split on an empty string
      return s.split(sep)
    return sep.split(s)  # regex split

class Int(Pipe):
  name = 'int'
  def __init__(self):
    Pipe.__init__(self, ArbType(0), int0)
  def func(self,x,_):
    return int(x)

class String(Pipe):
  name = 'string'
  def __init__(self):
    Pipe.__init__(self, ArbType(0), str0)
  def func(self,x,_):
    return str(x)

class Ord(Pipe):
  name = 'ord'
  def __init__(self):
    Pipe.__init__(self, str0, int0)
  def func(self,x,_):
    return ord(x)

class Chr(Pipe):
  name = 'chr'
  def __init__(self):
    Pipe.__init__(self, int0, str0)
  def func(self,x,_):
    return chr(x)

class Sum(Pipe):
  name = 'sum'
  def __init__(self):
    Pipe.__init__(self, int1, int0)
  def func(self,inpipe,_):
    return sum(inpipe)

class Zip(Pipe):
  name = 'zip'
  def __init__(self):
    a = ArbType(1)
    Pipe.__init__(self, a, a.deepen(1), 1)
  def func(self, inpipe, args):
    tozip = args[0]
    if isinstance(tozip,Pipe):
      assert tozip.type.input.name == 'nil', 'Subpipe must not require input, has type %s' % tozip.type
      return izip(inpipe, tozip.func(None,tozip.args))
    else:
      return izip(inpipe,tozip)

class Concat(Pipe):
  name = 'concat'
  def __init__(self):
    Pipe.__init__(self, ArbType(1))
  def func(self, inpipe, args):
    return chain(inpipe,args[0])

class Flatten(Pipe):
  name = 'flatten'
  def __init__(self):
    a = ArbType(2)
    Pipe.__init__(self, a, a.deepen(-1))
  def func(self, inpipe, _):
    return chain.from_iterable(inpipe)

class Compact(Pipe):
  name = 'compact'
  def __init__(self):
    Pipe.__init__(self, ArbType(1))
  def func(self, inpipe, _):
    return (x for x in inpipe if x)

class Join(Pipe):
  name = 'join'
  def __init__(self):
    Pipe.__init__(self, str1, str0, 1, [''])
  def func(self, inpipe, _):
    return args[0].join(inpipe)

stdlib = [Slurp,Shell,Grep,Head,Tail,Sort,Uniq,Count,Print,Strip,Split,
          Int,String,Ord,Chr,Sum,Zip,Concat,Flatten,Compact]
stdlib = dict((pipe.name,pipe) for pipe in stdlib)
