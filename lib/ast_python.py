
import re,sys,_ast
from ast import parse as ast_parse, fix_missing_locations, dump as ast_dump
from shlex import shlex
from functools import reduce
from marshal import load,dump # for saving compiled files
from stdlib import stdlib
from unparse import unparse

class Program:
    def __init__(self):
        self.tree = _ast.Module(body=[])
        self.tree.lineno = 1
        self.tree.col_offset = 1
        self.fname = '<>'

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
        exec(compile(self.tree,self.fname,'exec'))

class REPLProgram(Program):
    def run(self):
        assert len(self.tree.body) == 1
        #print(unparse(self.tree)) # super useful for debugging
        stmt = self.tree.body.pop()
        stree = _ast.Expression(body=stmt.value)
        fix_missing_locations(stree)
        return eval(compile(stree,'<repl>','eval'))

def Statement(line):
    c = ast_select('dummy([])') # call w/ empty list as initial seq
    c.func = Expression(line)
    s = _ast.Expr(value=c)
    s.col_offset = 1
    return s

 #TODO: fix!
def Assignment(lhs,rhs):
    a = ast_parse(lhs+' = dummy').body[0]
    a.value = Expression(rhs)
    a.col_offset = 1
    return a

def fold_ast(rpipe):
    a = rpipe[-1]
    if type(a) is not Literal:
        c = ast_select('dummy()')
        c.func = a.value
        if len(rpipe) > 1:
            c.args = [fold_ast(rpipe[:-1])]
        elif type(a) is Slurp:
            c.args = [] # slurps get no input
        else:
            c.args = [ast_select('initial')]
        return c
    elif len(rpipe) == 1:
        return a.value
    else: raise Exception('Literal atom not at beginning of pipe!')

def ast_select(s):
    return ast_parse(s).body[0].value

def Expression(expr): 
    lmda = ast_select('lambda initial: 1')
    pipe = [parse_atom(atom) for atom in expr.split('|')]
    lmda.body=fold_ast(pipe)
    return lmda

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
    try: return Function(atom)
    except AssertionError: pass 
    #print('literal: [%s]'%atom)
    return Literal(atom)

def lex_atom(atom):
    lex = shlex(atom,posix=False)
    lex.whitespace_split = True
    lex.quotes += '/^' # how I wish I could have matching quote chars, like {}
    cmd,*args = list(lex)
    return cmd,args

 # for convenience...
def ast_ctor(toparse,**kwargs):
    c = ast_select(toparse)
    for k,v in kwargs.items():
        setattr(c,k,v)
    return c

class Function:
    def __init__(self,atom):
        self.cmd, args = lex_atom(atom)
        assert self.cmd in stdlib
        self.args = [parse_atom(a) for a in args]
        self.value = ast_select(
                'lambda inputs: stdlib[dummy](inputs)')
        self.value.body.func.slice.value = _ast.Str(s=self.cmd)
        for a in self.args:
            if type(a) is Literal:
                self.value.body.args.append(a.value)
            else:
                self.value.body.args.append(ast_ctor('d([])',func=a.value))

    def __str__(self):
        return self.cmd+'  '+' '.join(map(str,self.args))

class Literal:
    def __init__(self,atom):
        if atom.startswith('/') and atom.endswith('/'):
            self.value=ast_select('re.compile(dummy)')
            self.value.args[0] = _ast.Str(s=atom[1:-1])
        else: 
            try: 
                self.value=ast_select(atom)
            except SyntaxError:
                self.value=_ast.Str(s=atom)
    def __str__(self):
        return str(self.value)

class Reference:
    def __init__(self,ref): 
        self.value=_ast.Name(id=ref,ctx=_ast.Load())
    def __str__(self):
        return '$'+self.value.id

class Slurp:
    def __init__(self,fname):
        self.fname = fname
        self.value = ast_select("lambda: stdlib['_slurp_']('dummy')")
        self.value.body.args[0].s = fname
    def __str__(self):
        return '<%s>' % self.fname

class Shell:
    def __init__(self,cmd):
        self.cmd = cmd
        self.value = ast_select("lambda inputs: stdlib['_shell_'](inputs)")
        self.value.body.args.append(_ast.Str(s=self.cmd))
    def __str__(self):
        return '`%s`'%self.cmd

ref_expr   = re.compile('\$(\w+)')
slurp_expr = re.compile('<\s*(.*?)\s*>')
shell_expr = re.compile('`\s*(.+?)\s*`')
inline_expr = re.compile('\^\s*(.+?)\s*\^')
