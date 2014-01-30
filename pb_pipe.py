
from types import MethodType
from itertools import count
from pb_type import *

class Pipe(object):
  def __init__(self, intype, outtype=None, num_required_args=0, default_args=None):
    # self.func, self.name are defined in subclasses
    if outtype is None:
      outtype = intype
    self.type = FuncType(intype, outtype)
    self.num_required_args = num_required_args
    self.args = default_args if default_args else []
    self.derived_type_arg_index = None

  def func(self,inpipe,args):
    raise AssertionError('Called the func of a raw Pipe object')

  def curry(self, other):
    ctype = self.type.join_types(other.type)
    new_pipe = Pipe(ctype.input, ctype.output, 0, other.args)
    cfunc = lambda cls,inpipe,args: other.func(self.func(inpipe,self.args),args)
    new_pipe.func = MethodType(cfunc, new_pipe)  # patch the default Pipe.func method
    return new_pipe

  def fill_args(self, args):
    for i,v in enumerate(args):
      assert i < self.num_required_args, 'Too many arguments to %s: arg %d (%s)' % (self.name,i,v)
      if i < len(self.args):
        self.args[i] = v
      else:
        self.args.append(v)
    assert len(self.args) >= self.num_required_args, 'Missing required argument for %s' % self.name
    if self.derived_type_arg_index is not None:
      print repr(self)
      self.type.convert_base(self.args[self.derived_type_arg_index].type.output)
      print repr(self)

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
    args = [a[1] for a in args]
    step = 1 if len(args) == 1 else args[1] - args[0]
    Literal.__init__(self, count(args[0],step), 'int', 1)

class BoundedRange(Literal):
  def __init__(self,args):
    args = [a[1] for a in args]
    step = 1 if len(args) == 2 else args[1] - args[0]
    Literal.__init__(self, xrange(args[0],args[-1],step), 'int', 1)