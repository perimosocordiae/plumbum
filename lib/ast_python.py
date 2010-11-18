
import re,sys,_ast
from ast import parse as ast_parse, fix_missing_locations, dump as ast_dump
from shlex import shlex
from functools import reduce
from marshal import load,dump # for saving compiled files
from unparse import unparse

stdlib = {}

class Program:
    def __init__(self, current_stdlib):
        self.refresh_stdlib(current_stdlib)
        self.tree = _ast.Module(body=[])
        self.tree.lineno = 1
        self.tree.col_offset = 1
        self.fname = '<>'

    def refresh_stdlib(self, new_stdlib):
        global stdlib
        stdlib = new_stdlib

    def parse_file(self,fname):
        self.fname = fname
        infile = open(fname) if fname != '-' else sys.stdin
        for i,line in enumerate(infile):
            self.parse_line(line,i+1)

    def parse_line(self,line,lineno=1):
        line = line.split('#')[0].strip() # comments begone!
        asn = line.split('=')
        assert len(asn) < 3, 'Too many assignments'
        if len(asn) == 1 and len(line) > 0:
            self.tree.body.append(Statement(line))
            self.tree.body[-1].lineno = lineno
        elif len(asn) == 2:
            lhs,rhs = asn
            assert lhs.strip() not in stdlib, 'Overriding stdlib function'
            self.tree.body.insert(0,Assignment(lhs.strip(),rhs))
            self.tree.body[0].lineno = lineno

    def save_compiled(self,fname):
        fix_missing_locations(self.tree)
        self.code = compile(self.tree,self.fname,'exec')
        with open(fname,'wb') as f:
            dump(self.code,f)

    def load_compiled(self,fname):
        with open(fname,'rb') as f:
            self.code = load(f)

    def run(self):
        if hasattr(self,'code'):
            return exec(self.code)
        fix_missing_locations(self.tree)
        #print(unparse(self.tree)) # super useful for debugging
        exec(compile(self.tree,self.fname,'exec'),globals(),globals())

class REPLProgram(Program):
    def run(self, debug=False):
        if debug:
            assert len(self.tree.body) == 1
            print(unparse(self.tree))
        stmt = self.tree.body.pop()
        if type(stmt) is _ast.Assign:
            stree = _ast.Module(body=[stmt])
            fix_missing_locations(stree)
            exec(compile(stree,'<repl>','exec'), globals(), globals())
        else:
            stree = _ast.Expression(body=stmt.value)
            fix_missing_locations(stree)
            return eval(compile(stree,'<repl>','eval'))

def Statement(line):
    c = ast_select('dummy([])') # call w/ empty list as initial seq
    c.func = Expression(line)
    s = _ast.Expr(value=c)
    s.col_offset = 1
    return s

def Assignment(lhs,rhs):
    asn = ast_parse(lhs+' = dummy').body[0]
    asn.value = Expression(rhs)
    asn.col_offset = 1
    return asn

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
        raise Exception('Invalid location for literal: %s'%atom)
    return atom

def Expression(expr): 
    pipe = [parse_atom(atom) for atom in expr.split('|')]
    return ast_ctor('lambda initial: 1', body=fold_ast(pipe))

def parse_atom(atom):
    atom = atom.strip()
    slurp = slurp_expr.match(atom)
    if slurp: return Slurp(slurp.group(1))
    shell = shell_expr.match(atom)
    if shell: return Shell(shell.group(1))
    ref = ref_expr.match(atom)
    if ref:   return Reference(ref.group(1))
    inline = inline_expr.match(atom)
    if inline: return parse_atom(inline.group(1))
    try:
        return Builtin(atom)
    except KeyError:
        return Literal(atom)

def lex_atom(atom):
    lex = shlex(atom,posix=False)
    lex.whitespace_split = True
    lex.quotes += '/^' # how I wish I could have matching quote chars, like {}
    cmd,*args = list(lex)
    return cmd,args

 # for convenience...
def ast_select(s):
    return ast_parse(s).body[0].value

def ast_ctor(toparse,**kwargs):
    c = ast_select(toparse)
    for k,v in kwargs.items():
        setattr(c,k,v)
    return c

def Builtin(atom):
    cmd, args = lex_atom(atom)
    func = stdlib[cmd]
    if type(func) is str: # inlines
        value = ast_select('(%s)([])' % func)
    else:
        value = ast_select('stdlib["%s"]([])' % cmd)
    value.args.extend(parse_atom(a) for a in args)
    return value

def Literal(atom):
    if atom.startswith('/') and atom.endswith('/'):
        return ast_select("re.compile(r'%s')" % atom[1:-1])
    try: 
        return ast_select(atom)
    except SyntaxError:
        return _ast.Str(s=atom)

def Reference(name):
    return ast_select(name+'([])')

def Slurp(fname):
    return ast_select("stdlib['_slurp_']('%s')" % fname)

def Shell(cmd):
    return ast_select("stdlib['_shell_']([],'%s')" % cmd)

ref_expr   = re.compile('\$(\w+)')
slurp_expr = re.compile('<\s*(.*?)\s*>')
shell_expr = re.compile('`\s*(.+?)\s*`')
inline_expr = re.compile('\^\s*(.+?)\s*\^')
