# Disassembler table generator.
# Reads gobjdump output and produces a map from instruction bytes to instruction string.

import doctest
import re
import sys

# TODO(glider): suboptimal, need to fix.
def remove_spaces(v):
  '''
>>> remove_spaces('a   b   c d e          f   ')
'a b c d e f '
  '''
  f = v.replace('  ', ' ')
  while f != v:
    v = f
    f = v.replace('  ', ' ')
  return f

def str_to_hex(s):
  '''
>>> s = str_to_hex('55 0a 14')
>>> s == [0x55, 0x0a, 0x14]
True
  '''
  pieces = s.split()
  return map(lambda p: int(p, 16), pieces)
  
# Table keys are byte tuples.
class TableGenerator(object):
  '''
  >>> T = TableGenerator()
  >>> text = """0000000000000eb0 <_inc_value>:
  ...  eb0:   55                      push   %rbp
  ...  eb1:   48 89 e5                mov    %rsp,%rbp
  ...  eb4:   89 7d fc                mov    %edi,-0x4(%rbp)
  ...  eb7:   8b 45 fc                mov    -0x4(%rbp),%eax
  ...  eba:   48 63 c8                movslq %eax,%rcx
  ...  ebd:   48 8d 15 3c 01 00 00    lea    0x13c(%rip),%rdx        # 1000 <_glob>
  ...  ec4:   48 be 04 00 00 00 00    movabs $0x4,%rsi
  ...  ecb:   00 00 00
  ...  ece:   48 0f af ce             imul   %rsi,%rcx"""
  >>> T.read_text(text)
  >>> T.table[(0x55,)]
  'push %rbp'
  >>> lea_rip = (0x48, 0x8d, 0x15, 0x3c, 0x01, 0x00, 0x00)
  >>> T.table[lea_rip]
  'lea 0x13c(%rip),%rdx'
  >>> movabs = (0x48, 0xbe, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
  >>> T.table[movabs]
  'movabs $0x4,%rsi'
  >>> bytes_unknown = [0x48]
  >>> T.match_prefix(bytes_unknown) is None
  True
  >>> bytes_mov = [0x48, 0x89, 0xe5]
  >>> T.match_prefix(bytes_mov) == tuple(bytes_mov)
  True
  >>> bytes_push = [0x55, 0x0c, 0x00]
  >>> T.match_prefix(bytes_push) == (0x55,)
  True
  >>> lines = file('movabs.dump').readlines()
  >>> T2 = TableGenerator()
  >>> T2.read_lines(lines)
  '''

  def __init__(self):
    self.table = {}
    self._cur_insn = ''
    self._cur_bytes = []
  def flush_bytes(self):
    if self._cur_insn == '':
      assert(len(self._cur_bytes) == 0)
      return
    key = tuple(self._cur_bytes)
    if key in self.table:
      assert(self.table[key] == self._cur_insn)
    else:
      self.table[key] = self._cur_insn
    self._cur_insn = ''
    self._cur_bytes = []

  def read_text(self, text):
    self.read_lines(text.split('\n'))
  
  # TODO(glider): suboptimal
  def match_prefix(self, bytes_list):
    for key in self.table:
      if bytes_list[:len(key)] == list(key):
        return key
    return None


  # Parse a single section, e.g. obtained from:
  #   gobjdump -d -j .text program_name
  def read_lines(self, input_lines):
    func_re = re.compile('[0-9a-f]+ <[^>]>:')
    insn_re = re.compile('\s*[0-9a-f]+:\s+((?:[0-9a-f]{2} )+)\s+([^#]+)')
    insn_cont_re = re.compile('\s*[0-9a-f]+:\s+([0-9a-f]{2}(?: [0-9a-f]{2})*)\s*')
  
    for line in input_lines:
      if func_re.search(line):
        self.flush_bytes()
        continue
      match = insn_re.search(line)
      if match:
        self.flush_bytes()
        new_bytes = match.groups()[0]
        self._cur_bytes.extend(str_to_hex(new_bytes.strip()))
        self._cur_insn = remove_spaces(match.groups()[1]).strip()
        continue
      match = insn_cont_re.search(line)
      if match:
        new_bytes = match.groups()[0]
        self._cur_bytes.extend(str_to_hex(new_bytes.strip()))
        continue
      self.flush_bytes()
    self.flush_bytes()

def _test():
  failures, tests = doctest.testmod()
  return failures > 0

if __name__ == "__main__":
  sys.exit(_test())
