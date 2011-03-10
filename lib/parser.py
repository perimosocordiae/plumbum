
import re,sys,shlex
from pyparsing import *
from stdlib import stdlib
from itertools import count

def Statement(sides):
    lhs, rhs = sides.asList()
    if not lhs: # just an eval
        res = rhs([])
        if res: return res
    else:
        stdlib[lhs] = rhs
    return {}

def Expression(pipe):
    expr = fold_pipe([x.atom for x in pipe.asList()])
    if not hasattr(expr,'__call__'):
        return lambda _: expr
    return expr 

def fold_pipe(pipe):
    def thepipe(inseq):
        res = pipe[0]
        if hasattr(res,'__call__'):
            res = res(inseq)
        for x in pipe[1:]:
            res = x(res)
        return res
    return thepipe

class Atom:
    def __init__(self,val):
        self.atom = val.asList()[0]

    def __repr__(self):
        return "<atom %r>"%self.atom

class Function(Atom):
    def __init__(self, cmd_args):
        cmd,*args = cmd_args
        args = [a.atom if hasattr(a,'atom') else a for a in args]
        if cmd not in stdlib:
            raise ValueError("%s isn't in the stdlib"%cmd)
        self.atom = lambda seq: stdlib[cmd](seq,*args)

class Inline(Function):
    def __init__(self, infn):
        self.atom = infn([])

class Slurp(Function):
    def __init__(self,fname):
        self.atom = stdlib['_slurp_'](fname)

class Shell(Function):
    def __init__(self,cmd):
        self.atom = stdlib['_shell_'](cmd)

def bounded_range(args):
    start = args[0]
    second = args[1] if len(args) > 2 else None
    step = second - start if second else 1
    # inclusive ranges
    last = args[-1] + (1 if step > 0 else -1)
    return range(start, last, step)

def inf_range(args):
    start = args[0]
    second = args[1] if len(args) > 1 else None
    step = second - start if second else 1
    return count(start, step)

def parser(p,action):
    p.setParseAction(lambda t: action(t[0]))
    return p

def generate_grammar(): # entirely for decluttering the global namespace
    LCURLY,RCURLY,LSQUARE,RSQUARE,EQ,DOLLAR,PIPE,SEMI = map(Suppress,'{}[]=$|;')
    slurp = parser(QuotedString('<',endQuoteChar='>'),Slurp)
    shell = parser(QuotedString('`'),Shell)
    expression = parser(Forward(),Expression)
    inline = parser(LCURLY + expression + RCURLY,Inline)
    regex = parser(QuotedString('/'),re.compile)
    integer = parser(Word('-123456789',nums),int)
    literal = Forward()
    brange = parser(Group(LSQUARE + integer + Optional(Suppress(',') + integer)
        + Suppress('..') + integer + RSQUARE), bounded_range)
    irange = parser(Group(LSQUARE + integer + Optional(Suppress(',') + integer)
        + Suppress('..]')), inf_range)
    listlit = parser(Group(LSQUARE + Optional(delimitedList(literal)) + RSQUARE)
            ,lambda lst: [lst])
    string = parser(quotedString,shlex.split)
    literal << (string | regex | integer | listlit | brange | irange)
    atom_lit = parser(Group(string | listlit | brange | irange),Atom)
    identifier = Word(alphas, alphanums+'_')
    atom = Forward()
    function = parser(Group(identifier + ZeroOrMore(atom | literal)),Function)
    atom << (slurp | shell | inline | atom_lit | function)
    expression << Group(atom + ZeroOrMore(PIPE + atom))
    statement = parser(
            Group(Optional(identifier + EQ, default=None) + expression),
            Statement)
    line = (statement + Optional(SEMI)) | pythonStyleComment.suppress()
    return line

 # this is the only thing one should import from this file...
program_parser = generate_grammar()
