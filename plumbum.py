
from copy import copy as shallowcopy
from pb_pipe import Pipe, Literal
from pb_stdlib import stdlib

def consume(ret_val):
  if hasattr(ret_val,'__iter__') and not hasattr(ret_val,'__len__'):
    for _ in ret_val: pass

class Plumbum(object):
  
  def __init__(self):
    self.pipes = dict((name,pipe()) for name, pipe in stdlib.iteritems())
    self.pipes[''] = []  # '' pipes are entrypoints, may have > 1
  
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
    if isinstance(atom,Literal): return atom
    name, args = atom
    assert name in self.pipes, 'No such pipe: %s' % name
    pipe = shallowcopy(self.pipes[name])
    for i in xrange(len(args)):
      if type(args[i]) is tuple and args[i][0] is 'subpipe':
        subpipe = self.join_pipe(map(self.resolve,args[i][1]))
        assert subpipe.type.input.name == 'nil', 'Subpipe must not require input, has type %s' % subpipe.type
        args[i] = subpipe.func(None,subpipe.args)
    pipe.fill_args(args)
    return pipe

  def join_pipe(self, pipes):
    assert len(pipes) > 0, 'No sense making a null pipe'
    assert isinstance(pipes[0],Pipe), '%s is not a Pipe object' % pipes[0]
    jp = shallowcopy(pipes[0])
    for p in pipes[1:]:
      assert isinstance(p,Pipe), '%s is not a Pipe object' % p
      jp = jp.curry(p)
    return jp