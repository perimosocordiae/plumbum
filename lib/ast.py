
import re,sys
from shlex import shlex
from functools import reduce
from pickle import load,dump
from stdlib import stdlib

class Program(object):
    def __init__(self):
        self.stmts = []
        self.symtab = {}
    def parse_file(self,fname):
        infile = open(fname) if fname != '-' else sys.stdin
        for line in infile:
            self.parse_line(line)
    def parse_line(self,line):
        line = line.split('#')[0].strip() # comments begone!
        asn = line.split('=')
        assert len(asn) < 3, 'Too many assignments'
        if len(asn) == 1 and len(line) > 0:
            self.stmts.append(Expression(line))
        elif len(asn) == 2:
            name,expr = asn #TODO: make assignment more powerful
            assert name.strip() not in stdlib, 'Overriding stdlib function'
            #TODO: look for infinite recursion cases
            self.symtab[name.strip()] = Expression(expr) # breaks recursion
    def compile(self,fname):
        with open(fname,'wb') as f:
            dump((self.stmts,self.symtab),f,-1)
    def load_compiled(self,fname):
        with open(fname,'rb') as f:
            self.stmts,self.symtab = load(f)
    def run(self):
        res = None # seems silly, but needs to be like this for the REPL
        while len(self.stmts) > 0:
            res = self.stmts.pop(0).run(None,self.symtab)
        return res

class Expression(object):
    def __init__(self,expr): 
        self.pipe = [parse_atom(atom) for atom in expr.split('|')]
    def run(self,inputs,symtab):
        apply = lambda in_pipe,atom: atom.run(in_pipe,symtab)
        return reduce( apply,self.pipe,inputs)
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

class Atom(object): pass # base class
class Function(Atom):
    def __init__(self,atom):
        self.cmd, args = lex_atom(atom)
        assert self.cmd in stdlib
        self.args = [parse_atom(a) for a in args]
    def run(self,inputs,symtab):
        args = [a.run(None,symtab) for a in self.args]
        return stdlib[self.cmd](inputs,*args)
    def __str__(self):
        return self.cmd+' '+' '.join(map(str,self.args))

class Literal(Atom):
    def __init__(self,atom):
        if atom.startswith('/') and atom.endswith('/'):
            self.val = re.compile(atom[1:-1])
        else: 
            try: 
                self.val = eval(atom)
            except SyntaxError:
                self.val = atom # just the bare string
    def run(self,inputs,symtab):
        assert inputs is None, "Trying to feed a stream to a literal"
        return self.val
    def __str__(self):
        return str(self.val)

class Reference(Atom):
    def __init__(self,ref): 
        self.ref = ref
    def run(self,inputs,symtab):
        assert self.ref in symtab, "reference $%s not in symtab"%self.ref
        return symtab[self.ref].run(inputs,symtab)
    def __str__(self):
        return '$'+self.ref

class Slurp(Atom):
    def __init__(self,fname):
        self.fname = fname
    def run(self,*_):
        return stdlib['_slurp_'](self.fname)
    def __str__(self):
        return '<%s>'% self.fname

class Shell(Atom):
    def __init__( self,cmd):
        self.cmd = cmd
    def run(self,inputs,_):
        return stdlib['_shell_'](self.cmd,inputs)
    def __str__(self):
        return '`%s`'%self.cmd

ref_expr   = re.compile('\$(\w+)')
slurp_expr = re.compile('<\s*(.*?)\s*>')
shell_expr = re.compile('`\s*(.+?)\s*`')
inline_expr = re.compile('\^\s*(.+?)\s*\^')
