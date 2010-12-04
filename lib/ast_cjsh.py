
import re, sys, ast
from collections import Counter
from functools import reduce
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
        ast.fix_missing_locations(self.tree)
        self.code = compile(self.tree,self.fname,'exec')
        with open(fname,'wb') as f:
            dump(self.code,f)

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
        #print(unparse(self.tree)) # super useful for debugging
        exec(compile(self.tree,self.fname,'exec'),globals(),globals())

class REPLProgram(Program):
    def run(self, debug=False):
        if debug:
            print(unparse(self.tree).strip())
            self.optimize() #maybe not for the repl... later
            print(unparse(self.tree).strip())
        result = None
        for stmt in self.tree.body:
            if type(stmt) is ast.Assign:
                stree = ast.Module(body=[stmt])
                ast.fix_missing_locations(stree)
                exec(compile(stree,'<repl>','exec'), globals(), globals())
            else:
                stree = ast.Expression(body=stmt.value)
                ast.fix_missing_locations(stree)
                result = eval(compile(stree,'<repl>','eval'))
        self.tree.body = []
        return result


class Optimizer(ast.NodeTransformer):
    def __init__(self):
        self.redo = False

    def visit_Call(self,node):
        # we only want to mutate lambdas, but we need access to args too
        if type(node.func) is not ast.Lambda: return node
        params = [a.arg for a in node.func.args.args]
        body = node.func.body
        # count up which names are used in the body
        self.used = Counter()
        self.generic_visit(body)
        # if no parameters are referenced in the body, unwrap the body
        if len(params & self.used.keys()) == 0:
            self.redo = True
            return body
        # check for inline-able arguments (only referenced once)
        self.inlines = {}
        for p,a in zip(params,node.args):
            if self.used[p] != 1: continue
            self.inlines[p] = a
            idx = params.index(p)
            del node.func.args.args[idx]
            del node.args[idx]
        if len(self.inlines) > 0:
            self.generic_visit(body)  # make a second pass to mutate
        del self.inlines
        return node

    def visit_Name(self,node):
        # don't bother with store operations
        if type(node.ctx) is not ast.Load: return node
        if hasattr(self,'inlines'):
            # second pass, mutation step
            if node.id in self.inlines:
                # replace node with the passed arg
                self.redo = True
                return self.inlines[node.id]
        else:
            # first pass, just counting for now
            self.used[node.id] += 1
        return node
