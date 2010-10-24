
import re,sys,signal
from itertools import islice,chain
from subprocess import Popen,PIPE
from select import select

def slurp(fname=''):
    if len(fname) > 0:
        return open(fname).readlines()
    return sys.stdin.readlines()

# suppress 'broken pipe' error messages
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
def shellexec(cmd):
    proc = Popen(cmd,shell=True,stdout=PIPE)
    #return proc.stdout.readlines() <-- unfortunately, this doesn't work
    line = ''
    while True:
        data = select([proc.stdout],[],[])[0][0]
        c = data.read(1).decode('utf-8')
        if len(c) == 0: return
        elif c == "\n":
            yield line+c
            line = ''
        else: line += c

def cjsh_print(seq,*args):
    sep = re.sub(r'\\n',"\n",args[0]) if len(args) > 0 else '' #hax
    for x in seq:
        print(x,sep='',end=sep)
def cjsh_println(seq,*args):
    cjsh_print(seq,*args)
    print()

def flatten(seq,*args):
    for x in seq:
        if hasattr(x,'__iter__') and not str(x) == x:
            for y in flatten(x,*args): # holy recursive generators, batman!
                yield y
        else:
            yield x

def grep(seq,*args):
    assert len(args) == 1 
    regex = re.compile(args[0])
    return (x for x in seq if regex.search(x))

def sub(seq,*args):
    assert len(args) > 1 
    regex = re.compile(args[0])
    return (regex.sub(args[1],x) for x in seq)

def split(seq,*args):
    regex = re.compile("\s") if len(args)==0 else re.compile(args[0])
    return (regex.split(x) for x in seq)

def seq_select(seq,*args):
    inds = list(map(int,args))
    if len(inds) > 1:
        grab = lambda row: [row[i] for i in inds]
        return map(grab,seq)
    return (row[inds[0]] for row in seq)

def lazy_uniq(seq,*_):
    last = None
    for x in seq:
        if x != last:
            yield x
            last = x

def cjsh_map(seq,*args):
    assert len(args) == 1, "can only map single fns, for now"
    assert args[0] in stdlib, "can only map stdlib fns, for now."
    return (map(stdlib[args[0]],x) for x in seq)

def join(seq,*args):
    sep = args[0]
    for x in seq:
        a = list(x)
        print(a)
        yield sep.join(a)

stdlib = {
    #lazy
    '_slurp_': slurp,
    '_shell_': shellexec,
    'grep': grep,'sub': sub,'split': split,
    'head': lambda seq,*args: islice(seq,*map(int,args)),
    'inc': lambda seq: (x+1 for x in seq),
    'compact': lambda seq: (x for x in seq if x not in ['',None]),
    'strip': lambda seq: (x.strip() for x in seq),
    'flatten': flatten,
    'zip': zip,
    'range': lambda _,*args: range(*map(int,args)),
    'select': seq_select,
    'luniq': lazy_uniq,
    'map': cjsh_map,
    'join': join,
    #non-lazy
    'sort': sorted,
    'uniq': set,
    'sum': sum,
    'count': lambda seq: sum(1 for _ in seq),
    'print': cjsh_print,
    'println': cjsh_println
    }

