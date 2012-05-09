import re

class UnitType(object):
  def __init__(self, type_name, depth=0):
    self.name = type_name
    self.depth = depth
  def __repr__(self):
    return '['*self.depth + self.name + ']'*self.depth
  def deepen(self, dd):
    return UnitType(self.name,self.depth+dd)
  def depth_difference(self, other):
    d = self.depth - other.depth
    if type(other) is ArbType and other.depth > 0:
      return min(d,0)  # arbtype(1+) can represent unit(1+)
    return d

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
  def depth_difference(self, other):
    d = self.depth - other.depth
    if self.depth > 0 and type(other) is UnitType:
      return max(d,0)  # see note for UnitType.depth_difference
    return d

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
  def join_types(self,other):
    if other.input.name == 'nil':
      raise TypeError('Cannot pass %r to nil input'%self.output)
    if self.output.name != other.input.name and not ((type(self.output) is ArbType) or (type(other.input) is ArbType)):
      raise TypeError('type mismatch: %r <> %r' % (self.output,other.input))
    if type(other.input) is ArbType and type(other.output) is ArbType and other.input.name==other.output.name:
      dd = other.output.depth - other.input.depth
      new_out = self.output.deepen(dd)
    else:
      dd = None
      new_out = other.output
    new_in = self.input
    ddepth = self.output.depth_difference(other.input)
    if ddepth > 0:
      new_out = new_out.deepen(ddepth)
      if dd is not None:
        ddd = new_out.depth_difference(new_in)
        if ddd != dd:
          new_in = new_in.deepen(ddd-dd)
    elif ddepth < 0:
      assert new_in.name is not 'nil', "Cannot auto-deepen a concrete input"
      new_in = new_in.deepen(-ddepth)
      if dd is not None:
        ddd = new_out.depth_difference(new_in)
        if ddd != dd:
          print "TODO: fix deepening bugs"
          # print dd,ddd,dd-ddd
          #new_out.deepen(dd-ddd)
    ctype = FuncType(new_in, new_out)
    return ctype
