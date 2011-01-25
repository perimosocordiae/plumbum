
import re, sys, ast
from optimizer import Optimizer
from marshal import load,dump # for saving compiled files
from unparse import unparse
from stdlib import * # to not break inlined builtins
from parser import program_parser

stdlib = {}

class Program:
    def __init__(self, current_stdlib):
        self.refresh_stdlib(current_stdlib)
        self.tree = ast.Module(body=[])
        self.tree.lineno = 1
        self.tree.col_offset = 1
        self.fname = '<>'

    def refresh_stdlib(self, new_stdlib):
        global stdlib
        stdlib = new_stdlib

    def parse_file(self,fname):
        self.fname = fname
        infile = open(fname) if fname != '-' else sys.stdin
        #TODO: figure out why parsing the file all at once fails
        for line in infile:
            self.parse_line(line)

    def parse_line(self,line):
        self.__add_stmts(program_parser.parseString(line))
    
    def __add_stmts(self, parse_res):
        for num,stmt in enumerate(parse_res[0]):
            if type(stmt) is ast.Expr:
                self.tree.body.append(stmt)
                self.tree.body[-1].lineno = num+1
            else:
                self.tree.body.insert(0, stmt)
                self.tree.body[0].lineno = num+1

    def save_compiled(self,fname):
        #self.optimize()
        ast.fix_missing_locations(self.tree)
        self.code = compile(self.tree,self.fname,'exec')
        with open(fname,'wb') as f:
            dump(self.code,f)

    def save_as_python(self,fname):
        #self.optimize()
        self.tree.body.insert(0,ast.parse('from stdlib import *').body[0])
        f = open(fname,'w') if fname != '-' else sys.stdout
        print(unparse(self.tree), file=f)
        if f != sys.stdout: f.close()
        del self.tree.body[0]

    def load_compiled(self,fname):
        with open(fname,'rb') as f:
            self.code = load(f)

    def optimize(self):
        # transform the AST, until no further minimizations can be made
        opt = Optimizer()
        opt.redo = True  # meh
        while opt.redo:
            opt.redo = False  # double meh
            self.tree = opt.visit(self.tree)

    def run(self):
        if hasattr(self,'code'):
            return exec(self.code)
        ast.fix_missing_locations(self.tree)
        exec(compile(self.tree,self.fname,'exec'),globals(),globals())

class REPLProgram(Program):
    def run(self, debug=False):
        if debug:
            print(unparse(self.tree).strip())
            #self.optimize() #maybe not for the repl... later
            #print(unparse(self.tree).strip())
        result = None
        try: # ugly, but it makes sure we clear out self.tree.body
            for stmt in self.tree.body:
                if type(stmt) is ast.Assign:
                    stree = ast.Module(body=[stmt])
                    ast.fix_missing_locations(stree)
                    exec(compile(stree,'<repl>','exec'), globals(), globals())
                else:
                    stree = ast.Expression(body=stmt.value)
                    ast.fix_missing_locations(stree)
                    result = eval(compile(stree,'<repl>','eval'))
        except Exception as e:
            self.tree.body = []
            raise e
        self.tree.body = []
        return result

