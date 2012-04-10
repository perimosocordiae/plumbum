
from pb_type import *

def auto_map(func, args, iterable, depth):
  if depth == 1:
    return (func(x,args) for x in iterable)
  return (auto_map(func,args,x,depth-1) for x in iterable)

class Pipe(object):

  def __init__(self, func, _type, args):
    assert hasattr(func,'__call__'), '%s is not a callable function' % func
    assert isinstance(_type,FuncType), '%s is not a FuncType object' % _type
    self.func = func
    self.type = _type
    self.args = args
  
  def clone(self):
    return Pipe(self.func, self.type, list(self.args))

  def curry(self, other):
    ctype = self.type.join_types(other.type)
    ddepth = self.type.output.depth_difference(other.type.input)
    if ddepth == 0:
      cfunc = lambda inpipe,args: other.func(self.func(inpipe,self.args),args)
    elif ddepth < 0:
      cfunc = lambda inpipe,args: other.func(auto_map(self.func,self.args,inpipe,-ddepth),args)
    else:
      cfunc = lambda inpipe,args: auto_map(other.func,args,self.func(inpipe,self.args),ddepth)
    return Pipe(cfunc, ctype, other.args)
  
  def __repr__(self):
    return "[%s: %s +%s]" % (self.func.func_name, self.type, self.args)

class Literal(Pipe):
  def __init__(self, lst, element_type, depth):
    self.func = lambda _,args: lst
    ret = ArbType(depth) if element_type is 'arb' else UnitType(element_type,depth)
    self.type = FuncType(UnitType('nil'),ret)
    self.args = []

  def __repr__(self):
    return "<literal: %s>" % self.type