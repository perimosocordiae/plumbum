
class UnitType(object):
  def __init__(self, type_name, depth=0):
    self.name = type_name
    self.depth = depth
  def __repr__(self):
    return '['*self.depth + self.name + ']'*self.depth
  def deepen(self, dd):
    return UnitType(self.name,self.depth+dd)
  def matches(self, other):
    if self.depth != other.depth: return False
    return self.name == other.name or type(other) is ArbType

#TODO: really handle arbtypes appropriately. Current depth hack is not great.
class ArbType(UnitType):
  def __init__(self, depth=0):
    UnitType.__init__(self,hash(self),depth)
  def __repr__(self):
    return "%s<arb %s>%s" % ('['*self.depth, self.name, ']'*self.depth)
  def deepen(self, dd):
    a = ArbType(self.depth+dd)
    a.name = self.name
    return a
  def matches(self, other):
    return self.depth == other.depth

class FuncType(object):
  def __init__(self, _input, output):
    self.input = _input
    self.output = output
  def __eq__(self, other):
    return (self.input  == other.input and 
            self.output == other.output) 
  def __repr__(self):
    return "(%r -> %r)" % (self.input, self.output)
  def deepen(self, dd):
    return FuncType(self.input,self.output.deepen(dd))
  def is_vartyped(self):
    return type(self.input) is ArbType and type(self.output) is ArbType and self.input.name==self.output.name
  def convert_base(self, base_type):
    assert self.is_vartyped(), 'Can only convert base for vartyped funcs'
    self.input.name = base_type.name
    self.output.name = base_type.name
  def join_types(self,other):
    if other.input.name == 'nil':
      raise TypeError('Cannot pass %r to nil input'%self.output)
    if not self.output.matches(other.input):
      raise TypeError('type mismatch: %r <> %r' % (self.output,other.input))
    if other.is_vartyped():
      # preserve types, but pass along the depth change
      new_out = self.output.deepen(other.output.depth - other.input.depth)
    else:
      new_out = other.output
    ctype = FuncType(self.input, new_out)
    return ctype
