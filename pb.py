#!/usr/bin/env python

from argparse import ArgumentParser
from plumbum import Plumbum
from pb_repl import Repl
from pb_parse import parse_file, parse_blob

def do_repl(debug=False):
  try: Repl(debug).cmdloop('Plumbum v2.0')
  except KeyboardInterrupt: print # move past the prompt

def exec_file(fname):
  fh = sys.stdin if fname == '-' else open(fname)
  pb = Plumbum()
  for st in parse_file(fh):
    pb.define(st)
  pb.run()

def exec_blob(blob):
  pb = Plumbum()
  for st in parse_blob(blob):
    pb.define(st)
  pb.run()

if __name__ == '__main__':
  p = ArgumentParser()
  p.add_argument('file',nargs='*',help='Plumbum source file(s) to execute')
  p.add_argument('--eval','-e',metavar='CODE',help='Plumbum code to execute')
  p.add_argument('--debug','-d',action='store_true',help='Turn on debug mode')
  args = p.parse_args()

  if args.eval:
    exec_blob(args.eval)
  elif not args.file or (len(args.file) == 1 and args.file[0] == '-'):
    do_repl(args.debug)
  else:
    for fname in args.file:
      exec_file(fname)
  