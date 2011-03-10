
import cmd
from glob import glob
from stdlib import stdlib

class Repl(cmd.Cmd):
    def __init__(self,plumbum,debug=False):
        super().__init__()
        self.plumbum = plumbum
        self.debug = debug
        self.prompt = '>> '
        if not debug: # use a terser exception printer
            from sys import exc_info
            self.print_exc = lambda: print(*(exc_info()[0:2]),sep=': ')
        else:
            from traceback import print_exc
            self.print_exc = print_exc

    def do_run(self,line):
        'Run a Plumbum source file'
        self.plumbum.eval_file(line.strip())

    def complete_run(self,text,line,beg,end):
        return glob(text+'*')

    def do_EOF(self,line):
        print() # move past the prompt
        return True

    def default(self,line):
        try:
            res = self.plumbum.eval_line(line)
            if not res: return
            if hasattr(res,'__iter__'): print(list(res))
            else: print(res)
        except KeyboardInterrupt:
            return # keep the interpreter going
        except:
            print("Error evaluating:",line)
            self.print_exc()

    def completedefault(self,text,line,beg,end):
        lch,rch = line.rfind('<'),line.rfind('>')
        if lch >= 0 and rch < lch:
            d = len(line[lch+1:]) - len(text) # super hax
            return [f[d:] for f in glob('%s*'%line[lch+1:])]
        funcs = (k for k in stdlib.keys() if not k.startswith('_'))
        return sorted(k for k in funcs if k.startswith(text))

    def emptyline(self): pass

