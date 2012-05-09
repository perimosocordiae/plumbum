
from copy import copy as shallowcopy
from pb_pipe import *
from pb_stdlib import stdlib

def consume(ret_val):
  if hasattr(ret_val,'__iter__') and not hasattr(ret_val,'__len__'):
    for _ in ret_val: pass

class Plumbum(object):
  
  def __init__(self):
    self.pipes = dict((name,pipe()) for name, pipe in stdlib.iteritems())
    self.pipes[''] = []  # '' pipes are entrypoints, may have > 1
  
  def define(self, statement):
    name = statement['name']
    pipe = self.join_pipe(map(self.resolve,statement['pipe']))
    if not name:
      assert pipe.type.input.name == 'nil', 'Pipe needs input of type %s' % pipe.type
      self.pipes[''].append(pipe)
    else:
      assert name not in self.pipes, 'Overwrites existing pipe: %s' % name
      self.pipes[name] = pipe

  def run(self):
    for main in self.pipes['']:
      consume(main.func(None,main.args))
  
  def typeof(self, statement):
    return self.join_pipe(map(self.resolve,statement['pipe'])).type

  def resolve(self, atom):
    resolvers = {
      'function': lambda val: self._resolve_function(val['name'],val['arguments']),
      'emptylist': lambda val: Literal(val,'arb',1),
      'irange': InfiniteRange,
      'brange': BoundedRange,
      'intlist': lambda val: Literal(val,'int',1),
      'strlist': lambda val: Literal(val,'str',1),
      'rgxlist': lambda val: Literal(val,'rgx',1),
      'lstlist': self._resolve_lstlist,
    }
    atype, val = atom
    return resolvers[atype](val)

  def _resolve_lstlist(self, val):
    lits = [self.resolve(c) for c in val]
    inner_type = lits[0].type.output
    # kinda hack, evaluate each list literal inside
    vals = [lit.func(None,None) for lit in lits]
    return Literal(vals,inner_type.name,inner_type.depth+1)

  def _resolve_arg(self, arg):
    if type(arg) is not tuple: return arg
    atype, val = arg
    if atype is 'pipe':
      subpipe = self.join_pipe(map(self.resolve,val))
      assert subpipe.type.input.name == 'nil', 'Subpipe must not require input, has type %s' % subpipe.type
      return subpipe.func(None,subpipe.args)
    else:
      a = self.resolve(arg)
      if isinstance(a,Literal):
        return a.value
      return a

  def _resolve_function(self, name, args):
    assert name in self.pipes, 'No such pipe: %s' % name
    pipe = shallowcopy(self.pipes[name])
    pipe.fill_args([self._resolve_arg(a) for a in args])
    return pipe

  def join_pipe(self, pipes):
    assert len(pipes) > 0, 'No sense making a null pipe'
    assert isinstance(pipes[0],Pipe), '%s is not a Pipe object' % pipes[0]
    jp = shallowcopy(pipes[0])
    for p in pipes[1:]:
      assert isinstance(p,Pipe), '%s is not a Pipe object' % p
      jp = jp.curry(p)
    return jp