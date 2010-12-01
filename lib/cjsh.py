#!/usr/bin/env python3

VERSION = '0.6'

from sys import argv,exit,exc_info
from itertools import chain
from optparse import OptionParser
from ast_cjsh import Program
from stdlib import stdlib

if __name__ == '__main__':
    op = OptionParser('Usage: %prog [options] file.cj',version=VERSION)
    op.add_option('-e','--eval',metavar='CODE',help='Run CODE with cjsh')
    op.add_option('-c','--compile',metavar='FILE',help='Compile to FILE')
    op.add_option('-d','--debug', action='store_true', default=False,
                  help='Turn debug flags on')
    (options, args) = op.parse_args()

    if options.eval:
        assert len(args) == 0, 'Additional args are meaningless with -e'
        cjsh = Program(stdlib)
        cjsh.parse_line(argv[2])
        cjsh.run()
    elif options.compile:
        assert len(args) == 1, 'Need exactly 1 source file to compile'
        cjsh = Program(stdlib)
        cjsh.parse_file(argv[3])
        cjsh.save_compiled(argv[2])
    elif len(args) == 0:
        from repl import Repl
        debugstr = ' (debug)' if options.debug else ''
        welcome = 'Welcome to CJSH v%s%s'%(VERSION,debugstr)
        try: Repl(options.debug).cmdloop(welcome)
        except KeyboardInterrupt: print() # move past the prompt
    elif len(args) > 1:
        op.error('Only one source file at a time')
    else: #TODO: maybe use a flag to specify, or look at filename
        cjsh = Program(stdlib)
        try: cjsh.parse_file(args[0])
        except: cjsh.load_compiled(args[0])
        cjsh.run()

