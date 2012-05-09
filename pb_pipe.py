
from types import MethodType
from itertools import count
from pb_type import *

def auto_map(func, args, iterable, depth):
  if depth == 1:
    return (func(x,args) for x in iterable)
  return (auto_map(func,args,x,depth-1) for x in iterable)

class Pipe(object):
  def __init__(self, intype, outtype=None, num_required_args=0, default_args=None):
    # self.func, self.name are defined in subclasses
    if outtype is None:
      outtype = intype
    self.type = FuncType(intype, outtype)
    self.num_required_args = num_required_args
    self.args = default_args if default_args else []

  def func(self,inpipe,args):
    raise AssertionError('Called the func of a raw Pipe object')

  def curry(self, other):
    ctype = self.type.join_types(other.type)
    ddepth = self.type.output.depth_difference(other.type.input)
    new_pipe = Pipe(ctype.input, ctype.output, 0, other.args)
    if ddepth == 0:
      cfunc = lambda cls,inpipe,args: other.func(self.func(inpipe,self.args),args)
    elif ddepth < 0:
      cfunc = lambda cls,inpipe,args: other.func(auto_map(self.func,self.args,inpipe,-ddepth),args)
    else:
      cfunc = lambda cls,inpipe,args: auto_map(other.func,args,self.func(inpipe,self.args),ddepth)
    new_pipe.func = MethodType(cfunc, new_pipe)  # patch the default Pipe.func method
    return new_pipe

  def fill_args(self, args):
    assert (len(args) >= self.num_required_args) or (len(self.args) >= self.num_required_args), 'Missing required argument for %s' % self.name
    for i,v in enumerate(args):
      assert i < self.num_required_args, 'Too many arguments to %s: arg %d (%s)' % (self.name,i,v)
      if i < len(self.args):
        self.args[i] = v
      else:
        self.args.append(v)
  
  def __repr__(self):
    return "[%s: %s +%s]" % (self.name, self.type, self.args)

class Literal(Pipe):
  def __init__(self, lst, element_type, depth):
    self.value = lst
    ret = ArbType(depth) if element_type is 'arb' else UnitType(element_type,depth)
    self.type = FuncType(UnitType('nil'),ret)
    self.args = []

  def func(self,_,args):
    return self.value

  def __repr__(self):
    return "<literal: %s>" % self.type

class InfiniteRange(Literal):
  def __init__(self,args):
    step = 1 if len(args) == 1 else args[1] - args[0]
    Literal.__init__(self, count(args[0],step), 'int', 1)

class BoundedRange(Literal):
  def __init__(self,args):
    step = 1 if len(args) == 2 else args[1] - args[0]
    Literal.__init__(self, xrange(args[0],args[-1],step), 'int', 1)