
import re,sys,signal
from os.path import isfile
from urllib.request import urlopen
from itertools import islice,chain,tee,count,repeat
from subprocess import Popen,PIPE
from select import select
from random import random

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

def split(seq,*args):
    regex = args[0] if args else re.compile("\s")
    return (regex.split(x) for x in seq)

def seq_select(seq,*args):
    assert len(args) > 0, "Must provide at least one 1-based index"
    inds = list(int(x)-1 for x in args)
    if len(inds) > 1:
        return ([row[i] for i in inds] for row in seq)
    # special case to avoid unnecessary nesting
    return (row[inds[0]] for row in seq)

def lazy_uniq(seq,*_):
    last = None
    for x in seq:
        if x != last:
            yield x
            last = x

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
    '_slurp_': 'slurp',
    '_shell_': 'shellexec',
    'split': 'split',
    'flatten': 'flatten',
    'select': 'seq_select',
    'luniq': 'lazy_uniq',
    'join': 'join',
    # inlines
    'sub':     'lambda seq,regex,repl,*_: (regex.sub(repl,x) for x in seq)',
    'grep':    'lambda seq,regex,*_: (x for x in seq if regex.search(x))',
    'inc':     'lambda seq: (int(x)+1 for x in seq)',
    'ord':     'lambda seq: map(ord,seq)',
    'chr':     'lambda seq: map(chr,seq)',
    'rand':    'lambda seq: (random() for _ in seq)',
    'flip':    'lambda seq: (list(reversed(row)) for row in seq)',
    'zip':     'zip',
    'repeat':  'lambda _, arg: repeat(arg)',
    'take':    'lambda seq,*args: islice(seq,*map(int,args))',
    'strip':   'lambda seq: (x.strip() for x in seq)',
    'compact': 'lambda seq: (x for x in seq if x)',
    # non-lazy
    'print': 'pb_print',
    'println': 'pb_println',
    # inlines
    'sort':  'sorted',
    'reverse': 'reversed',
    'uniq':  'set',
    'sum':   'sum',
    'count': 'lambda seq: sum(1 for _ in seq)',
    }

