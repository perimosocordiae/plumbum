#!/usr/bin/env python3

VERSION = '0.3'
DEBUG = False

from sys import argv,exit,exc_info
from itertools import chain
from ast import Program
from repl import Repl # maybe do conditional import on this

# all the magic is in here
cjsh = Program()

# different types of 'print_exc' based on debug flag
if DEBUG:
	from traceback import print_exc
else:
	def print_exc():
		etype,estr = exc_info()[0:2]
		print(etype.__name__,estr,sep=': ')

def do_repl():
	welcome = 'Welcome to CJSH version %s'%VERSION
	if DEBUG: welcome += ' (debug)'
	try: Repl(cjsh,print_exc).cmdloop(welcome)
	except KeyboardInterrupt: print() # move past the prompt

if __name__ == '__main__':
	if len(argv) == 1:
		do_repl()
	elif argv[1] == '-e':
		cjsh.parse_line(argv[2])
		cjsh.run()
	elif argv[1] == '-c':
		cjsh.parse_file(argv[3])
		cjsh.compile(argv[2])
	else: #TODO: maybe use a flag to specify, or look at filename
		try: cjsh.parse_file(argv[1])
		except: cjsh.load_compiled(argv[1])
		cjsh.run()

