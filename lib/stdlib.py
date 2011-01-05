
import re,sys,signal
from os.path import isfile
from urllib.request import urlopen
from itertools import islice,chain,tee
from subprocess import Popen,PIPE
from select import select

def slurp(fname=''):
    if len(fname) == 0:
        return sys.stdin.readlines()
    if isfile(fname):
        return open(fname).readlines()
    try:
        return (x.decode() for x in urlopen(fname).readlines())
    except:
        raise ValueError('%s is not a file or a web address'%fname)

# suppress 'broken pipe' error messages
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
def shellexec(seq,cmd):
    assert not seq or len(seq) == 0, "Passing input to shell cmds is NYI"
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

def pb_print(seq,*args):
    sep = re.sub(r'\\n',"\n",args[0]) if len(args) > 0 else '' #hax
    for x in seq:
        print(x,sep='',end=sep)
def pb_println(seq,*args):
    pb_print(seq,*args)
    print()

def flatten(seq,*args):
    for x in seq:
        if hasattr(x,'__iter__') and not str(x) == x:
            for y in flatten(x,*args): # holy recursive generators, batman!
                yield y
        else:
            yield x

def grep(seq,regex,*extra):
    assert len(extra) == 0
    if not hasattr(regex,'search'):
        regex = re.compile(regex)
    return (x for x in seq if regex.search(x))

def sub(seq,*args):
    assert len(args) > 1 
    regex = re.compile(args[0])
    return (regex.sub(args[1],x) for x in seq)

def split(seq,*args):
    regex = re.compile("\s") if len(args)==0 else re.compile(args[0])
    return (regex.split(x) for x in seq)

def seq_select(seq,*args):
    assert len(args) > 0, "Must provide at least one 0-based index"
    inds = list(map(int,args))
    if len(inds) > 1:
        grab = lambda row: [row[i] for i in inds]
        return map(grab,seq)
    # special case to avoid unnecessary nesting
    return (row[inds[0]] for row in seq)

def lazy_uniq(seq,*_):
    last = None
    for x in seq:
        if x != last:
            yield x
            last = x

def pb_map(seq,*args):
    assert len(args) == 1, "can only map single fns, for now"
    assert args[0] in stdlib, "can only map stdlib fns, for now."
    return (map(stdlib[args[0]],x) for x in seq)

def join(seq,*args):
    sep = args[0]
    seq1,seq2 = tee(seq) # just in case
    try:
        for x in seq1:
            yield sep.join(map(str,x)) # coerce to strs
    except TypeError as e:
        if 'not iterable' in e.args[0]:
            yield sep.join(map(str,seq2))
        else:
            raise e

stdlib = {
    # lazy
    '_slurp_': slurp,
    '_shell_': shellexec,
    'grep': grep,'sub': sub,'split': split,
    'flatten': flatten,
    'select': seq_select,
    'luniq': lazy_uniq,
    'map': pb_map,
    'join': join,
    # inlines
    'inc':     'lambda seq: (int(x)+1 for x in seq)',
    'zip':     'zip',
    'head':    'lambda seq,*args: islice(seq,*map(int,args))',
    'strip':   'lambda seq: (x.strip() for x in seq)',
    'range':   'lambda _,*args: range(*map(int,args))',
    'compact': 'lambda seq: (x for x in seq if x)',
    # non-lazy
    'print': pb_print,
    'println': pb_println,
    # inlines
    'sort':  'sorted',
    'uniq':  'set',
    'sum':   'sum',
    'count': 'lambda seq: sum(1 for _ in seq)',
    }

