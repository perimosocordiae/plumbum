import inspect
builtins = {}


class Func(object):
  '''Base class for callable functions.
  Subclasses must provide .run() and the .name attribute'''

  def run(self, stack, state):
    raise NotImplementedError('Subclasses must override this method')

  def __str__(self):
    return self.__repr__()

  def __repr__(self):
    return '<%s: %s>' % (self.__class__.__name__, self.name)


class Builtin(Func):
  '''Plumbum function supported by native code.
  This class serves a dual purpose as a decorator (see builtins.py)'''

  def __init__(self, arity=None, name=None):
    assert arity is None or type(arity) is int, 'Invalid arity: '+arity
    assert name is None or type(name) is str, 'Invalid name: '+name
    self.arity = arity
    self.name = name
    self.func = None

  def __call__(self, func):
    self.func = func
    if self.arity is None:
      self.arity = len(inspect.getargspec(self.func)[0])
    if self.name is None:
      self.name = self.func.func_name
    global builtins
    builtins[self.name] = self

  def run(self, stack, unused_state):
    if self.arity > len(stack):
      raise Exception('stack underflow when calling %s' % self)
    args = stack[-self.arity:]
    stack = stack[:-self.arity]
    out = self.func(*args)
    if out is not None:
      stack.append(out)
    return stack


class Pipe(Func):
  '''User-created function (composed of Builtins and literals).'''

  def __init__(self, name, parts):
    self.name = name
    self.parts = parts

  def run(self, stack, state):
    for p in self.parts:
      if type(p) is str and p in state:
        p = state[p]
      if hasattr(p, 'run'):
        stack = p.run(stack, state)
      else:
        stack.append(p)
    return stack
