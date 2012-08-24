import doctest
import sys

# static
def is_relative(insn_name):
  '''
>>> is_relative('lea 0x13c(%rip),%rdx')
True
>>> is_relative('push %rbp')
False
  '''
  return '%rip' in insn_name


class Instruction(object):
  def __init__(self, bytes, name, position=-1):
    self.bytes = bytes
    self.name = name
    self.relative = is_relative(name)
    self.orig_position = position  # position in the original byte stream
    self.position = position   # new position relative to the beginning of the original stream
  def __str__(self):
    #result = '%8x\t%8x\t%s' % (self.orig_position, self.position, self.name)
    result = '%8x\t%8x\t%s\t\t\t%s' % (self.orig_position, self.position, self.name, map(hex, self.bytes))
    return result
  def size(self):
    return len(self.bytes)
  def fix_relative_instruction(self, offset):
    bytes = list(self.bytes)
    assert(self.relative)
    shifts = [0, 8, 16, 24]
    off_list = map(lambda x: (offset >> x) % 256, shifts)
    borrow = 0
    orig_rel = 0
    # We increased the RIP, thus decrease the encoded relative offset.
    for index in range(-1, -5, -1):
      orig_rel *= 256
      orig_rel += bytes[index]
    for index in range(-4, 0):
      if bytes[index] < off_list[index] + borrow:
        bytes[index] += 256
        borrow = 1
      bytes[index] -= (off_list[index] + borrow)
    assert(borrow == 0)  # we should not overflow
    new_rel = orig_rel - offset
    self.name = self.name.replace(hex(orig_rel) + '(%rip)', hex(new_rel) + '(%rip)')
    self.bytes = tuple(bytes)
  def move(self, offset):
    self.position += offset
    if self.relative:
      self.fix_relative_instruction(offset)

class NopInstruction(Instruction):
  def __init__(self, position=-1):
    bytes = [0x90]
    name = 'nop'
    super(NopInstruction, self).__init__(bytes, name, position)

def instruction_cmp(a, b):
  return cmp(a.position, b.position) 

class CodeSection(object):
  def __init__(self):
    self.instructions = []
  def add_orig(self, insn):
    self.instructions.append(insn)
  def insert_instruction(self, insn, position):
    insn.orig_position = -1
    insn.position = self.instructions[position].position
    self.instructions.insert(position, insn)
    for i in self.instructions[position+1:]:
      i.move(insn.size())
      
    
  def __str__(self):
    result = ''
    for insn in self.instructions:
      result += ("%s\n" % insn)
    return result
  def size_in_bytes(self):
    result = 0
    for i in self.instructions:
      result += i.size()
    return result
  def size_in_instructions(self):
    return len(self.instructions)
  def check(self):
    # check various invariants
    pass

def _test():
  failures, tests = doctest.testmod()
  return failures > 0

if __name__ == "__main__":
  sys.exit(_test())
