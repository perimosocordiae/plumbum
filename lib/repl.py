
import cmd,imp
from glob import glob
from itertools import chain
from ast_plumbum import REPLProgram
from traceback import print_exc
import stdlib

class Repl(cmd.Cmd):
    def __init__(self,debug=False):
        super().__init__()
        self.plumbum = REPLProgram(stdlib.stdlib)
        self.debug = debug
        self.prompt = '>> '
        if not debug: # use a terser exception printer
            print_exc = lambda: print(exc_info()[0:2],sep=': ')

    def do_reload(self,line):
        'Reload the stdlib module'
        try:
            imp.reload(stdlib)
            self.plumbum.refresh_stdlib(stdlib.stdlib)
        except:
            print('Error reloading stdlib:')
            print_exc()
        else:
            print('Success: stdlib reloaded')
    
    def do_run(self,line):
        'Run a Plumbum source file'
        self.plumbum.parse_file(line.strip())
        self.plumbum.run(self.debug)

    def complete_run(self,text,line,beg,end):
        return glob(text+'*')

    def do_EOF(self,line):
        print() # move past the prompt
        return True

    def default(self,line):
        try:
            self.plumbum.parse_line(line)
        except:
            print("Error parsing:",line)
            print_exc()
            return
        try:
            res = self.plumbum.run(self.debug)
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
        funcs = (k for k in stdlib.stdlib.keys() if not k.startswith('_'))
        return sorted(k for k in funcs if k.startswith(text))

    def emptyline(self): pass

