import re
from pyparsing import ParserElement, ParseException
from pyparsing import Suppress, QuotedString, Word, Optional, Forward, ZeroOrMore
from pyparsing import alphas, alphanums, nums, delimitedList, pythonStyleComment, empty
ParserElement.enablePackrat()

def __setup_parser():
  # reserved single-character tokens
  LSQUARE,RSQUARE,LCURLY,RCURLY,EQ,PIPE,SEMI = map(Suppress,'[]{}=|;')

  # non-iterable literals
  integer = simple(Word('-'+nums,nums), 'int', int)
  string  = simple(QuotedString("'") | QuotedString('"'), 'str', str)
  regex   = simple(QuotedString('/'), 'rgx', re.compile)

  # list/range literals
  emptylist = named(LSQUARE + RSQUARE, 'emptylist')
  rstart = LSQUARE + integer + Optional(Suppress(',') + integer)
  irange = named(rstart + Suppress('..]'), 'irange')
  brange = named(rstart + Suppress('..') + integer + RSQUARE, 'brange')
  intlist = named(LSQUARE + delimitedList(integer) + RSQUARE, 'intlist')
  strlist = named(LSQUARE + delimitedList(string)  + RSQUARE, 'strlist')
  rgxlist = named(LSQUARE + delimitedList(regex)   + RSQUARE, 'rgxlist')
  list_lit = Forward()
  lstlist = named(LSQUARE + delimitedList(list_lit) + RSQUARE, 'lstlist')
  list_lit << (emptylist | irange | brange | intlist | strlist | rgxlist | lstlist)

  # special-syntax functions
  slurp = special(QuotedString('<',endQuoteChar='>'), 'slurp')
  shell = special(QuotedString('`'), 'shell')

  # functions and arguments
  name = simple(Word(alphas, alphanums+'_'), 'name', str)
  subpipe = Forward()
  function = Forward()
  argument = string | list_lit | regex | integer | subpipe | slurp | shell | function
  function << name + named(ZeroOrMore(argument), 'arguments')
  function.setParseAction(lambda parse: ('function', dict(parse.asList())))

  # an atom is anything that can fit between pipes on its own
  atom = (function | slurp | shell | list_lit)

  # an expression/subpipe is multiple atoms piped together
  expression = named(atom + ZeroOrMore(PIPE + atom), 'pipe')
  subpipe << LCURLY + expression + RCURLY

  # statements and lines are pretty standard
  statement = Optional(name + EQ, default=('name','')) + expression
  statement.setParseAction(lambda parse: dict(parse.asList()))
  line = (statement | empty).ignore(pythonStyleComment)
  return line.parseString

def simple(p, name, func):
  pa = lambda parse: (name, func(parse[0]))
  return p.setParseAction(pa)

def named(p, name):
  pa = lambda parse: (name, parse.asList())
  return p.setParseAction(pa)

def special(p, func_name):
  #FIXME: gross hack to type the args
  pa = lambda parse: ('function',{'name':func_name, 'arguments':[('str',parse.asList()[0])]})
  return p.setParseAction(pa)

_parser = __setup_parser()

def parse_line(s):
  try:
    p = _parser(s).asList()
  except ParseException as e:
    print 'Error parsing %r' % s
    print e
    import sys
    sys.exit(1)
  if p and p[0]:
    #print p[0]
    return p[0]

def _parse_filter(lines):
  for line in lines:
    pr = parse_line(line)
    if pr is not None: yield pr

parse_blob = lambda blob: _parse_filter(blob.splitlines())
parse_file = lambda fh: _parse_filter(fh)
