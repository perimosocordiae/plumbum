import sys
from optparse import OptionParser

import pblib
import builtins  # required to populate pblib.builtins

from interpret import parse, tokenize, evaluate
from repl import Repl


def main(opts):
  state = pblib.builtins
  for line in open(opts.prelude):
    parse(tokenize(line), state)
  if opts.e:
    tokens = tokenize(opts.e)
    return evaluate(tokens, state)
  if opts.f:
    fh = sys.stdin if opts.f == '-' else open(opts.f)
    for line in fh:
      tokens = tokenize(line)
      evaluate(tokens, state)
    return
  # REPL mode
  welcome = 'Loaded %d builtin functions' % len(state)
  try:
    Repl(state, debug=opts.debug).cmdloop(welcome)
  except KeyboardInterrupt:
    return


if __name__ == '__main__':
  op = OptionParser()
  op.add_option('-d','--debug',action='store_true')
  op.add_option('-e','--eval',type=str,dest='e')
  op.add_option('-f','--file',type=str,dest='f')
  op.add_option('--prelude',type=str,default='prelude.pb')
  opts, args = op.parse_args()
  if args:
    op.error('Extra arguments: %s' % args)
  main(opts)
