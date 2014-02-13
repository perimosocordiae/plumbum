import inspect
builtins = {}

class Func(object):
  def __str__(self):
    return self.__repr__()
  def __repr__(self):
    return '<%s: %s>' % (self.__class__.__name__, self.name)

class Builtin(Func):
  def __init__(self, arity=None, name=None):
    assert arity is None or type(arity) is int, 'Invalid arity: '+arity
    assert name is None or type(name) is str, 'Invalid name: '+name
    self.arity = arity
    self.name = name
    self.func = None
  def one_time_setup(self, func):
    self.func = func
    if self.arity is None:
      self.arity = len(inspect.getargspec(self.func)[0])
    if self.name is None:
      self.name = self.func.func_name
    global builtins
    builtins[self.name] = self
  def __call__(self, stack_or_func):
    if self.func is None:
      self.one_time_setup(stack_or_func)
      return self
    if self.arity > len(stack_or_func):
      raise Exception('stack underflow when calling %s' % self)
    args = stack_or_func[-self.arity:]
    stack = stack_or_func[:-self.arity]
    out = self.func(*args)
    if out is not None:
      stack.append(out)
    return stack


class Pipe(Func):
  def __init__(self, name, parts):
    self.name = name
    self.parts = parts
  def __call__(self, stack):
    for p in self.parts:
      if isinstance(p, Func):
        stack = p(stack)
      else:
        stack.append(p)
    return stack

