
import re,sys,_ast
from ast import parse as ast_parse, fix_missing_locations, dump as ast_dump
from shlex import shlex
from functools import reduce
from pickle import load,dump
from stdlib import stdlib

class Program(_ast.Module):
    def __init__(self):
        super().__init__(body=[])
        self.lineno = 1
        self.col_offset = 1
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
            self.body.append(Statement(line))
            self.body[-1].lineno = lineno
        elif len(asn) == 2:
            lhs,rhs = asn
            assert lhs.strip() not in stdlib, 'Overriding stdlib function'
            self.body.insert(0,Assignment(lhs.strip(),rhs))
            self.body[0].lineno = lineno
    def save_compiled(self,fname):
        fix_missing_locations(self)
        self.code = compile(self,self.fname,'exec')
        with open(fname,'wb') as f:
            dump(self.code,f,-1)
    def load_compiled(self,fname):
        with open(fname,'rb') as f:
            self.code = load(f)
    def run(self):
        if hasattr(self,'code'):
            return exec(self.code)
        fix_missing_locations(self) # buggy
   #     print(ast_dump(self,False,True))
        exec(compile(self,self.fname,'exec'))
        self.body = [] # clear the module

class Statement(_ast.Expr):
    def __init__(self,line):
        c = ast_select('dummy()')
        c.func = Expression(line)
        super().__init__(value=c)
        self.col_offset = 1

class Assignment(_ast.Assign):
    def __init__(self,lhs,rhs):
        super().__init__(
            targets=[_ast.Name(id=lhs, ctx=_ast.Store())],
            value=Expression(rhs))
        self.col_offset = 1

def fold_ast(rpipe):
    a = rpipe[-1]
    if type(a) is not Literal:
        c = ast_select('dummy()')
        c.func = a.value
        c.args = [fold_ast(rpipe[:-1])] if len(rpipe) > 1 else ['dummy']
        return c
    elif len(rpipe) == 1:
        return a.value
    else: raise Exception('Literal atom not at beginning of pipe!')

def ast_select(s):
    return ast_parse(s).body[0].value

class Expression(_ast.Lambda):
    def __init__(self,expr): 
        self.pipe = [parse_atom(atom) for atom in expr.split('|')]
        dummy = ast_select('lambda: 1')
        self.args=dummy.args
        self.body=fold_ast(self.pipe)
    def __str__(self):
        return ' | '.join(str(a) for a in self.pipe)

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

class Function:
    def __init__(self,atom):
        self.cmd, args = lex_atom(atom)
        assert self.cmd in stdlib
        self.args = [parse_atom(a) for a in args]
        self.value = ast_select(
                'lambda inputs: stdlib[dummy](inputs)')
        self.value.body.func.slice.value = _ast.Str(s=self.cmd)
        self.value.body.args.extend(a.value for a in self.args)
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
        self.value = ast_select("lambda _: stdlib['_slurp_'](dummy)")
        self.value.body.args[0].id = fname
    def __str__(self):
        return '<%s>' % self.fname

class Shell:
    def __init__( self,cmd):
        self.cmd = cmd
        self.value = ast_select("lambda inputs: stdlib['_shell_'](dum,inputs)")
        self.value.body.args[0].id = cmd
    def __str__(self):
        return '`%s`'%self.cmd

ref_expr   = re.compile('\$(\w+)')
slurp_expr = re.compile('<\s*(.*?)\s*>')
shell_expr = re.compile('`\s*(.+?)\s*`')
inline_expr = re.compile('\^\s*(.+?)\s*\^')
