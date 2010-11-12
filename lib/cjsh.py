#!/usr/bin/env python3

VERSION = '0.5'
DEBUG = True

from sys import argv,exit,exc_info
from itertools import chain
from optparse import OptionParser
#from ast_simple import Program
from ast_python import Program, REPLProgram

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
    op = OptionParser('Usage: %prog [options] file.cj',version=VERSION)
    op.add_option('-e','--eval',metavar='CODE',help='Run CODE with cjsh')
    op.add_option('-c','--compile',metavar='FILE',help='Compile to FILE')
    (options, args) = op.parse_args()

    if options.eval:
        assert len(args) == 0, 'Additional args are meaningless with -e'
        cjsh = Program()
        cjsh.parse_line(argv[2])
        cjsh.run()
    elif options.compile:
        assert len(args) == 1, 'Need exactly 1 source file to compile'
        cjsh = Program()
        cjsh.parse_file(argv[3])
        cjsh.save_compiled(argv[2])
    elif len(args) == 0:
        run_repl(REPLProgram())
    elif len(args) > 1:
        op.error('Only one source file at a time')
    else: #TODO: maybe use a flag to specify, or look at filename
        cjsh = Program()
        try: cjsh.parse_file(args[0])
        except: cjsh.load_compiled(args[0])
        cjsh.run()

