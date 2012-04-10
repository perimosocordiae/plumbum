
from pb_pipe import Pipe
from pb_stdlib import stdlib

_required_arg = object()  # just a placeholder

def consume(ret_val):
  if hasattr(ret_val,'__iter__') and not hasattr(ret_val,'__len__'):
    for _ in ret_val: pass

class Plumbum(object):
  
  def __init__(self):
    self.pipes = {'':[]}  # '' pipes are entrypoints, may have > 1
    for name, ftype, func, n_args, default_args in stdlib:
      # args list, filling in any defaults
      args = default_args + [_required_arg]*(n_args-len(default_args))
      self.pipes[name] = Pipe(func,ftype,args)
  
  def define(self, name, raw_pipe):
    pipe = self.join_pipe(map(self.resolve,raw_pipe))
    if not name:
      assert pipe.type.input.name == 'nil', 'Pipe needs input of type %s' % pipe.type
      self.pipes[''].append(pipe)
    else:
      assert name not in self.pipes, 'Overwrites existing pipe: %s' % name
      self.pipes[name] = pipe

  def run(self):
    for main in self.pipes['']:
      consume(main.func(None,main.args))
  
  def typeof(self, raw_pipe):
    return self.join_pipe(map(self.resolve,raw_pipe)).type

  def resolve(self, atom):
    if isinstance(atom,Pipe): return atom
    name, args = atom
    assert name in self.pipes, 'No such pipe: %s' % name
    pipe = self.pipes[name].clone()
    for i,v in enumerate(args):
      #TODO: type check here (pipe.args[i] should be a type/primitive)
      if type(v) is tuple and v[0] is 'subpipe':
        subpipe = self.join_pipe(map(self.resolve,v[1]))
        #TODO: assert that the input to subpipe is nil
        v = subpipe.func(None,subpipe.args)
        # we now know what the real type is
        pipe.type.input = subpipe.type.output  # zip input must match subpipe output
        pipe.type.output = subpipe.type.output.deepen(1)
      assert i < len(pipe.args), 'Too many arguments to %s: arg %d (%s)' % (name,i,v)
      pipe.args[i] = v
    # check to make sure all required args are filled
    assert all(a != _required_arg for a in pipe.args), 'Missing required argument for %s' % name
    return pipe

  def join_pipe(self, pipes):
    assert len(pipes) > 0, 'No sense making a null pipe'
    assert isinstance(pipes[0],Pipe), '%s is not a Pipe object' % pipes[0]
    jp = pipes[0].clone()
    for p in pipes[1:]:
      assert isinstance(p,Pipe), '%s is not a Pipe object' % p
      jp = jp.curry(p)
    return jp