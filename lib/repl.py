
import cmd,imp
from glob import glob
from itertools import chain
from ast_python import REPLProgram
from traceback import print_exc
import stdlib

class Repl(cmd.Cmd):
    def __init__(self,debug=False):
        super().__init__()
        self.cjsh = REPLProgram(stdlib.stdlib)
        self.debug = debug
        self.prompt = '>> '
        if not debug: # use a terser exception printer
            print_exc = lambda: print(exc_info()[0:2],sep=': ')

    def do_reload(self,line):
        'Reload the stdlib module'
        try:
            imp.reload(stdlib)
            self.cjsh.stdlib = stdlib.stdlib
        except:
            print('Error reloading stdlib:')
            print_exc()
        else:
            print('Success: stdlib reloaded')
    
    def do_show(self,line):
        'Show the current definition of a var'
        var = line.strip()
        if var in stdlib.stdlib:
            print('%s: stdlib function'%var)
        elif self.cjsh.symtab:
            print('%s: defined in symtab: %s'%(var,self.cjsh.symtab[var]))
        elif var == '':
            print('Symtab:',list(self.cjsh.symtab.keys()))
            print('Stdlib:',list(stdlib.stdlib.keys()))
        else:
            print("'%s' not found in stdlib or symtab"%var)

    def do_run(self,line):
        'Run a CJSH source file'
        self.cjsh.parse_file(line.strip())
        self.cjsh.run(self.debug)

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
            print_exc()
            return
        try:
            res = self.cjsh.run(self.debug)
            if not res: return
            if hasattr(res,'__iter__'): print(list(res))
            else: print(res)
        except KeyboardInterrupt: pass # keep the interpreter going
        except:
            print("Error running:",line)
            print_exc()

    def completedefault(self,text,line,beg,end):
        lch,rch = line.rfind('<'),line.rfind('>')
        if lch >= 0 and rch < lch:
            d = len(line[lch+1:]) - len(text) # super hax
            return [f[d:] for f in glob('%s*'%line[lch+1:])]
        comps = chain(stdlib.stdlib.keys(),self.cjsh.symtab.keys())
        return sorted(k for k in comps if k.startswith(text))

    def emptyline(self): pass

