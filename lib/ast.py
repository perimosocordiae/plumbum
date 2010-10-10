
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
        res = None
        while len(self.stmts) > 0:
            res = self.stmts.pop(0).run(None,self.symtab)
        return res # for interactive sessions, mostly

class Expression(object):
    def __init__(self,expr):
        self.pipe = [self.parse(atom) for atom in expr.split('|')]
    def parse(self,atom):
        slurp = slurp_expr.search(atom)
        if slurp:
            return Slurp(slurp.group(1))
        shell = shell_expr.search(atom)
        if shell:
            return Shell(shell.group(1))
        return Atom(atom)
    def run(self,inputs,symtab):
        apply = lambda in_pipe,atom: atom.run(in_pipe,symtab)
        return reduce(apply,self.pipe,inputs)
    def __str__(self):
        return ' | '.join(str(a) for a in self.pipe)

class Atom(object):
    def __init__(self,atom):
        self.atom = atom.strip()
        lex = shlex(atom,posix=True)
        lex.wordchars += '?!@$-' # the more the merrier
        lex.quotes += '/' # for regexen
        self.cmd,*self.args = list(lex)
    def run(self,inputs,symtab):
        if self.cmd in symtab:
            return symtab[self.cmd].run(inputs,symtab)
        if self.cmd in stdlib:
            args = [(Atom(a[1:]).run([],symtab) if a.startswith('$') else a) for a in self.args]
            return stdlib[self.cmd](inputs,*args)
        return eval(self.atom)
    def __str__(self):
        return self.atom
class Slurp(Atom):
    def __init__(self,fname):
        self.fname = fname
    def run(self,*_):
        return stdlib['_slurp_'](self.fname)
    def __str__(self):
        return '<%s>'%self.fname
class Shell(Atom):
    def __init__(self,cmd):
        self.cmd = cmd
    def run(self,*_):
        return stdlib['_shell_'](self.cmd)
    def __str__(self):
        return '`%s`'%self.cmd

#is_string = lambda s: str(s) == s # hax
#is_type = lambda t,x: t in type(x).mro()
slurp_expr = re.compile('<\s*(.*?)\s*>')
shell_expr = re.compile('`\s*(.*?)\s*`')
