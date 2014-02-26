import inspect
builtins = {}


class Ident(object):
  '''Simple wrapper for a string that corresponds
     to a named entity (Func or Pipe).'''
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return self.__repr__()

  def __repr__(self):
    return '<ident: %s>' % self.name


class QuotedIdent(Ident):
  '''Represents a quoted identifier.'''
  def __init__(self, name):
    Ident.__init__(self, name)
    self.func = None

  def __repr__(self):
    return '<quote: %s>' % self.name


class SyntaxIdent(Ident):
  '''Used only for syntax-produced builtins.'''
  def __init__(self, literal, name):
    Ident.__init__(self, name)
    self.literal = literal

  def __repr__(self):
    return '<%s: %s>' % (self.name, self.literal)


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
      if isinstance(p, Ident):
        assert p.name in state, 'Undefined identifier: %s' % p.name
        if type(p) is QuotedIdent:
          p.func = state[p.name]
        else:
          if type(p) is SyntaxIdent:
            stack.append(p.literal)
          p = state[p.name]
      if hasattr(p, 'run'):
        stack = p.run(stack, state)
      else:
        stack.append(p)
    return stack
