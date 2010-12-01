
import re,sys,_ast
from ast import fix_missing_locations, dump as ast_dump
from functools import reduce
from marshal import load,dump # for saving compiled files
from unparse import unparse
from stdlib import * # to not break inlined builtins
from parser import program_parser

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
        #TODO: figure out why parsing the file all at once fails
        for line in infile:
            self.parse_line(line)

    def parse_line(self,line):
        self.__add_stmts(program_parser.parseString(line))
    
    def __add_stmts(self, parse_res):
        for num,stmt in enumerate(parse_res[0]):
            if type(stmt) is _ast.Expr:
                self.tree.body.append(stmt)
                self.tree.body[-1].lineno = num+1
            else:
                self.tree.body.insert(0, stmt)
                self.tree.body[0].lineno = num+1

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
            print(unparse(self.tree))
        result = None
        for stmt in self.tree.body:
            if type(stmt) is _ast.Assign:
                stree = _ast.Module(body=[stmt])
                fix_missing_locations(stree)
                exec(compile(stree,'<repl>','exec'), globals(), globals())
            else:
                stree = _ast.Expression(body=stmt.value)
                fix_missing_locations(stree)
                result = eval(compile(stree,'<repl>','eval'))
        self.tree.body = []
        return result

