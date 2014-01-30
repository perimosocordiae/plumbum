#!/usr/bin/env python

from pb_repl import InteractivePB
from pb_parse import parse_blob
import re,sys
from time import time

def _make_pb(code):
  pb = InteractivePB()
  for statement in parse_blob(code):
    pb.define(statement)
  return pb

def assert_equal(code, expected_out):
  pb = _make_pb(code)
  out = pb.run()
  assert out == expected_out, 'Expected %s, got %s' % (expected_out,out)

def assert_error(code, expected_msg):
  try:
    pb = _make_pb(code)
    pb.run()
  except Exception as e:
    msg = str(e)
    assert msg == expected_msg, 'Expected error %r, got error %r' % (expected_msg,msg)
  else:
    raise AssertionError('Expected error %r, got no error' % expected_msg)

def assert_type(code, expected_type):
  pb = InteractivePB()
  for statement in parse_blob(code):
    pb.define(statement)
  if statement['name']:
    t = str(pb.pipes[statement['name']].type)
  else:
    t = str(pb.pipes[''][0].type.output)
  assert t == expected_type, 'Expected type %s, got type %s' % (expected_type,t)

def run_tests(*all_tests):
  failed,total = 0,0
  for runner, tests in all_tests:
    for code,res in tests:
      total += 1
      tic = time()
      try:
        runner(code,res)
      except Exception as e:
        failed += 1
        print 'Failed test %d: %s\n >> %s' % (total,code,e)
      elapsed = time()-tic
      if elapsed > 0.02 and total != 32:  # test 32 does an HTTP request
        print 'Timeout on test %d: %s\n >> %f secs' % (total,code,elapsed)
  return failed, total

FILE = sys.argv[0]
equality_tests = (
  ('[]', []),
  ('[] # comment', []),
  ('["foo"]', ["foo"]),
  ("[\"foo\",'bar']", ["foo","bar"]),
  ('[/a/]', [re.compile('a')]),
  ('[/a/,/b/]', map(re.compile, ('a','b'))),
  ('[0,1,2,3,4,5,6,7,8,9]', range(10)),
  ('[-1,99,32,5]', [-1,99,32,5]),
  ('[0..10]', range(10)),
  ('[0,1..10]', range(10)),
  ('[1,3..10]', range(1,10,2)),
  ('[0..99] | head', range(10)),
  ('[0..] | head 5', range(5)),
  ('[0..] | head', range(10)),
  ('[-3,5..] | head', range(-3,70,8)),
  ('[0..] | head 1', [0]),
  ('<%s> | head 1'%FILE, ['#!/usr/bin/env python\n']),
  ('`echo 1`', ['1\n']),
  ('["a","","b"] | grep /./', ['a','b']),
  ('[1..20] | map string | grep /3/', ['3','13']),
  ('[4,2,5,1] | sort', [1,2,4,5]),
  ('[1,-5,0] | count', 3),
  ('[9,8..0] | map string | sort | head 2', ['1','2']),
  ('`echo "1\\n2\\n3"` | map int', [1,2,3]),
  ('[1,2,3] | map string', ['1','2','3']),
  ('`echo "1\\n2\\n3"` | strip', ['1','2','3']),
  ('[2,3,3,2] | uniq', [2,3,2]),
  ('["a"] | sort | strip', ['a']),
  ('["a","b"] | map ord', [97,98]),
  ('[50] | map chr | map ord', [50]),
  ('[1..10] | sum', 45),
  ('<http://www.google.com> | head 1 | count', 1),   # this is test 32, exempt from timeout checks
  ('[[2,3],[4,5]]', [[2,3],[4,5]]),
  ('[[5..8],[4,3..1]]', [[5,6,7],[4,3,2]]),
  ('[[2],[3]] | flatten', [2,3]),
  ('[[4,5],[6,3]] | sort', [[4,5],[6,3]]),
  ('[[4,5],[6,3]] | head 1', [[4,5]]),
  ('[2,3] | zip [4,5]', [[2,4],[3,5]]),
  ('[2,3] | zip [4,5] | head 1', [[2,4]]),
  ('[2,3] | zip [4,5] | map string', [['2','4'],['3','5']]),
  ('[2,3] | zip {[4,5]}', [[2,4],[3,5]]),
  ('[2,3] | zip [4,5] | flatten', [2,4,3,5]),
  #('[1..] | string | zip {`yes`} | head 2 | join ""', ['1y\n','2y\n']),  # inf looping?
  ('["","f","","","fg "] | compact', ['f','fg ']),
  ('["hello world","foo"] | split', [['hello','world'],['foo']]),
  ('["abcd"] | split ""', [['a','b','c','d']]),
  ('["hello world"] | split /l+/', [['he','o wor','d']]),
  # multiline tests, for defining pipes
  (''' foo = flatten | sort
    [[6,2],[8,3]] | foo)''', [2,3,6,8]),
  (''' foo = strip | compact
    ["hel ", " lo", "", "world"] | foo''', ['hel','lo','world']),
)

error_tests = (
  ('[1] | sort | strip', 'type mismatch: [int] <> str'),
  ('[1] | count | grep /foo/', 'type mismatch: int <> [str]'),
  ('[1] | <>', 'Cannot pass [int] to nil input'),
  ('grep /foo/', 'Pipe needs input of type ([str] -> [str])'),
  ('[] | grep /foo/ 4', 'Too many arguments to grep: arg 1 (4)'),
  ('["a","4"] | grep 4', 'first argument must be string or compiled pattern'),
  ('[] | grep', 'Missing required argument for grep'),
  ('[[2],[3]] | flatten | flatten', 'Cannot auto-deepen a concrete input'),
)

type_tests = (
  ('[1]', '[int]'),
  ('[1..]', '[int]'),
  ('["foo"]', '[str]'),
  ('<>', '[str]'),
  ('``', '[str]'),
  ('`` | map strip', '[str]'),
  ('[[1]]', '[[int]]'),
  ('[2,3] | zip [4,3]', '[[int]]'),
  ('[[4,5],[6,3]] | head 1', '[[int]]'),
  ('foo=strip|compact', '([str] -> [str])'),
  #TODO: allow arb types to match here
)

if __name__ == '__main__':
  failed,total = run_tests((assert_equal, equality_tests),
                           (assert_error, error_tests),
                           (assert_type,  type_tests))
  if failed == 0:
    print "SUCCESS:",
  print "%d/%d tests failed" % (failed,total)


