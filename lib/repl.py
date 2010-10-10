
import cmd,imp
from glob import glob
from itertools import chain
import ast
import stdlib

class Repl(cmd.Cmd):
    def __init__(self,program,print_exc):
        super().__init__()
        self.cjsh = program # instance of ast.Program
        self.print_exc = print_exc # function to print an exception
        self.prompt = '>> '

    def do_reload(self,line):
        'Reload the stdlib module'
        try:
            imp.reload(stdlib)
            ast.stdlib = stdlib.stdlib
        except:
            print('Error reloading stdlib:')
            self.print_exc()
        else:
            print('Success: stdlib reloaded')
    
    def do_show(self,line):
        'Show the current definition of a var'
        var = line.strip()
        if var in stdlib.stdlib:
            print('%s: stdlib function'%var)
        elif self.cjsh.symtab:
            print('%s: defined in symtab: %s'%(var,self.cjsh.symtab[var]))
        else:
            print('%s not found in stdlib or symtab')

    def do_run(self,line):
        'Run a CJSH source file'
        self.cjsh.parse_file(line.strip())
        self.cjsh.run()

    def complete_run(self,text,line,beg,end):
        return glob(text+'*')

    def do_EOF(self,line):
        print() # move past the prompt
        return True

    def default(self,line):
        try:
            self.cjsh.parse_line(line)
        except:
            print("Error parsing:",line)
            self.print_exc()
            return
        try:
            res = self.cjsh.run()
            if not res: return
            if hasattr(res,'__iter__'): print(list(res))
            else: print(res)
        except KeyboardInterrupt: pass # keep the interpreter going
        except:
            print("Error running:",line)
            self.print_exc()

    def completedefault(self,text,line,beg,end):
        lch,rch = line.rfind('<'),line.rfind('>')
        if lch >= 0 and rch < lch:
            d = len(line[lch+1:]) - len(text) # super hax
            return [f[d:] for f in glob('%s*'%line[lch+1:])]
        comps = chain(stdlib.stdlib.keys(),self.cjsh.symtab.keys())
        return sorted(k for k in comps if k.startswith(text))

    def emptyline(self): pass

