import re

__all__ = ['tokenize']


def tokenize(code):
  '''Converts a single 'line' of Plumbum into a sequence of token strings.'''
  WHITESPACE = ' \t\n\r'
  QUOTES = '"\'`<'
  REGEX_FLAGS = 'gimlsux'
  i = 0
  while i < len(code):
    char = code[i]
    if char in WHITESPACE:
      i = seek_to_regex(code, i+1, '\S')
    elif char == '#':
      i = seek_past_char(code, i+1, '\n')
    elif char == '|':
      yield char
      i += 1
    else:
      # we have a token, compute its end index (j)
      if char in QUOTES:
        j = seek_past_char(code, i+1, char if char != '<' else '>')
      elif char == '/':
        j = seek_past_char(code, i+1, '/')
        j = seek_to_regex(code, j, '[^%s]' % REGEX_FLAGS)
      elif char == '[':
        j = seek_past_nested(code, i+1, '[', ']')
      else:
        j = seek_to_regex(code, i+1, '\s|\|')
      # common to all tokens
      yield code[i:j]
      i = j
  assert i == len(code)


def seek_past_char(string, start_idx, char):
  end_idx = string.find(char, start_idx)
  while end_idx > 0 and string[end_idx-1] == '\\':
    end_idx = string.find(char, end_idx+1)
  if end_idx == -1:
    return len(string)
  return end_idx + 1


def seek_to_regex(string, start_idx, regex):
  m = re.search(regex, string[start_idx:])
  if not m:
    return len(string)
  return m.start() + start_idx


def seek_past_nested(string, start_idx, open_char, close_char):
  depth = 1  # assumes that start_idx-1 is an open_char
  bracket = re.compile('\%s|\%s' % (open_char, close_char))
  while depth > 0:
    m = bracket.search(string[start_idx:])
    assert m, 'Unbalanced nesting: too many %s\'s' % open_char
    char = m.group()
    if char == open_char:
      depth += 1
    elif char == close_char:
      depth -= 1
    else:
      assert False, 'bracket regex matched incorrect char: ' + char
    start_idx += m.end()
  return start_idx
