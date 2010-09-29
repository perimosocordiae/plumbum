
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
	sep = re.sub(r'\\n',"\n",args[0]) if len(args) > 0 else ''
	for x in seq:
		print(x,sep='',end=sep)
def cjsh_println(seq,*args):
	cjsh_print(seq,*args)
	print()

def flatten(seq,*args):
	for x in seq:
		if hasattr(x,'__iter__'):
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

stdlib = {
	#lazy
	'_slurp_': slurp,
	'_shell_': shellexec,
	'grep': grep,'sub': sub,
	'head': lambda seq,*args: islice(seq,*map(int,args)),
	'inc': lambda seq: (x+1 for x in seq),
	'compact': lambda seq: (x for x in seq if x not in ['',None]),
	'strip': lambda seq: (x.strip() for x in seq),
	'flatten': flatten,
	#non-lazy
	'sort': sorted,
	'uniq': set,
	'sum': sum,
	'count': lambda seq: sum(1 for _ in seq),
	'print': cjsh_print,
	'println': cjsh_println
	}

