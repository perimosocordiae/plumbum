#!/usr/bin/env python3

VERSION = '0.7'

from sys import argv,exit,exc_info
from itertools import chain
from optparse import OptionParser
from program import Program
from stdlib import stdlib

if __name__ == '__main__':
    op = OptionParser('Usage: %prog [options] file.cj',version=VERSION)
    op.add_option('-e','--eval',metavar='CODE',help='Run CODE with plumbum')
    op.add_option('-d','--debug', action='store_true', default=False,
                  help='Turn debug flags on')
    (options, args) = op.parse_args()
    
    plumbum = Program()
    if options.eval:
        assert len(args) == 0, 'Additional args are meaningless with -e'
        plumbum.eval_line(argv[2])
    elif len(args) == 0:
        from repl import Repl
        debugstr = ' (debug)' if options.debug else ''
        welcome = 'Welcome to Plumbum v%s%s'%(VERSION,debugstr)
        try: Repl(plumbum,options.debug).cmdloop(welcome)
        except KeyboardInterrupt: print() # move past the prompt
    elif len(args) > 1:
        op.error('Only one source file at a time')
    else:
        plumbum.eval_file(args[0])

