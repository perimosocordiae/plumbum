from pyparsing import *
ParserElement.enablePackrat()

def __setup_parser():
  # reserved single-character tokens
  LSQUARE,RSQUARE,LCURLY,RCURLY,EQ,PIPE,SEMI = map(Suppress,'[]{}=|;')

  # non-iterable literals
  integer = Word('-'+nums,nums)('integer')
  string  = (QuotedString("'") | QuotedString('"'))('string')
  regex   = QuotedString('/')('regex')

  # list/range literals
  emptylist = Group(LSQUARE + RSQUARE)('emptylist')
  rstart = LSQUARE + integer + Optional(Suppress(',') + integer)
  irange = Group(rstart + Suppress('..]'))('irange')
  brange = Group(rstart + Suppress('..') + integer + RSQUARE)('brange')
  intlist = Group(LSQUARE + delimitedList(integer) + RSQUARE)('intlist')
  strlist = Group(LSQUARE + delimitedList(string) + RSQUARE)('strlist')
  rgxlist = Group(LSQUARE + delimitedList(regex) + RSQUARE)('rgxlist')
  list_lit = Forward()
  lstlist = Group(LSQUARE + delimitedList(list_lit) + RSQUARE)('lstlist')
  list_lit << (emptylist | irange | brange | intlist | strlist | rgxlist | lstlist)

  # special-syntax functions
  slurp =QuotedString('<',endQuoteChar='>')('slurp')
  shell = QuotedString('`')('shell')

  # functions and arguments
  name = Word(alphas, alphanums+'_')('name')
  subpipe = Forward()
  function = Forward()('function')
  argument = string | list_lit | regex | integer | subpipe | slurp | shell | function
  function << Group(name + Optional(Group(OneOrMore(argument))('arguments')))

  # an atom is anything that can fit between pipes on its own
  atom = (function | slurp | shell | list_lit)

  # an expression/subpipe is multiple atoms piped together
  expression = Group(atom + ZeroOrMore(PIPE + atom))('pipe')
  subpipe << LCURLY + expression + RCURLY
  
  # statements and lines are pretty standard
  statement = Group(Optional(name + EQ) + expression)('statement')
  line = (statement | empty)('line')
  line.ignore(pythonStyleComment)
  return line

_parser = __setup_parser()

# import here because I plan on "doing it right" and removing this later
from lxml import objectify
def parse_line(s):
  try:
    parse_result = _parser.parseString(s)
  except ParseException as e:
    print 'Error parsing %r' % s
    print e
    import sys
    sys.exit(1)
  # convert raw parse into a nicer format (JSON-like)
  #TODO
  # - avoid horrible pyparsing -> XML -> python chain
  # - convert slurp and shell into function syntax?
  if not parse_result.line: return
  xml_str = parse_result.line.asXML()
  return objectify.fromstring(xml_str)

def _parse_filter(lines):
  for line in lines:
    pr = parse_line(line)
    if pr is not None: yield pr

parse_blob = lambda blob: _parse_filter(blob.splitlines())
parse_file = lambda fh: _parse_filter(fh)
