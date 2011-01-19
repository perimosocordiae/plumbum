
import re,sys,_ast
from ast import parse as ast_parse
from pyparsing import *
from stdlib import stdlib # for inlining purposes

# convenience functions for AST manipulation
def ast_select(s):
    return ast_parse(s).body[0].value

def ast_ctor(toparse,**kwargs):
    c = ast_select(toparse)
    for k,v in kwargs.items():
        setattr(c,k,v)
    return c


 #################
 # parse actions #
 #################

def Statement(sides):
    lhs, rhs = sides
    if not lhs:
        # use empty list as initial seq
        s = _ast.Expr(value=ast_ctor('dummy([])',func=rhs))
    else:
        s = ast_parse(lhs+' = dummy').body[0]
        s.value = rhs
    s.col_offset = 0
    return s

 # woo recursion! TODO: rewrite as a fold
DUMMY = 0xdead
def fold_ast(rpipe):
    atom = rpipe[-1]
    if type(atom) is _ast.Call:
        if len(rpipe) > 1:
            atom.args[0] = fold_ast(rpipe[:-1])
        elif atom.args[0] == DUMMY:
            atom.args[0] = ast_select('initial')
        return atom
    if len(rpipe) > 1:
        if type(atom) is _ast.Name:
            a = atom.id
            raise Exception("Invalid name: '%s'. Did you mean '$%s'?"%(a,a))
        raise Exception('Invalid location for literal: %s'%atom)
    return atom

def Expression(pipe): 
    return ast_ctor('lambda initial: 1', body=fold_ast(pipe))

def Function(atom):
    cmd, args = atom[0], atom[1:]
    if cmd not in stdlib: # hope it's a user-defined!
        return ast_ctor(cmd+'()', args=[DUMMY])
    func = stdlib[cmd]
    if type(func) is str: # inlines
        value = ast_ctor('(%s)()' % func, args=[DUMMY])
    else:
        value = ast_ctor('stdlib["%s"]()' % cmd, args=[DUMMY])
    value.args.extend(args)
    return value

def Regex(patt):
    return ast_select("re.compile(r'%s')" % patt)

def String(s):
    return ast_select(s)

def Range(args): #TODO: bug! ranges of form [1,4..] are interpreted [1..4]
    start = args[0]
    second = args[1] if len(args) > 2 else None
    last = args[-1] if len(args) > 1 else None
    step = Integer(second.n - start.n) if second else Integer(1)
    if last:
        last = Integer(last.n + (1 if step.n > 0 else -1)) # make it inclusive
        return ast_ctor("range()", args=[start, last, step])
    return ast_ctor("count()", args=[start, step])

def List(lst):
    return _ast.List(elts=list(lst), ctx=_ast.Load())

def Integer(i):
    return _ast.Num(n=int(i))

def Inline(expr):
    #TODO: there's a subtle bug here: expr.body has a free variable 'initial'
    #       usually, it won't cause trouble, but it's technically not correct.
    return expr.body

def Slurp(fname):
    return ast_select("stdlib['_slurp_']('%s')" % fname)

def Shell(cmd):
    return ast_select("stdlib['_shell_']('%s')" % cmd)


###########
# Grammar #
###########

def parser(p,action):
    p.setParseAction(lambda t: action(t[0]))
    return p

def generate_grammar(): # entirely for decluttering the global namespace
    LCURLY,RCURLY,LSQUARE,RSQUARE,EQ,DOLLAR,PIPE,SEMI = map(Suppress,'{}[]=$|;')
    slurp = parser(QuotedString('<',endQuoteChar='>'),Slurp)
    shell = parser(QuotedString('`'),Shell)
    expression = parser(Forward(),Expression)
    inline = parser(LCURLY + expression + RCURLY,Inline)
    regex = parser(QuotedString('/'),Regex)
    integer = parser(Word('-123456789',nums),Integer)
    literal = Forward()
    rangelit = (LSQUARE + integer + Optional(Suppress(',') + integer) + 
                Suppress('..') + Optional(integer) + RSQUARE)
    rangelit.setParseAction(Range)
    listlit = LSQUARE + Optional(delimitedList(literal)) + RSQUARE
    listlit.setParseAction(List)
    string = parser(quotedString,String)
    literal << (string | regex | integer | listlit | rangelit)
    identifier = Word(alphas, alphanums)
    atom = Forward()
    function = parser(Group(identifier + ZeroOrMore(atom)),Function)
    atom << (slurp | shell | inline | literal | function)
    expression << Group(atom + ZeroOrMore(PIPE + atom))
    statement = parser(
            Group(Optional(identifier + EQ, default=None) + expression),
            Statement)
    line = (statement + Optional(SEMI)) | pythonStyleComment.suppress()
    return Group(ZeroOrMore(line))

 # this is the only thing one should import from this file...
program_parser = generate_grammar()
