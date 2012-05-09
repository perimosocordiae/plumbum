
from copy import copy as shallowcopy
import re
from lxml.objectify import ObjectifiedElement
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
    name = str(statement.name.text) if statement.find('name') else ''
    pipe = self.join_pipe(map(self.resolve,statement.pipe.iterchildren()))
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
    return self.join_pipe(map(self.resolve,statement.pipe.iterchildren())).type

  def resolve(self, atom):
    resolvers = {
      'function': lambda atom: self._resolve_function(atom.name.text,atom.find('arguments')),
      'slurp': lambda atom: self._resolve_function('slurp',(atom.text,)),
      'shell': lambda atom: self._resolve_function('shell',(atom.text,)),
      'emptylist': lambda atom: Literal([],'arb',1),
      'irange': lambda atom: InfiniteRange([int(c.text) for c in atom.iterchildren()]),
      'brange': lambda atom: BoundedRange([int(c.text) for c in atom.iterchildren()]),
      'intlist': lambda atom: Literal([int(c.text) for c in atom.iterchildren()],'int',1),
      'strlist': lambda atom: Literal([(c.text or '') for c in atom.iterchildren()],'str',1),
      'rgxlist': lambda atom: Literal([re.compile(c.text) for c in atom.iterchildren()],'rgx',1),
      'lstlist': self._resolve_lstlist,
      'ITEM': lambda atom: self._resolve_function('slurp',('',)),  # mega hax
    }
    return resolvers[atom.tag](atom)

  def _resolve_lstlist(self,atom):
    lits = [self.resolve(c) for c in atom.iterchildren()]
    inner_type = lits[0].type.output
    return Literal([lit.func(None,None) for lit in lits],inner_type.name,inner_type.depth+1)

  def _resolve_arg(self, arg):
    if arg.tag == 'pipe':
      subpipe = self.join_pipe(map(self.resolve,arg.iterchildren()))
      assert subpipe.type.input.name == 'nil', 'Subpipe must not require input, has type %s' % subpipe.type
      return subpipe.func(None,subpipe.args)
    elif arg.tag == 'integer':
      return int(arg.text)
    elif arg.tag == 'string':
      return arg.text or ''
    elif arg.tag == 'regex':
      return re.compile(arg.text)
    elif arg.tag == 'ITEM':
      return re.compile('')  # another big hack, will go away when XML is cut out
    else:
      a = self.resolve(arg)
      if isinstance(a,Literal):
        return a.value
      return a

  def _resolve_function(self, name, args):
    assert name in self.pipes, 'No such pipe: %s' % name
    pipe = shallowcopy(self.pipes[name])
    if args is None:
      args = []
    elif type(args) is ObjectifiedElement:
      args = [self._resolve_arg(a) for a in args.iterchildren()]
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