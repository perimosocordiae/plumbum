import re,shlex
from itertools import chain, count
from pyparsing import *
from pb_pipe import Literal

def __setup_parser():
  def parser(p,func):
    p.setParseAction(lambda t: func(t[0]))
    return p

  def lit(typestr):
    return lambda x: Literal(x.asList(),typestr,1)

  def brange(x):
    nums = x.asList()
    assert 2 <= len(nums) <= 3, 'Wrong number of numbers for a brange: %d'%nums
    step = 1 if len(nums) == 2 else nums[1] - nums[0]
    return Literal(xrange(nums[0],nums[-1],step),'int',1)

  def irange(x):
    nums = x.asList()
    assert 1 <= len(nums) <= 2, 'Wrong number of numbers for an irange: %d'%nums
    if len(nums) == 1:
      step = 1
    else:
      step = nums[1] - nums[0]
    return Literal(count(nums[0],step),'int',1)

  def list_of_lists(x):
    inner_type = x.asList()[0].type.output
    d = inner_type.depth + 1
    return Literal([sublist.func(None,None) for sublist in x.asList()],inner_type.name,d)
  
  def extract_arg(x):
    if type(x) is Literal:
      return [x.func(None,None)]  # retrieve the literal value
    else:
      return x

  # reserved single-character tokens
  LSQUARE,RSQUARE,LCURLY,RCURLY,EQ,PIPE,SEMI = map(Suppress,'[]{}=|;')

  # non-iterable literals
  integer = parser(Word('-'+nums,nums), int)
  string  = parser(quotedString, shlex.split)  #TODO: handle newlines
  regex   = parser(QuotedString('/'), re.compile)

  # list/range literals
  varlist = parser(Group(LSQUARE + RSQUARE), lambda _: Literal([],'arb',1))
  rstart = LSQUARE + integer + Optional(Suppress(',') + integer)
  irange = parser(Group(rstart + Suppress('..]')),                    irange)
  brange = parser(Group(rstart + Suppress('..') + integer + RSQUARE), brange)
  intlist = parser(Group(LSQUARE + delimitedList(integer) + RSQUARE), lit('int'))
  strlist = parser(Group(LSQUARE + delimitedList(string) + RSQUARE),  lit('str'))
  rgxlist = parser(Group(LSQUARE + delimitedList(regex) + RSQUARE),   lit('rgx'))
  list_lit = Forward()
  lstlist = parser(Group(LSQUARE + delimitedList(list_lit) + RSQUARE), list_of_lists)
  list_lit << (varlist | irange | brange | intlist | strlist | rgxlist | lstlist)

  # special-syntax functions
  slurp = parser(QuotedString('<',endQuoteChar='>'), lambda s: ('slurp',[s]))
  shell = parser(QuotedString('`'),                  lambda s: ('shell',[s]))

  # functions and arguments
  identifier = Word(alphas, alphanums+'_')
  subpipe = Forward()
  function = Forward()
  argument = parser(string | list_lit | regex | integer | subpipe | slurp | shell | function, extract_arg)
  function << parser(Group(identifier + Group(ZeroOrMore(argument))), lambda x: tuple(x.asList()))

  # an atom is anything that can fit between pipes on its own
  atom = (function | slurp | shell | list_lit)

  # an expression/subpipe is multiple atoms piped together
  expression = Group(atom + ZeroOrMore(PIPE + atom))
  subpipe << parser(LCURLY + expression + RCURLY, lambda s: ('subpipe',s.asList()))
  
  # statements and lines are pretty standard
  statement = Group(Optional(identifier + EQ, default=None) + expression)
  line = (statement + Optional(SEMI)) | pythonStyleComment.suppress() | White().suppress()

#
# TODO: return JSON blob!
#
  def parse_line(s):
    try:
      return line.parseString(s).asList()
    except ParseException as e:
      print 'Error parsing %r' % s
      print e
      import sys
      sys.exit(1)

  return parse_line

# each returns an iterable of (lhs,rhs) pairs
parse_line = __setup_parser()

def parse_blob(blob):
  for line in blob.splitlines():
    for pl in parse_line(line):
      yield pl  # == (lhs,rhs)

def parse_file(fh):
  for line in fh:
    for pl in parse_line(line):
      yield pl  # == (lhs,rhs)
