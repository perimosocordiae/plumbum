
from cmd import Cmd
from glob import glob
from traceback import print_exc
from sys import exc_info

from interpret import tokenize, evaluate

def terse_trace():
  err_type, msg = exc_info()[:2]
  print "%s: %s" % (err_type.__name__, msg)


class Repl(Cmd):
  def __init__(self, state, debug=False):
    Cmd.__init__(self)
    self.prompt = '>> '
    self.print_exc = print_exc if debug else terse_trace
    self.state = state

  def do_EOF(self,line):
    print # move past the prompt
    return True

  def default(self,line):
    try:
      tokens = tokenize(line)
      evaluate(tokens, self.state, repl_mode=True)
    except KeyboardInterrupt:
      return # keep the interpreter going
    except:
      print "Error evaluating '%s'" % line
      self.print_exc()

  def completedefault(self,text,line,beg,end):
    lch,rch = line.rfind('<'),line.rfind('>')
    if lch >= 0 and rch < lch:
      d = len(line[lch+1:]) - len(text) # super hax
      return [f[d:] for f in glob('%s*'%line[lch+1:])]
    funcs = (k for k in self.state.iterkeys() if k)
    return sorted(k for k in funcs if k.startswith(text))

  def emptyline(self): pass


