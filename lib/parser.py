
import re,sys,_ast
from ast import parse as ast_parse, dump as ast_dump
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

def Expression(pipe):
    return ast_ctor('lambda initial: 1', body=fold_ast(pipe))

def fold_ast(pipe):
    init,*rest = reversed(pipe)
    return init.fold_ast(rest)

class Atom: pass

class Inline(Atom):
    def __init__(self,expr):
        #TODO: there's a subtle bug here:
        # expr.body has a free variable 'initial'.
        # Usually, it won't cause trouble, but it's technically not correct.
        self.atom = expr.body

DUMMY = 0xdead # value doesn't really matter
class Function(Atom):
    def __init__(self, cmd_args):
        cmd,*args = cmd_args
        if cmd not in stdlib: # hope it's a user-defined!
            #TODO: actually store these, w/ tags
            self.atom = ast_ctor(cmd+'()', args=[DUMMY])
        else:
            func = stdlib[cmd]
            if type(func) is str: # inlines
                self.atom = ast_ctor('(%s)()' % func, args=[DUMMY])
            else:
                self.atom = ast_ctor('stdlib["%s"]()' % cmd, args=[DUMMY])
        self.atom.args.extend(x.atom for x in args)

    def fold_ast(self, upstream):
        if upstream:
            a,*rest = upstream
            self.check_type(a)
            self.atom.args[0] = a.fold_ast(rest)
        else:
            self.atom.args[0] = ast_select('initial')
        return self.atom

    def check_type(self, param):
        #TODO: use tags
        pass

class Slurp(Function):
    def __init__(self,fname):
        self.atom = ast_select(stdlib['_slurp_']+"('%s')" % fname)
        self.type = 'strseq'

    def fold_ast(self, upstream):
        if upstream:
            raise Exception("Can't pass things into a slurp (yet)")
        return self.atom

class Shell(Function):
    def __init__(self,cmd):
        self.atom = ast_select(stdlib['_shell_']+"('%s')" % cmd)
        self.type = 'strseq'

    def fold_ast(self, upstream):
        if upstream:
            raise Exception("Can't pass things into a shell command (yet)")
        return self.atom

class Literal(Atom):
    def fold_ast(self, upstream):
        if upstream:
            raise Exception("Can't pass things into a Literal")
        return self.atom

class Regex(Literal):
    def __init__(self,patt):
        self.atom = ast_select("re.compile(r'%s')" % patt)
        self.type = 'regex'
        self.val = patt

class String(Literal):
    def __init__(self,s):
        self.atom = ast_select(s)
        self.type = 'str'
        self.val = s

class Integer(Literal):
    def __init__(self,i):
        self.atom = _ast.Num(n=int(i))
        self.type = 'int'
        self.val = self.atom.n

class BoundedRange(Literal):
    def __init__(self,args):
        start = args[0]
        second = args[1] if len(args) > 2 else None
        step = Integer(second.val - start.val) if second else Integer(1)
        # inclusive ranges
        last = Integer(args[-1].val + (1 if step.val > 0 else -1))
        self.atom = ast_ctor("range()", args=[start.atom, last.atom, step.atom])
        self.type = 'intseq'

class InfRange(Literal):
    def __init__(self,args):
        start = args[0]
        second = args[1] if len(args) > 1 else None
        step = Integer(second.val - start.val) if second else Integer(1)
        self.atom = ast_ctor("count()", args=[start.atom, step.atom])
        self.type = 'intseq'

class ListLit(Literal):
    def __init__(self,lst):
        self.atom = _ast.List(elts=[x.atom for x in lst], ctx=_ast.Load())
        self.type = lst[0].type # assume homogenous
 #end


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
    brange = (LSQUARE + integer + Optional(Suppress(',') + integer) +
                Suppress('..') + integer + RSQUARE)
    irange = LSQUARE + integer + Optional(Suppress(',') + integer) + Suppress('..]')
    listlit = LSQUARE + Optional(delimitedList(literal)) + RSQUARE
    # Not sure why, but PyParsing barfs unless I wrap the ctors in lambdas
    brange.setParseAction(lambda t: BoundedRange(t))
    irange.setParseAction(lambda t: InfRange(t))
    listlit.setParseAction(lambda t: ListLit(t))
    string = parser(quotedString,String)
    literal << (string | regex | integer | listlit | brange | irange)
    identifier = Word(alphas, alphanums+'_')
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
