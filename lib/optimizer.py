
import ast
from collections import Counter

#TODO: bug when optimizing inlined 'sub' (seq + 2 args)
class Optimizer(ast.NodeTransformer):
    def __init__(self):
        self.redo = False
        self.used_stack = []

    def visit_Call(self,node):
        # we only want to mutate lambdas, but we need access to args too
        if type(node.func) is not ast.Lambda or hasattr(self,'inlines'): 
            self.generic_visit(node)  # keep walkin'
            return node
        params = [a.arg for a in node.func.args.args]
        params.append(node.func.args.vararg)
        body = node.func.body
        # forward on to arguments
        for a in node.args:
            self.visit(a)
        # count up which names are used in the body
        self.used_stack.append(Counter())
        self.visit(body)
        used = self.used_stack.pop()
        # if no parameters are referenced in the body, unwrap the body
        if not any(params & used.keys()):
            self.redo = True
            return body
        # check for inline-able arguments (only referenced once)
        self.inlines = {}
        for i,p_a in enumerate(zip(params[:-1],node.args)):
            p, arg = p_a
            if used[p] != 1: continue
            self.inlines[p] = arg
            del node.func.args.args[i]
            del node.args[i]
        # check the vararg separately
        vararg = params[-1]
        if used[vararg] == 1:
            i = len(node.func.args.args)
            self.inlines[vararg] = ast.List(elts=node.args[i:],ctx=ast.Load())
            node.func.args.vararg = None
            del node.args[i:]
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
            for used in self.used_stack:
                used[node.id] += 1
        return node
