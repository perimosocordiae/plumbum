import re
import copy
import sys
from time import time

from interpret import evaluate


def run_all_tests(state):
  all_tests = ((equality_tests, assert_equal),
               (error_tests, assert_error))
  failed,total = 0,0
  for tests, runner in all_tests:
    for code, expected in tests:
      total += 1
      tic = time()
      try:
        # prevent leaks between tests by copying the state
        runner(code, copy.deepcopy(state), expected)
      except Exception as e:
        failed += 1
        print 'Failed test %d: %s\n >> %s' % (total,code,e)
      elapsed = time()-tic
      if elapsed > 0.02 and total != 32:  # test 32 does an HTTP request
        print 'Timeout on test %d: %s\n >> %f secs' % (total,code,elapsed)
  return failed, total


def assert_equal(code, state, expected_out):
  for line in code.splitlines():
    out = evaluate(line, state, return_leftovers=True)
  assert len(out) == 1, 'Expected one result, got %d: %s' % (len(out), out)
  assert out[0] == expected_out, 'Expected %s, got %s' % (expected_out, out[0])


def assert_error(code, state, expected_msg):
  try:
    for line in code.splitlines():
      # Must return leftovers to force evaluation of lazy pipes.
      evaluate(line, state, return_leftovers=True)
  except:
    msg = str(sys.exc_info()[1])
    assert msg == expected_msg, 'Expected error %r, got error %r' % (expected_msg,msg)
  else:
    raise AssertionError('Expected error %r, got no error' % expected_msg)

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
  ('<testing.py> | head 1', ['import re\n']),
  ('`echo 1`', ['1\n']),
  ('["a","","b"] | grep /./', ['a','b']),
  ('[1..20] | string | grep /3/', ['3','13']),
  ('[4,2,5,1] | sort', [1,2,4,5]),
  ('[1,-5,0] | count', 3),
  ('[9,8..0] | string | sort | head 2', ['1','2']),
  ('`echo "1\\n2\\n3"` | int', [1,2,3]),
  ('[1,2,3] | string', ['1','2','3']),
  ('`echo "1\\n2\\n3"` | strip', ['1','2','3']),
  ('[2,3,3,2] | luniq', [2,3,2]),
  ('[2,3,3,2] | uniq | sort', [2,3]),
  ('["a"] | sort | strip', ['a']),
  ('["a","b"] | ord', [97,98]),
  ('[50] | chr | ord', [50]),
  ('[1..10] | sum', 45),
  ('<http://www.google.com> | head 1 | count', 1),   # this is test 32, exempt from timeout checks
  ('[[2,3],[4,5]]', [[2,3],[4,5]]),
  ('[[5..8],[4,3..1]]', [[5,6,7],[4,3,2]]),
  ('[[2],[3]] | flatten', [2,3]),
  ('[[4,5],[6,3]] | sort', [[4,5],[6,3]]),
  ('[[4,5],[6,3]] | head 1', [[4,5]]),
  ('[2,3] | zip [4,5]', [[2,4],[3,5]]),
  ('[2,3] | zip [4,5] | head 1', [[2,4]]),
  ('[2,3] | zip [4,5] | string', [['2','4'],['3','5']]),
  ('[2,3] | zip {[4,5]}', [[2,4],[3,5]]),
  ('[2,3] | zip [4,5] | flatten', [2,4,3,5]),
  #('[1..] | string | zip {`yes`} | head 2 | join ""', ['1y\n','2y\n']),  # inf looping?
  ('["","f","","","fg "] | compact', ['f','fg ']),
  ('["hello world","foo"] | split /\s+/i', [['hello','world'],['foo']]),
  ('["abcd"] | split ""', [['a','b','c','d']]),
  ('["hello world"] | split /l+/', [['he','o wor','d']]),
  # multiline tests, for defining pipes
  (''' foo = flatten | sort
    [[6,2],[8,3]] | foo''', [2,3,6,8]),
  (''' foo = strip | compact
    ["hel ", " lo", "", "world"] | foo''', ['hel','lo','world']),
)

error_tests = (
  # infinite loop, for now
  #('[1] | <>', 'Cannot pass [int] to nil input'),
  ('grep /foo/',  'stack underflow when calling <Builtin: grep>'),
  # current stack-based model doesn't know about # of args in a pipe
  #('[] | grep /foo/ 4', 'Too many arguments to grep: arg 1 (4)'),
  ('["a","4"] | grep 4', 'Invalid arg: regex required'),
  ('[] | grep',  'stack underflow when calling <Builtin: grep>'),
)

