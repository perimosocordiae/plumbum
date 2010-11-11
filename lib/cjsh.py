#!/usr/bin/env python3

VERSION = '0.5'
DEBUG = True

from sys import argv,exit,exc_info
from itertools import chain
from ast_simple import Program as REPLProgram
from ast_python import Program

def run_repl(cjsh):
    from repl import Repl
    # different types of 'print_exc' based on debug flag
    if DEBUG:
        from traceback import print_exc
    else:
        def print_exc():
            etype,estr = exc_info()[0:2]
            print(etype.__name__,estr,sep=': ')
    welcome = 'Welcome to CJSH, ver %s%s'%(VERSION,' (debug)' if DEBUG else '')
    try: Repl(cjsh,print_exc).cmdloop(welcome)
    except KeyboardInterrupt: print() # move past the prompt

if __name__ == '__main__':
    cjsh = Program() # all the magic is in here
    if len(argv) == 1:
        run_repl(REPLProgram())
    elif argv[1] == '-e':
        cjsh.parse_line(argv[2])
        cjsh.run()
    elif argv[1] == '-c':
        cjsh.parse_file(argv[3])
        cjsh.save_compiled(argv[2])
    else: #TODO: maybe use a flag to specify, or look at filename
        try: cjsh.parse_file(argv[1])
        except: cjsh.load_compiled(argv[1])
        cjsh.run()

