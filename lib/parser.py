
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
def fold_ast(rpipe):
    atom = rpipe[-1]
    if type(atom) is _ast.Call:
        if len(rpipe) > 1:
            atom.args[0] = fold_ast(rpipe[:-1])
        elif type(atom.args[0]) is not _ast.Str: # slurps get no input
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

def Builtin(atom):
    cmd, args = atom[0], atom[1:]
    func = stdlib[cmd]
    if type(func) is str: # inlines
        value = ast_select('(%s)([])' % func)
    else:
        value = ast_select('stdlib["%s"]([])' % cmd)
    value.args.extend(args)
    return value

def Regex(patt):
    return ast_select("re.compile(r'%s')" % patt)

def String(s):
    return ast_select(s)

def List(lst):
    return _ast.List(elts=list(lst), ctx=_ast.Load())

def Integer(i):
    return _ast.Num(n=int(i))

def Reference(name):
    # note: name[0] == '$'
    return ast_select(name[1:]+'([])')

def Inline(expr):
    #TODO: there's a subtle bug here: expr.body has a free variable 'initial'
    #       usually, it won't cause trouble, but it's technically not correct.
    return expr.body

def Slurp(fname):
    return ast_select("stdlib['_slurp_']('%s')" % fname)

def Shell(cmd):
    return ast_select("stdlib['_shell_']([],'%s')" % cmd)


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
    reference = parser(Word('$', alphanums),Reference)
    expression = parser(Forward(),Expression)
    inline = parser(LCURLY + expression + RCURLY,Inline)
    regex = parser(QuotedString('/'),Regex)
    integer = parser(Word('-123456789',nums),Integer)
    literal = Forward()
    listlit = LSQUARE + Optional(delimitedList(literal)) + RSQUARE
    listlit.setParseAction(List)
    string = parser(quotedString,String)
    literal << (string | regex | integer | listlit)
    identifier = Word(alphas, alphanums)
    atom = Forward()
    builtin = parser(Group(identifier + ZeroOrMore(atom)),Builtin)
    atom << (slurp | shell | reference | inline | literal | builtin)
    expression << Group(atom + ZeroOrMore(PIPE + atom))
    statement = parser(
            Group(Optional(identifier + EQ, default=None) + expression),
            Statement)
    line = (statement + Optional(SEMI)) | pythonStyleComment.suppress()
    return Group(ZeroOrMore(line))

 # this is the only thing one should import from this file...
program_parser = generate_grammar()
