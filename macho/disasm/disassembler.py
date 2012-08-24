import doctest
from table_generator import TableGenerator  # TODO(glider): from is forbidden?
from instruction import Instruction, NopInstruction, CodeSection
import sys

class UnknownInstruction(Exception):
  def __init__(self, bytes):
    self.bytes = bytes
  def __str__(self):
    return repr(map(hex, self.bytes))

class Disassembler(object):
  '''
>>> lines = file('increment.dylib.dump').readlines()
>>> D = Disassembler(lines)
>>> bytes = [0x55, 0x48, 0x89, 0xe5, 0x89, 0x7d, 0xfc, 0x8b, 0x45, 0xfc, 0x48, 0x63, 0xc8]
>>> bytes += [0x48, 0x8d, 0x15, 0x3c, 0x01, 0x00, 0x00]
>>> code = D.disassemble(bytes)
>>> (code.size_in_bytes() == len(bytes)) and (code.size_in_instructions() == 2)
True
>>> print code
>>> code.insert_instruction(NopInstruction(), 0)
>>> print code
>>> code.insert_instruction(NopInstruction(), 0)
>>> code.insert_instruction(NopInstruction(), 1)
>>> code.insert_instruction(NopInstruction(), 3)
>>> code.insert_instruction(NopInstruction(), 5)
>>> print code
  '''
  def __init__(self, lines):
    self.TG = TableGenerator()
    self.TG.read_lines(lines)
  def disassemble(self, bytes):
    index = 0
    size = len(bytes)
    code = CodeSection()
    while index < size:
      insn_bytes = self.TG.match_prefix(bytes[index:])
      if insn_bytes is None:
        raise UnknownInstruction(bytes[index:index+8])
      else:
        name = self.TG.table[insn_bytes]
        insn = Instruction(insn_bytes, name, index)
        index += len(insn_bytes)
        code.add_orig(insn)
    return code
        
def _test():
  import doctest
  failures, tests = doctest.testmod()
  return failures > 0

if __name__ == "__main__":
  sys.exit(_test())
