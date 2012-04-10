
from cmd import Cmd
from glob import glob
from traceback import print_exc
from sys import exc_info
from pb_parse import parse_line
from plumbum import Plumbum

def terse_trace():
  err_type, msg = exc_info()[:2]
  print "%s: %s" % (err_type.__name__, msg)

def listify(x):
  '''Turn all nested generators and such into lists of concrete values'''
  if hasattr(x,'__iter__'):
    return map(listify,x)
  return x

class InteractivePB(Plumbum):
  def __init__(self):
    Plumbum.__init__(self)
    del self.pipes['']  # no special casing for main pipes
  
  def define(self, name, raw_pipe):
    pipe = self.join_pipe(map(self.resolve,raw_pipe))
    if not name:
      name = ''
      assert pipe.type.input.name == 'nil', 'Pipe needs input of type %s' % pipe.type
    self.pipes[name] = pipe

  def run(self):
    main = self.pipes['']
    res = main.func(None,main.args)
    return listify(res)

class Repl(Cmd):
  def __init__(self,debug=False):
    Cmd.__init__(self)
    self.plumbum = InteractivePB()
    self.debug = debug
    self.prompt = '>> '
    self.print_exc = print_exc if debug else terse_trace

  def do_EOF(self,line):
    print # move past the prompt
    return True
  
  def do_reload(self,_):
    print "TODO"

  def do_typeof(self,line):
    for lhs,rhs in parse_line(line):
      try:
        t = self.plumbum.typeof(rhs)
      except:
        print "Error evaluating '%s'" % line
        self.print_exc()
        break
      if lhs: print lhs,'::',t
      else:   print t

  def default(self,line):
    try:
      for lhs,rhs in parse_line(line):
        self.plumbum.define(lhs,rhs)
        if lhs:
          print 'Defined pipe:', lhs
        else:
          res = self.plumbum.run()
          if res: print res
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
    funcs = (k for k in self.plumbum.pipes.iterkeys() if k)
    return sorted(k for k in funcs if k.startswith(text))

  def emptyline(self): pass

